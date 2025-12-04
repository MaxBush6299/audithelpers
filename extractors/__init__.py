"""
Extractors package for AI Calibration evidence documents.

Main modules:
- ppt_extract: PowerPoint extraction with Document Intelligence OCR
- xlsx_extract: Excel extraction

Example usage:
    from extractors.ppt_extract import pptx_to_unified_json
    from extractors.xlsx_extract import extract_xlsx
    
    # Extract PPTX with compact output
    result = pptx_to_unified_json("presentation.pptx", compact=True)
    
    # Extract Excel
    result = extract_xlsx("workbook.xlsx")
"""

from .ppt_extract import pptx_to_unified_json
from .xlsx_extract import extract_xlsx

__all__ = [
    "pptx_to_unified_json",
    "extract_xlsx",
]
