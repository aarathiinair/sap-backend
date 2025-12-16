from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, asc, and_, outerjoin, over, distinct
from app.db import get_db
from app.schemas.report_data import ReportRequest, ReportResponse, ReportDataRow
from app.models import RawEmail, SegregatedEmail, JiraEntry, Notification
from app.report_utils import generate_csv_report
from app.auth_utils import verify_token
from datetime import datetime, date, timezone
from typing import List, Tuple
from decorators import log_function_call
from sqlalchemy.dialects import postgresql

router = APIRouter(prefix="/data", tags=["Report Generation"])

SORT_MAPPING = {
    "received_at": RawEmail.received_at,
    "priority": SegregatedEmail.priority,
    "timestamp": JiraEntry.created_at,
    "assigned_to": JiraEntry.assigned_to
}

@log_function_call
def get_report_data_query(
    db: Session,
    request: ReportRequest,
    only_count: bool = False
) -> Tuple[int, List[ReportDataRow]]:

    JiraEntry_Aliased = JiraEntry

    jira_subquery = select(
        JiraEntry_Aliased.email_id.label('sq_email_id'),
        JiraEntry_Aliased.jiraticket_id.label('jiraticket_id'), 
        JiraEntry_Aliased.created_at.label('sq_created_at'),
        JiraEntry_Aliased.assigned_to.label('assigned_to'),
        func.row_number().over(
            partition_by=JiraEntry_Aliased.email_id,
            order_by=desc(JiraEntry_Aliased.created_at)
        ).label('rn')
    ).cte('jira_subquery')

    latest_jira = select(jira_subquery).where(jira_subquery.c.rn == 1).subquery('latest_jira')

    select_columns = [
        RawEmail.email_id.label("email_id"),
        RawEmail.received_at.label("received_at"),
        RawEmail.sender.label("sender"),
        RawEmail.subject.label("subject"),
        func.coalesce(SegregatedEmail.priority, func.cast('Informational', postgresql.VARCHAR)).label("priority"),
        func.coalesce(SegregatedEmail.type, func.cast('Informational', postgresql.VARCHAR)).label("type"),
        latest_jira.c.jiraticket_id.label("jiraticket_id"), 
        latest_jira.c.sq_created_at.label("timestamp"),
        latest_jira.c.assigned_to.label("assigned_to"),
    ]

    stmt = select(*select_columns).select_from(RawEmail) \
        .outerjoin(SegregatedEmail, RawEmail.email_id == SegregatedEmail.email_id) \
        .outerjoin(latest_jira, RawEmail.email_id == latest_jira.c.sq_email_id)

    filter_clauses = [
        RawEmail.received_at >= request.start_date,
        RawEmail.received_at <= request.end_date
    ]

    if request.filter_type:
        if request.filter_type == "Informational":
            # Informational includes explicit 'Informational' OR null values
            filter_clauses.append((SegregatedEmail.type == None) | (SegregatedEmail.type == "Informational"))
        else:
            filter_clauses.append(SegregatedEmail.type == request.filter_type)

    if request.filter_priority:
        if request.filter_priority == "Informational":
            filter_clauses.append((SegregatedEmail.priority == None) | (SegregatedEmail.priority == "Informational"))
        else:
            filter_clauses.append(SegregatedEmail.priority == request.filter_priority)

    stmt = stmt.where(and_(*filter_clauses))

    total_rows = db.scalar(select(func.count()).select_from(stmt.subquery()))
    
    if only_count:
        return total_rows, []

    sort_column_map = {
        "received_at": RawEmail.received_at,
        "priority": SegregatedEmail.priority,
        "timestamp": latest_jira.c.sq_created_at, 
        "assigned_to": latest_jira.c.assigned_to 
    }
    
    sort_column = sort_column_map.get(request.sort_by)
    
    if sort_column is not None:
        order = desc if request.sort_order == 'desc' else asc

        # The check for sorting on Outer Join columns also needs to be updated
        # to use the new column references:
        if sort_column in [latest_jira.c.sq_created_at, latest_jira.c.assigned_to]:
            if request.sort_order == 'desc':
                 stmt = stmt.order_by(order(sort_column).nulls_last())
            else:
                 stmt = stmt.order_by(order(sort_column).nulls_first())
        else:
             stmt = stmt.order_by(order(sort_column))

    else:
        stmt = stmt.order_by(desc(RawEmail.received_at))

    stmt = stmt.limit(request.page_size).offset((request.page - 1) * request.page_size)

    result = db.execute(stmt)
    
    data: List[ReportDataRow] = []
    for row in result.fetchall():
        data.append(ReportDataRow(
            email_id=row.email_id,
            received_at=row.received_at,
            sender=row.sender,
            subject=row.subject,
            priority=row.priority,
            type=row.type,
            jiraticket_id=row.jiraticket_id, 
            timestamp=row.timestamp,
            assigned_to=row.assigned_to, 
        ))

    return total_rows, data

@router.get("/", response_model=ReportResponse)
@log_function_call
async def get_report_data(
    request: ReportRequest = Depends(),
    db: Session = Depends(get_db)
):
    """Fetches paginated and filtered report data for the UI table."""
    total_rows, data = get_report_data_query(db, request)


    total_pages = (total_rows + request.page_size - 1) // request.page_size

    return ReportResponse(
        data=data,
        total_rows=total_rows,
        page=request.page,
        page_size=request.page_size,
        total_pages=total_pages
    )

@router.post("/download")
@log_function_call
async def download_report(
    request: ReportRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(verify_token)
):
    """Generates and downloads the full report data as a CSV file."""

    user_id = payload.get("sub")
    username = payload.get("username")

    total_rows, _ = get_report_data_query(db, request, only_count=True)

    if total_rows == 0:
        raise HTTPException(status_code=404, detail="No data found for the selected criteria.")

    full_request = request.model_copy(update={"page": 1, "page_size": total_rows})
    _, full_data = get_report_data_query(db, full_request)

    csv_file = generate_csv_report(full_data)

    try:
        start_date_str = request.start_date.strftime('%d-%m-%Y')
        end_date_str = request.end_date.strftime('%d-%m-%Y')
    except AttributeError:
        start_date_str = str(request.start_date)
        end_date_str = str(request.end_date)

    notification_text = f"Report for {start_date_str} to {end_date_str} ({total_rows} rows) downloaded successfully."

    new_notification = Notification(
        user_id=user_id,
        text=notification_text,
        timestamp=datetime.now(timezone.utc),
        read=False
    )
    db.add(new_notification)
    db.commit()

    filename = f"report_data_{date.today().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        csv_file,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )