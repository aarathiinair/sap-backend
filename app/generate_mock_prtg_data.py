import hashlib
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import and_

# Importing your existing DB infrastructure
from app.db import get_db, Base
from app.models import RawEmail, SegregatedPRTGEmail, JiraEntry

# --- CONFIGURATION ---
TEST_SENDER = 'prtg@bitzer.de'  # Configurable sender for PRTG reports
NUM_RECORDS = 25         # Increased count for better variety
JIRA_PREFIX = "MAI"
# ---------------------

def generate_email_id(subject, timestamp):
    """Generates a unique SHA-256 hash for the email_id (CHAR 64)."""
    hash_input = f"{subject}{timestamp}{random.random()}"
    return hashlib.sha256(hash_input.encode()).hexdigest()

def create_mock_data():
    # Use the generator from your app.db
    db_gen = get_db()
    db = next(db_gen)
    
    print(f"🚀 Starting mock data generation for: {TEST_SENDER}")
    
    try:
        for i in range(NUM_RECORDS):
            # 1. Create Raw Email
            received_date = datetime.now(timezone.utc) - timedelta(
                days=random.randint(0, 5), 
                minutes=random.randint(0, 1440)
            )
            
            # Randomly decide the type for this record
            email_type = random.choice(['Informational', 'Actionable'])
            
            subject_prefix = "[INFO]" if email_type == 'Informational' else "[ALERT]"
            subject = f"{subject_prefix} PRTG: {random.choice(['Link Down', 'Ping Loss', 'Disk Full'])}"
            e_id = generate_email_id(subject, received_date)
            
            raw_email = RawEmail(
                email_id=e_id,
                sender=TEST_SENDER,
                subject=subject,
                body=f"Type: {email_type}\nDetail: Mocked PRTG Payload content.",
                email_path=f"C:/storage/emails/{e_id}.msg",
                received_at=received_date,
                status=True
            )
            db.add(raw_email)

            # 2. Create Segregated PRTG Entry
            # Applying logic: Informational -> Informational | Actionable -> P1/P2
            if email_type == 'Informational':
                priority = 'Informational'
            else:
                priority = random.choice(['P1', 'P2'])
            
            prtg_entry = SegregatedPRTGEmail(
                email_id=e_id,
                priority=priority,
                type=email_type,
                device=f"PRTG-Node-{random.randint(10, 50)}",
                sensor=f"Sensor-{random.choice(['01', '05', '09'])}",
                status=True
            )
            db.add(prtg_entry)

            # 3. Create Jira Entry 
            # Logic: Only Actionable items usually get tickets.
            if email_type == 'Actionable' and random.random() > 0.2:
                # Create a primary ticket
                jira_entry = JiraEntry(
                    email_id=e_id,
                    jiraticket_id=f"{JIRA_PREFIX}-{random.randint(1000, 9999)}",
                    assigned_to=random.choice(['Admin.User', 'OnCall.Eng', 'Support.Lead']),
                    created_at=received_date + timedelta(minutes=random.randint(2, 15)),
                    teams_flag='true',
                    teams_channel='Network-Critical-Alerts'
                )
                db.add(jira_entry)
                
                # Occasionally create a second ticket for the same email to test CTE row_number() logic
                if random.random() > 0.85:
                    duplicate_jira = JiraEntry(
                        email_id=e_id,
                        jiraticket_id=f"{JIRA_PREFIX}-{random.randint(1000, 9999)}",
                        assigned_to='Escalation.Manager',
                        created_at=jira_entry.created_at + timedelta(hours=1),
                        teams_flag='true',
                        teams_channel='Escalations'
                    )
                    db.add(duplicate_jira)

        db.commit()
        print(f"✅ Successfully inserted {NUM_RECORDS} records with conditional priority logic.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during generation: {str(e)}")
    finally:
        # Properly close the session by exhausting the generator
        try:
            next(db_gen)
        except StopIteration:
            pass

if __name__ == "__main__":
    create_mock_data()