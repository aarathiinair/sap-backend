from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc, asc, and_, cast, String
from sqlalchemy.dialects import postgresql
from app.db import get_db
from app.schemas.report_data import ReportRequest, ReportResponse
from app.models import RawEmail, SegregatedEmail, JiraEntry, Notification, Certificate, JiraState
from app.report_utils import generate_csv_report
from app.auth_utils import verify_token
from datetime import datetime, timezone, date
import uuid
from typing import List, Tuple, Any

router = APIRouter(prefix="/data", tags=["Report Generation"])

# --- HANDLER 1: ControlUp ---
def query_controlup_mails(db: Session, request: ReportRequest):
    # 1. CTE for latest Jira Entry per email
    jira_subquery = select(
        JiraEntry.email_id.label('sq_email_id'),
        JiraEntry.jiraticket_id.label('jiraticket_id'), 
        JiraEntry.created_at.label('sq_created_at'),
        JiraEntry.assigned_to.label('assigned_to'),
        JiraEntry.teams_channel.label('teams_channel'),
        func.row_number().over(
            partition_by=JiraEntry.email_id,
            order_by=desc(JiraEntry.created_at)
        ).label('rn')
    ).cte('jira_subquery')

    # 2. Subquery to pick only the most recent ticket
    latest_jira = select(
        jira_subquery.c.sq_email_id,
        jira_subquery.c.jiraticket_id,
        jira_subquery.c.sq_created_at,
        jira_subquery.c.assigned_to,
        jira_subquery.c.teams_channel
    ).where(jira_subquery.c.rn == 1).subquery('latest_jira')

    # 3. Main Statement
    # Note: Explicitly label columns to ensure the Row object keys match your Pydantic/Frontend expectations
    stmt = select(
        RawEmail.email_id.label("email_id"),
        RawEmail.received_at.label("received_at"),
        RawEmail.sender.label("sender"),
        RawEmail.subject.label("subject"),
        # Use a case-insensitive coalesce check
        func.coalesce(SegregatedEmail.priority, func.cast('Informational', postgresql.VARCHAR)).label("priority"),
        func.coalesce(SegregatedEmail.type, func.cast('Informational', postgresql.VARCHAR)).label("type"),
        latest_jira.c.jiraticket_id.label("jiraticket_id"), 
        latest_jira.c.sq_created_at.label("timestamp"),
        latest_jira.c.assigned_to.label("assigned_to"),
        latest_jira.c.teams_channel.label("teams_channel"),
    ).select_from(RawEmail)\
     .outerjoin(SegregatedEmail, RawEmail.email_id == SegregatedEmail.email_id)\
     .outerjoin(latest_jira, RawEmail.email_id == latest_jira.c.sq_email_id)

    # 4. Filter Logic Fix
    # Ensure start/end date are within range
    filter_clauses = [RawEmail.received_at >= request.start_date, RawEmail.received_at <= request.end_date]
    
    if request.filter_type:
        search_type = request.filter_type.lower()
        if search_type == "informational":
            # Correctly handle NULL values as Informational
            filter_clauses.append((SegregatedEmail.type == None) | (func.lower(SegregatedEmail.type) == "informational"))
        else:
            # If searching for 'actionable', we MUST match explicitly
            filter_clauses.append(func.lower(SegregatedEmail.type) == search_type)
    
    if request.filter_priority:
        search_priority = request.filter_priority.lower()
        if search_priority == "informational":
            filter_clauses.append((SegregatedEmail.priority == None) | (func.lower(SegregatedEmail.priority) == "informational"))
        else:
            filter_clauses.append(func.lower(SegregatedEmail.priority) == search_priority)

    stmt = stmt.where(and_(*filter_clauses))
    
    # 5. Sort Map
    # Map the frontend string to the actual SQLAlchemy column object
    sort_map = {
        "received_at": RawEmail.received_at,
        "sender": RawEmail.sender,
        "subject": RawEmail.subject,
        "priority": func.lower(SegregatedEmail.priority),
        "type": func.lower(SegregatedEmail.type),
        "timestamp": latest_jira.c.sq_created_at,
        "assigned_to": latest_jira.c.assigned_to
    }
    
    return stmt, sort_map

