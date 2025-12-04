from typing import Iterable, List, Dict, Union
from io import BytesIO
from openpyxl import load_workbook
import re

def extract_pi_rows_xlsx(
    source: Union[str, bytes, BytesIO],
    sheets: Iterable[str] = None # type: ignore
) -> List[Dict]:

    
    pat = re.compile(
        r'^\s*(?P<num>\d+(?:\.\d+)*)\s*([>\-–—])\s*(?P<text>.+?)\s*$'
    )

    # Load workbook
    if isinstance(source, (bytes, bytearray)):
        wb = load_workbook(BytesIO(source), data_only=True, read_only=True)
    elif isinstance(source, BytesIO):
        wb = load_workbook(source, data_only=True, read_only=True)
    elif isinstance(source, str):
        wb = load_workbook(source, data_only=True, read_only=True)
    else:
        raise TypeError("source must be a path, bytes, or BytesIO")

    out: List[Dict] = []

    worksheets = (
        [wb[s] for s in sheets if s in wb.sheetnames]
        if sheets else wb.worksheets
    )

    for ws in worksheets:
        for row in ws.iter_rows():

            # Ensure row has at least columns A–M (index 12)
            if len(row) < 13:
                continue

            col_L = row[11].value  # column L (12th column)
            col_M = row[12].value  # column M (13th column)

            # ---------------------------
            # UPDATED GUARD
            # Skip row if either column is empty, None, or only whitespace.
            # ---------------------------
            if not col_L or str(col_L).strip() == "":
                continue
            if not col_M or str(col_M).strip() == "":
                continue

            # Parse L with regex
            match = pat.match(str(col_L))
            if not match:
                continue

            num_raw = match.group("num")
            ask_text = match.group("text").strip().strip('"').strip("'")

            # Convert PI-Element to float when possible (e.g., "9.4")
            if num_raw.count(".") <= 1:
                try:
                    pi_value = float(num_raw)
                except ValueError:
                    pi_value = num_raw
            else:
                pi_value = num_raw  # hierarchical like "9.4.1" stays string

            out.append({
                "PI-Element": pi_value,
                "Ask/Look For": ask_text,
                "Calibrator notes": str(col_M).strip()
            })

    wb.close()
    return out
