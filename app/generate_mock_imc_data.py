import hashlib
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import and_

# Importing your existing DB infrastructure
from app.db import get_db
# Ensure SegregatedIMCEmail is imported from your models
from app.models import RawEmail, SegregatedIMCEmail, JiraEntry

# --- CONFIGURATION ---
TEST_SENDER = 'imc@bitzer.biz'  # Configurable sender for IMC reports
NUM_RECORDS = 100 
JIRA_PREFIX = "MAI"
# ---------------------

def generate_email_id(subject, timestamp):
    """Generates a unique SHA-256 hash for the email_id (CHAR 64)."""
    hash_input = f"{subject}{timestamp}{random.random()}"
    return hashlib.sha256(hash_input.encode()).hexdigest()

def create_imc_mock_data():
    # Use the generator from your app.db
    db_gen = get_db()
    db = next(db_gen)
    
    print(f"🚀 Starting IMC mock data generation for: {TEST_SENDER}")
    
    try:
        for i in range(NUM_RECORDS):
            # 1. Create Raw Email
            received_date = datetime.now(timezone.utc) - timedelta(
                days=random.randint(0, 7), 
                minutes=random.randint(0, 1440)
            )
            
            # Logic: Informational vs Actionable
            email_type = random.choice(['Informational', 'Actionable'])
            
            subject_prefix = "[IMC-INFO]" if email_type == 'Informational' else "[IMC-CRITICAL]"
            subject = f"{subject_prefix} Device Connectivity: {random.choice(['Switch-A', 'Router-B', 'AP-Internal'])}"
            e_id = generate_email_id(subject, received_date)
            
            raw_email = RawEmail(
                email_id=e_id,
                sender=TEST_SENDER,
                subject=subject,
                body=f"IMC Source Alert\nType: {email_type}\nStatus: Active",
                email_path=f"C:/storage/emails/imc/{e_id}.msg",
                received_at=received_date,
                status=True
            )
            db.add(raw_email)

            # 2. Create Segregated IMC Entry
            # Applying logic: Informational -> Informational | Actionable -> P1/P2
            priority = 'Informational' if email_type == 'Informational' else random.choice(['P1', 'P2'])
            
            imc_entry = SegregatedIMCEmail(
                email_id=e_id,
                priority=priority,
                type=email_type,
                device=f"IMC-Node-{random.randint(100, 999)}",
                # Note: 'sensor' field is removed per your requirement
                status=True
            )
            db.add(imc_entry)

            # 3. Create Jira Entry 
            if email_type == 'Actionable' and random.random() > 0.2:
                jira_entry = JiraEntry(
                    email_id=e_id,
                    jiraticket_id=f"{JIRA_PREFIX}-{random.randint(5000, 9999)}",
                    assigned_to=random.choice(['Network.Team', 'NOC.Lead', 'System.Admin']),
                    created_at=received_date + timedelta(minutes=random.randint(5, 20)),
                    teams_flag='true',
                    teams_channel='IMC-Network-Alerts'
                )
                db.add(jira_entry)
                
                # Handle potential duplicate tickets for testing CTE
                if random.random() > 0.9:
                    db.add(JiraEntry(
                        email_id=e_id,
                        jiraticket_id=f"{JIRA_PREFIX}-{random.randint(1000, 4999)}",
                        assigned_to='Escalation.Manager',
                        created_at=jira_entry.created_at + timedelta(minutes=30),
                        teams_flag='true',
                        teams_channel='IMC-Escalations'
                    ))

        db.commit()
        print(f"✅ Successfully inserted {NUM_RECORDS} IMC records.")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during generation: {str(e)}")
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass

if __name__ == "__main__":
    create_imc_mock_data()