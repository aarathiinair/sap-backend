import io
import csv
from typing import List, Dict, Any
from datetime import datetime

def generate_csv_report(data: List[Dict[str, Any]]) -> io.StringIO:
    """
    Converts a list of dictionaries into a CSV string dynamically.
    Works for any source (ControlUp, Certificates, etc.) by extracting keys.
    """
    output = io.StringIO()
    if not data:
        return output

    # Extract headers from the first dictionary keys
    # Replace underscores with spaces and capitalize for a cleaner header
    raw_keys = data[0].keys()
    headers = [key.replace('_', ' ').title() for key in raw_keys]

    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)

    for row in data:
        formatted_row = []
        for key in raw_keys:
            val = row.get(key)
            
            # Format Datetime objects for CSV readability
            if isinstance(val, datetime):
                formatted_row.append(val.strftime('%Y-%m-%d %H:%M:%S'))
            # Handle Nulls/None
            elif val is None or val == "":
                formatted_row.append("N/A")
            else:
                formatted_row.append(val)
        
        writer.writerow(formatted_row)

    output.seek(0)
    return output