
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, asc, and_
from sqlalchemy.sql.expression import true, false
from app.db import get_db
from app.schemas.report_data import ReportRequest, ReportResponse, ReportDataRow
from app.models import Email, EmailProcessing, TriggerList, JiraTicket, ReportData, Notification
from app.report_utils import generate_csv_report
from app.auth_utils import verify_token
from datetime import datetime, time, date
from typing import List
from decorators import log_function_call
import asyncio

router = APIRouter(prefix="/data", tags=["Report Generation"])

SORT_MAPPING = {
    "received_at": ReportData.received_at,
    "priority": ReportData.priority,
    "timestamp": ReportData.timestamp,
    "assigned_to": ReportData.assigned_to
}

@log_function_call
def get_report_data_query(
    db: Session,
    request: ReportRequest,
    only_count: bool = False
):
    """Constructs and executes the SQLAlchemy query for the report using the new ReportData table."""

    # Build base query with filters
    stmt = select(ReportData).where(
        and_(
            ReportData.received_at >= request.start_date,
            ReportData.received_at <= request.end_date
        )
    )

    if request.filter_type:
        stmt = stmt.where(ReportData.type == request.filter_type)

    if request.filter_priority:
        stmt = stmt.where(ReportData.priority == request.filter_priority)

    # Count rows for pagination or early exit
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_rows = db.execute(count_stmt).scalar_one()
    if only_count:
        return total_rows, []

    # Sorting
    sort_column = SORT_MAPPING.get(request.sort_by)
    if sort_column:
        order = desc if request.sort_order == 'desc' else asc
        stmt = stmt.order_by(order(sort_column))
    else:
        # Default sort by most recent received_at
        stmt = stmt.order_by(desc(ReportData.received_at))

    # Pagination
    stmt = stmt.limit(request.page_size).offset((request.page - 1) * request.page_size)

    # Execute and transform to schema
    result = db.execute(stmt)
    report_data_objects = [row[0] for row in result.all()]

    data: List[ReportDataRow] = [
        ReportDataRow.model_validate(obj) for obj in report_data_objects
    ]
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
        timestamp=datetime.utcnow(),
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