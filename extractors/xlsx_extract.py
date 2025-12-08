from typing import Iterable, List, Dict, Union
from io import BytesIO
from openpyxl import load_workbook
import re
import argparse
import json
import sys
from pathlib import Path


def extract_pi_rows_xlsx(
    source: Union[str, bytes, BytesIO],
    sheets: Iterable[str] = None, # type: ignore
    verbose: bool = False
) -> List[Dict]:
    """
    Extract PI calibration elements from an Excel file.
    
    Reads columns L (Ask/Look For) and M (Calibrator notes) to extract
    PI element definitions.
    
    Args:
        source: Path to Excel file, bytes, or BytesIO
        sheets: Optional list of sheet names to process (default: all sheets)
        verbose: Print progress information
        
    Returns:
        List of dictionaries with PI-Element, Ask/Look For, Calibrator notes
    """
    
    pat = re.compile(
        r'^\s*(?P<num>\d+(?:\.\d+)*)\s*([>\-–—])\s*(?P<text>.+?)\s*$'
    )

    # Load workbook
    if verbose:
        print(f"Loading workbook...")
    
    if isinstance(source, (bytes, bytearray)):
        wb = load_workbook(BytesIO(source), data_only=True, read_only=True)
    elif isinstance(source, BytesIO):
        wb = load_workbook(source, data_only=True, read_only=True)
    elif isinstance(source, str):
        wb = load_workbook(source, data_only=True, read_only=True)
    else:
        raise TypeError("source must be a path, bytes, or BytesIO")

    out: List[Dict] = []
    rows_processed = 0
    rows_skipped = 0

    worksheets = (
        [wb[s] for s in sheets if s in wb.sheetnames]
        if sheets else wb.worksheets
    )
    
    if verbose:
        print(f"Processing {len(worksheets)} worksheet(s)...")

    for ws in worksheets:
        if verbose:
            print(f"  Reading sheet: {ws.title}")
        
        for row in ws.iter_rows():
            rows_processed += 1

            # Ensure row has at least columns A–M (index 12)
            if len(row) < 13:
                rows_skipped += 1
                continue

            col_L = row[11].value  # column L (12th column)
            col_M = row[12].value  # column M (13th column)

            # ---------------------------
            # UPDATED GUARD
            # Skip row if either column is empty, None, or only whitespace.
            # ---------------------------
            if not col_L or str(col_L).strip() == "":
                rows_skipped += 1
                continue
            if not col_M or str(col_M).strip() == "":
                rows_skipped += 1
                continue

            # Parse L with regex
            match = pat.match(str(col_L))
            if not match:
                rows_skipped += 1
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
    
    if verbose:
        print(f"Processed {rows_processed} rows, extracted {len(out)} elements, skipped {rows_skipped} rows")

    wb.close()
    return out


def main():
    """CLI entry point for Excel element extraction."""
    parser = argparse.ArgumentParser(
        description="Extract PI calibration elements from an Excel file (columns L and M)"
    )
    parser.add_argument(
        "input_xlsx",
        help="Path to the input Excel file"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output JSON file path (default: prints to stdout)"
    )
    parser.add_argument(
        "-s", "--sheets",
        nargs="+",
        default=None,
        help="Specific sheet names to process (default: all sheets)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress information"
    )
    
    args = parser.parse_args()
    
    # Validate input file exists
    input_path = Path(args.input_xlsx)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input_xlsx}", file=sys.stderr)
        sys.exit(1)
    
    if not input_path.suffix.lower() in [".xlsx", ".xlsm", ".xltx", ".xltm"]:
        print(f"Warning: File may not be an Excel file: {input_path.suffix}", file=sys.stderr)
    
    try:
        # Extract elements
        if args.verbose:
            print(f"Input: {args.input_xlsx}")
        
        elements = extract_pi_rows_xlsx(
            source=str(input_path),
            sheets=args.sheets,
            verbose=args.verbose
        )
        
        if not elements:
            print("Warning: No elements extracted. Check that columns L and M contain valid data.", file=sys.stderr)
        
        # Output results
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(elements, f, indent=2, ensure_ascii=False)
            
            if args.verbose:
                print(f"Output: {args.output}")
            print(f"Extracted {len(elements)} PI elements to {args.output}")
        else:
            # Print to stdout
            print(json.dumps(elements, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
