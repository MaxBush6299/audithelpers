from typing import Iterable, List, Dict, Union, Optional
from io import BytesIO
from openpyxl import load_workbook
import re
import argparse
import json
import sys
import os
from pathlib import Path

# Import cache storage abstraction
from extractors.helpers.cache_storage import (
    get_cache_storage,
    compute_file_hash,
    get_cache_key
)


def _load_xlsx_from_cache(
    xlsx_path: str,
    allow_local_cache: bool = False,
    verbose: bool = False
) -> Optional[List[Dict]]:
    """Load cached Excel extraction results if available."""
    if not os.path.exists(xlsx_path):
        return None
    
    storage = get_cache_storage(allow_local=allow_local_cache, verbose=False)
    if not storage.is_available:
        return None
    
    file_hash = compute_file_hash(xlsx_path)
    cache_key = get_cache_key(file_hash, prefix="xlsx")
    
    cached = storage.get(cache_key)
    if cached is not None:
        if cached.get("_cache_meta", {}).get("file_hash") == file_hash:
            elements = cached.get("elements", [])
            if verbose:
                print(f"[Excel] Cache hit! Loading {len(elements)} elements from cache")
            return elements
    
    return None


def _save_xlsx_to_cache(
    elements: List[Dict],
    xlsx_path: str,
    allow_local_cache: bool = False,
    verbose: bool = False
) -> None:
    """Save Excel extraction results to cache."""
    storage = get_cache_storage(allow_local=allow_local_cache, verbose=False)
    if not storage.is_available:
        return
    
    file_hash = compute_file_hash(xlsx_path)
    cache_key = get_cache_key(file_hash, prefix="xlsx")
    
    cached = {
        "_cache_meta": {
            "file_hash": file_hash,
            "source_file": os.path.basename(xlsx_path),
            "element_count": len(elements)
        },
        "elements": elements
    }
    
    storage.set(cache_key, cached)
    
    if verbose:
        print(f"[Excel] Cached {len(elements)} elements")


def extract_pi_rows_xlsx(
    source: Union[str, bytes, BytesIO],
    sheets: Iterable[str] = None, # type: ignore
    verbose: bool = False,
    use_cache: bool = True,
    allow_local_cache: bool = False
) -> List[Dict]:
    """
    Extract PI calibration elements from an Excel file.
    
    Reads columns L (Ask/Look For) and M (Calibrator notes) to extract
    PI element definitions.
    
    Args:
        source: Path to Excel file, bytes, or BytesIO
        sheets: Optional list of sheet names to process (default: all sheets)
        verbose: Print progress information
        use_cache: Whether to use cached results if available
        allow_local_cache: Allow local filesystem cache (for development only)
        
    Returns:
        List of dictionaries with PI-Element, Ask/Look For, Calibrator notes
    
    Optional env vars (for Azure Blob cache):
    - AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_NAME
    """
    
    # Check cache if source is a file path
    if use_cache and isinstance(source, str) and os.path.isfile(source):
        cached_result = _load_xlsx_from_cache(source, allow_local_cache, verbose)
        if cached_result is not None:
            return cached_result
    
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
    
    # Save to cache if source is a file path
    if use_cache and isinstance(source, str) and os.path.isfile(source):
        _save_xlsx_to_cache(out, source, allow_local_cache, verbose)
    
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
