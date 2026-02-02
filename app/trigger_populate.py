import sys
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from typing import Iterator

# Project imports
try:
    from app.db import get_db, Base
    from app.models.trigger_mappings import TriggerMapping
except ImportError:
    print("Error: Could not import required modules from 'app'")
    sys.exit(1)


# ---------------- Configuration ----------------

EXCEL_FILE_PATH = r"app/ControlUp Trigger Details.xlsx"

# Map Excel headers → SQLAlchemy model fields
COLUMN_MAPPING = {
    "TriggerName": "trigger_name",
    "Category": "category",
    "Priority": "priority",
    "Informational/Actionable": "actionable",
    "Recommended Actions": "recommended_action",
    "Responsible Person": "responsible_persons",
    "Team": "team",
    "Department": "department",
}

REQUIRED_COLUMNS = ["TriggerName", "Team"]

# ------------------------------------------------


def get_trigger_mappings_from_excel(file_path: str) -> Iterator[TriggerMapping]:
    """
    Reads trigger mapping data from all sheets in an Excel file
    and yields TriggerMapping objects.
    """
    print(f"Reading Excel file: {file_path}")

    try:
        xls = pd.ExcelFile(file_path)
        all_sheets = pd.read_excel(xls, sheet_name=None)
    except Exception as e:
        print(f"Failed to read Excel file: {e}")
        sys.exit(1)

    total_rows = 0

    for sheet_name, df in all_sheets.items():
        print(f"Processing sheet: '{sheet_name}'")

        # Normalize column names
        df.columns = df.columns.str.strip()

        # Ensure required columns exist
        if not all(col in df.columns for col in REQUIRED_COLUMNS):
            print(f"Skipping sheet '{sheet_name}': missing required columns")
            continue

        # Rename columns to model field names
        df = df.rename(columns=COLUMN_MAPPING)

        for _, row in df.iterrows():
            trigger_name = row.get("trigger_name")
            team = row.get("team")

            # Skip invalid rows
            if pd.isna(trigger_name) or not str(trigger_name).strip():
                continue
            if pd.isna(team) or not str(team).strip():
                continue

            total_rows += 1

            yield TriggerMapping(
                trigger_name=str(trigger_name).strip(),
                category=str(row.get("category", "")).strip(),
                priority=str(row.get("priority", "")).strip(),
                actionable=str(row.get("actionable", "")).strip(),
                recommended_action=str(row.get("recommended_action", "")).strip(),
                team=str(team).strip(),
                department=str(row.get("department", "")).strip(),
                responsible_persons=str(row.get("responsible_persons", "")).strip(),
            )

    print(f"Total valid trigger mappings prepared: {total_rows}")


def populate_trigger_mappings_table(file_path: str):
    """
    Creates the trigger_mappings table (if needed)
    and inserts Excel data.
    """
    db_generator = get_db()
    db: Session = next(db_generator)

    try:
        engine = db.get_bind()
        print(f"Ensuring table '{TriggerMapping.__tablename__}' exists...")
        Base.metadata.create_all(bind=engine)

        records = list(get_trigger_mappings_from_excel(file_path))

        if records:
            db.add_all(records)
            db.commit()
            print("-" * 40)
            print("Trigger mappings successfully inserted.")
            print(f"Total records inserted: {len(records)}")
            print("-" * 40)
        else:
            print("No valid records found to insert.")

    except SQLAlchemyError as e:
        db.rollback()
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        db.close()
        print("Database session closed.")


if __name__ == "__main__":
    populate_trigger_mappings_table(EXCEL_FILE_PATH)
    print("--- Script Finished ---")