# --- HANDLER 2: Certificates ---
def query_certificates(db: Session, request: ReportRequest):
    # 1. Base Query
    stmt = select(
        Certificate.certificate_name,
        Certificate.expiration_date,
        Certificate.calculated_status,
        Certificate.responsible_group,
        Certificate.teams_channel,
        Certificate.description,
        Certificate.usage,
        Certificate.effected_users,
        JiraState.jira_ticket_id
    ).select_from(Certificate)\
     .outerjoin(JiraState, Certificate.certificate_name == JiraState.certificate_name)

    # 2. Base Filters (Dates)
    filter_clauses = [
        Certificate.expiration_date >= request.start_date,
        Certificate.expiration_date <= request.end_date
    ]

    # 3. Status Filter (Fixing the Enum + lower() issue)
    if request.filter_type:
        # We cast to String here so PostgreSQL can compare text
        # 'ilike' is case-insensitive, handling 'Expiring Soon' or 'EXPIRING_SOON'
        search_status = request.filter_type.strip()
        filter_clauses.append(
            cast(Certificate.calculated_status, String).ilike(search_status)
        )

    # 4. Responsible Group Filter
    if request.responsible_group:
        filter_clauses.append(Certificate.responsible_group == request.responsible_group)

    stmt = stmt.where(and_(*filter_clauses))

    # 5. Sorting Map
    sort_map = {
        "certificate_name": Certificate.certificate_name,
        "expiration_date": Certificate.expiration_date,
        "calculated_status": Certificate.calculated_status,
        "responsible_group": Certificate.responsible_group,
        "jira_ticket_id": JiraState.jira_ticket_id
    }

    return stmt, sort_map

# --- Registry Mapping ---
REPORT_HANDLERS = {
    "ControlUp": query_controlup_mails,
    "Certificates": query_certificates
}

def get_filtered_query(db: Session, request: ReportRequest):
    handler = REPORT_HANDLERS.get(request.source)
    if not handler:
        raise HTTPException(status_code=400, detail=f"Invalid source: {request.source}")
    
    stmt, sort_map = handler(db, request)

    # Generic Sorting Logic
    order = desc if request.sort_order == 'desc' else asc
    sort_col = sort_map.get(request.sort_by)
    
    if sort_col is not None:
        stmt = stmt.order_by(order(sort_col).nulls_last())
    
    return stmt

@router.get("/", response_model=ReportResponse)
async def get_report_data(request: ReportRequest = Depends(), db: Session = Depends(get_db)):
    # 1. Get the base query (without sorting)
    handler = REPORT_HANDLERS.get(request.source)
    if not handler:
        raise HTTPException(status_code=400, detail=f"Invalid source: {request.source}")
    
    # We call the handler to get the base stmt and sort_map
    stmt, sort_map = handler(db, request)
    
    # 2. Count total rows BEFORE applying sorting or paging
    # This avoids the "ORDER BY in subquery" error
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_rows = db.scalar(count_stmt)
    
    # 3. Apply Generic Sorting Logic to the original stmt
    order = desc if request.sort_order == 'desc' else asc
    sort_col = sort_map.get(request.sort_by)
    
    if sort_col is not None:
        # Apply sorting only to the statement used for data fetching
        stmt = stmt.order_by(order(sort_col).nulls_last())
    
    # 4. Paging
    stmt = stmt.limit(request.page_size).offset((request.page - 1) * request.page_size)
    
    # 5. Fetch data
    result = db.execute(stmt).mappings().all()

    return ReportResponse(
        data=list(result),
        total_rows=total_rows,
        page=request.page,
        page_size=request.page_size,
        total_pages=(total_rows + request.page_size - 1) // request.page_size if total_rows else 0
    )

@router.post("/download")
async def download_report(
    request: ReportRequest = Body(...),  # Explicitly tell FastAPI this is the JSON body
    db: Session = Depends(get_db), 
    payload: dict = Depends(verify_token)
):
    username = payload.get("username", "Unknown User")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="User identifier missing in token")
    
    # Matching your UUID conversion logic
    user_id = uuid.uuid5(uuid.NAMESPACE_DNS, str(user_id_str))
    
    # 1. Get query (Pass db and request)
    stmt, sort_map = query_controlup_mails(db, request) if request.source == "ControlUp" else query_certificates(db, request)

    # 2. Add sorting from the generic logic
    order = desc if request.sort_order == 'desc' else asc
    sort_col = sort_map.get(request.sort_by)
    if sort_col is not None:
        stmt = stmt.order_by(order(sort_col).nulls_last())

    # 3. Execute without LIMIT/OFFSET for full download
    full_data = db.execute(stmt).mappings().all()

    if not full_data:
        raise HTTPException(status_code=404, detail="No data found.")

    # Convert rows to list of dicts
    dict_data = [dict(row) for row in full_data]
    csv_file = generate_csv_report(dict_data)
    
    # Notification
    db.add(Notification(user_id=user_id, text=f"{request.source} report downloaded.", timestamp=datetime.now(timezone.utc)))
    db.commit()

    filename = f"{request.source.lower()}_report_{date.today()}.csv"
    return StreamingResponse(csv_file, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})