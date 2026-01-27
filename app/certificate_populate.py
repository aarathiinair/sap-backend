import pandas as pd
from datetime import datetime
from app.db import get_db
from app.models.certificates import Certificate  # adjust import path if needed


EXCEL_PATH = r"C:\smart-email-integration-backend\app\Certificates.xlsx"  # path to your Excel file


def parse_expiration_date(value):
    dt = pd.to_datetime(value, utc=True)
    return dt.tz_convert(None).replace(microsecond=0)

def load_certificates_from_excel(path: str):
    df = pd.read_excel(EXCEL_PATH)
    df.columns = df.columns.str.strip()

    db = next(get_db())

    for idx, row in df.iterrows():
        expiration_date = parse_expiration_date(row["Expiration Date"])

        cert = Certificate(
            certificate_name=str(row["Title"]).strip(),
            expiration_date=expiration_date,
            description=row.get("Description"),
            usage=row.get("Usage"),
            effected_users=row.get("Effected Users"),
            responsible_group=row["Jira Team"],
            teams_channel=row["Jira Team"],
        )

        print({
            "certificate_name": row["Title"],
            "expiration_date": expiration_date,
            "description": row.get("Description"),
            "usage": row.get("Usage"),
            "effected_users": row.get("Effected Users"),
            "responsible_group": row["Jira Team"],
            "teams_channel": row["Jira Team"],
        })

        db.add(cert)

    db.commit()
    db.close()


if __name__ == "__main__":
    load_certificates_from_excel(EXCEL_PATH)