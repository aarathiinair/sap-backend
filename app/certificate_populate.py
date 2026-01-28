#!/usr/bin/env python3
"""
Reads an Excel file and inserts rows into the certificates table.

Column mappings:
- certificate_name  <- Title
- expiration_date   <- Expiration Date (converted to LOCAL TIME, naive)
- description       <- Description
- usage             <- Usage
- responsible_group <- Jira Team
- teams_channel     <- Jira Team

Other fields:
- created_at / updated_at -> now (LOCAL TIME, naive)

Usage:
    python -m app.certificate_populate "C:\\path\\to\\Certificates_Inventory.xlsx" [optional_sheet_name_or_index]
"""

import sys
from typing import Optional, Dict, Any, Union

import pandas as pd
from datetime import datetime

# ---- App imports ----
from app.db import get_db  # generator that yields a Session and closes it at the end
from app.models.certificates import Certificate  # adjust if your model lives elsewhere


def _local_now_naive() -> datetime:
    """Return current local time as a naive datetime (no tzinfo)."""
    return datetime.now().astimezone().replace(tzinfo=None)


def _to_local_naive(value: Any) -> Optional[datetime]:
    """
    Convert a wide range of datetime-like values to LOCAL TIME (naive).

    Behavior:
    - Timezone-aware values (e.g., '2026-06-02T22:00:00Z') are converted to local tz, then tzinfo is stripped.
    - Naive values are treated as already local and returned as naive.
    - Returns None if unparsable.
    """
    if pd.isna(value):
        return None

    ts = pd.to_datetime(value, errors='coerce', utc=False)
    if pd.isna(ts):
        return None

    # For pandas Timestamp, .tzinfo exists (similar to datetime)
    if getattr(ts, "tzinfo", None) is not None:
        # Convert aware -> local tz, then drop tzinfo to make it naive local
        local_tz = datetime.now().astimezone().tzinfo
        try:
            # For pandas Timestamp, tz_convert works if tz-aware
            ts_local = ts.tz_convert(local_tz)
            return ts_local.to_pydatetime().replace(tzinfo=None)
        except Exception:
            # Fallback: convert via Python datetime
            py_dt = ts.to_pydatetime()
            return py_dt.astimezone(local_tz).replace(tzinfo=None)
    else:
        # Naive: assume it's already local
        return ts.to_pydatetime()


def _normalize_str(value: Any) -> Optional[str]:
    """Return a trimmed string or None."""
    if pd.isna(value):
        return None
    s = str(value).strip()
    return s if s else None


def _load_excel_first_sheet(excel_path: str, sheet_name: Optional[Union[str, int]] = 0) -> pd.DataFrame:
    """
    Load the Excel sheet as a DataFrame.

    - If sheet_name is None, pandas returns a dict; we pick the first sheet.
    - If sheet_name is 0 (default), we read the first sheet.
    - If a specific name or index is provided, we read that.

    Returns:
        pd.DataFrame
    """
    df_or_dict = pd.read_excel(excel_path, sheet_name=sheet_name, engine="openpyxl")

    if isinstance(df_or_dict, dict):
        if not df_or_dict:
            raise ValueError("Excel file contains no sheets.")
        # Pick the first available sheet deterministically
        first_key = next(iter(df_or_dict.keys()))
        print(f"[info] sheet_name=None returned multiple sheets; using first sheet: '{first_key}'")
        return df_or_dict[first_key]
    else:
        return df_or_dict


def import_certificates_from_excel(excel_path: str, sheet_name: Optional[Union[str, int]] = 0) -> None:
    """
    Read the Excel and insert each valid row into the certificates table.
    """
    # Load the DataFrame from Excel
    df = _load_excel_first_sheet(excel_path, sheet_name=sheet_name)

    # Normalize expected columns (be forgiving about casing/extra spaces)
    expected_cols = {
        "title": "Title",
        "expiration date": "Expiration Date",
        "description": "Description",
        "usage": "Usage",
        "effected users": "Effected Users",  # ignored
        "jira team": "Jira Team",
    }

    # Build a lowercase mapping for the provided columns
    present_cols_map: Dict[str, str] = {}
    for col in df.columns:
        key = str(col).strip().lower()
        present_cols_map[key] = col

    # Verify required columns exist
    required_keys = ["title", "expiration date", "jira team"]
    missing = [expected_cols[k] for k in required_keys if k not in present_cols_map]
    if missing:
        raise ValueError(f"Missing required column(s) in Excel: {missing}")

    # Prepare timestamps (LOCAL, naive) for created_at/updated_at
    now_local = _local_now_naive()

    gen = get_db()
    session = next(gen)
    inserted = 0
    skipped = 0
    errors: list[str] = []

    try:
        for idx, row in df.iterrows():
            try:
                title = _normalize_str(row[present_cols_map["title"]])
                expiration_raw = row[present_cols_map["expiration date"]]
                jira_team = _normalize_str(row[present_cols_map["jira team"]])

                # Optional fields
                description = _normalize_str(row[present_cols_map["description"]]) if "description" in present_cols_map else None
                usage = _normalize_str(row[present_cols_map["usage"]]) if "usage" in present_cols_map else None

                # Basic validation
                if not title or pd.isna(expiration_raw) or not jira_team:
                    skipped += 1
                    continue

                expiration_local_naive = _to_local_naive(expiration_raw)
                if expiration_local_naive is None:
                    skipped += 1
                    continue

                cert = Certificate(
                    certificate_name=title,
                    expiration_date=expiration_local_naive,   # LOCAL TIME, naive
                    description=description,
                    usage=usage,
                    responsible_group=jira_team,
                    teams_channel=jira_team,
                    created_at=now_local,   # LOCAL TIME, naive
                    updated_at=now_local,   # LOCAL TIME, naive
                )

                session.add(cert)
                inserted += 1

            except Exception as row_err:
                skipped += 1
                errors.append(f"Row {idx + 2}: {row_err}")  # +2 for header + 1-based row indexing

        session.commit()

    except Exception:
        session.rollback()
        raise
    finally:
        try:
            gen.close()
        except Exception:
            pass

    print(f"Import complete. Inserted: {inserted}, Skipped: {skipped}")
    if errors:
        print("Some rows were skipped due to errors:")
        for e in errors[:20]:
            print("  -", e)
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.certificate_populate \"C:\\path\\to\\Certificates_Inventory.xlsx\" [optional_sheet_name_or_index]")
        sys.exit(1)

    excel_file = sys.argv[1]
    sheet_arg: Optional[Union[str, int]] = None
    if len(sys.argv) >= 3:
        # Allow either numeric (index) or string (sheet name)
        maybe_idx = sys.argv[2]
        if maybe_idx.isdigit():
            sheet_arg = int(maybe_idx)
        else:
            sheet_arg = maybe_idx

    import_certificates_from_excel(excel_file, sheet_name=sheet_arg if sheet_arg is not None else 0)