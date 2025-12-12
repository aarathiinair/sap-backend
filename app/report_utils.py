import io
import csv
from typing import List
from app.schemas.report_data import ReportDataRow
from datetime import datetime, timedelta
import uuid
 
# For SMTP mailing
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
 
# --- Configuration (Placeholders) ---
# NOTE: Replace these with actual values for production/testing
SMTP_SERVER = "smtp.office365.com"  # Common for Office 365/Outlook
SMTP_PORT = 587
SMTP_USERNAME = "your_sending_email@yourdomain.com" 
SMTP_PASSWORD = "your_email_password_or_app_password" # Use App Password if MFA is enabled
SENDER_EMAIL = SMTP_USERNAME
PLACEHOLDER_RECEIVER_EMAIL = "testing_receiver@example.com" # Replace with actual recipient
 
# --- Mock Data Generation (Retained for testing) ---
def generate_mock_report_data(count: int = 10) -> List[ReportDataRow]:
    """Generates mock data for testing when the DB is empty."""
    mock_data = []
    priorities = ["P1", "P2", "P3"]
    senders = ["ControlUp", "SAP", "ServiceNow", "Jenkins"]
    subjects = ["Critical Alert", "New Feature Request", "Daily Summary", "Actionable Item"]
    types = ["Actionable", "Informational"]
    jira_tickets = ["JIRA-1001", "JIRA-1002", "JIRA-1003", None]
 
    for i in range(count):
        is_jira = jira_tickets[i % 4]
        row_data = {
            "email_id": str(uuid.uuid4()),
            "sender": senders[i % len(senders)],
            "subject": subjects[i % len(subjects)],
            "received_at": datetime.utcnow() - timedelta(days=(i % 7)),
            "type": types[i % 2],
            "priority": priorities[i % 3],
            "jira_ticket": is_jira,
            "timestamp": datetime.utcnow() if is_jira else None
        }
        # Use ReportDataRow.model_validate for correct Pydantic instantiation
        mock_data.append(ReportDataRow.model_validate(row_data))
        
    return mock_data
 
# --- CSV Generation ---
def generate_csv_report(data: List[ReportDataRow]) -> io.StringIO:
    """Converts a list of ReportDataRow objects into a CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
 
    header = ["Email ID", "Sender", "Subject", "Received At", "Type", "Priority", "Jira Ticket", "Timestamp"]
    writer.writerow(header)
 
    for row in data:
        writer.writerow([
            row.email_id,
            row.sender,
            row.subject,
            row.received_at.strftime('%Y-%m-%d %H:%M:%S'),
            row.type,
            row.priority,
            row.jira_ticket if row.jira_ticket else "N/A",
            row.timestamp.strftime('%Y-%m-%d %H:%M:%S') if row.timestamp else "N/A",
        ])
 
    output.seek(0)
    return output
 
# --- Actual Email Function ---
async def send_report_email(recipient: str, csv_file_content: io.StringIO):
    """Sends an email with the report attached using SMTP (Outlook/Exchange)."""
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient
    msg['Subject'] = f"Automated Email Report - {datetime.now().strftime('%Y-%m-%d')}"
 
    # Email Body
    body = "Please find the attached automated report based on the requested criteria."
    msg.attach(MIMEText(body, 'plain'))
 
    # Attach CSV
    filename = f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # Read CSV content from StringIO object
    csv_content = csv_file_content.getvalue()
    
    part = MIMEApplication(csv_content, _subtype="csv")
    part.add_header('Content-Disposition', 'attachment', filename=filename)
    msg.attach(part)
 
    try:
        # Connect to the SMTP server
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
        
        print(f"Report successfully sent to {recipient}")
        return True
    except Exception as e:
        print(f"ERROR sending email report to {recipient}: {e}")
        # In a real app, you would log this error properly
        return False