"""Azure Document Intelligence helpers for OCR and document extraction."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import io

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult
from azure.core.credentials import AzureKeyCredential


@dataclass
class DIConfig:
    """Configuration for Document Intelligence."""
    endpoint: str
    key: str
    model_id: str = "prebuilt-layout"  # Options: prebuilt-layout, prebuilt-read, prebuilt-document
    
    def get_client(self) -> DocumentIntelligenceClient:
        """Create a Document Intelligence client."""
        return DocumentIntelligenceClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key)
        )


def analyze_document_bytes(
    config,  # DIConfig from config.py
    document_bytes: bytes,
    content_type: str = "application/octet-stream"
) -> AnalyzeResult:
    """
    Analyze a document from bytes using Document Intelligence.
    
    Args:
        config: Document Intelligence configuration
        document_bytes: Raw document bytes
        content_type: MIME type of the document
        
    Returns:
        AnalyzeResult with extracted content
    """
    print(f"[DEBUG DI] Creating client for endpoint: {config.endpoint}")
    client = config.get_client()
    
    print(f"[DEBUG DI] Calling begin_analyze_document with model={config.model_id}, content_type={content_type}, bytes={len(document_bytes)}")
    # The SDK expects the bytes in a specific format
    poller = client.begin_analyze_document(
        model_id=config.model_id,
        body=document_bytes,
        content_type=content_type
    )
    
    print(f"[DEBUG DI] Waiting for result (this may take a moment)...")
    result = poller.result()
    print(f"[DEBUG DI] Result received!")
    return result


def analyze_image_bytes(
    config: DIConfig,
    image_bytes: bytes,
    content_type: str = "image/png"
) -> Dict[str, Any]:
    """
    Analyze an image and extract OCR text using Document Intelligence.
    
    Args:
        config: Document Intelligence configuration
        image_bytes: Raw image bytes
        content_type: MIME type (image/png, image/jpeg, etc.)
        
    Returns:
        Normalized OCR result dict with text and lines
    """
    result = analyze_document_bytes(config, image_bytes, content_type)
    return normalize_di_result(result)


def analyze_document_file(
    config: DIConfig,
    file_path: str
) -> AnalyzeResult:
    """
    Analyze a document file using Document Intelligence.
    
    Args:
        config: Document Intelligence configuration
        file_path: Path to the document file
        
    Returns:
        AnalyzeResult with extracted content
    """
    # Determine content type from extension
    import os
    ext = os.path.splitext(file_path)[1].lower()
    content_types = {
        ".pdf": "application/pdf",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".tiff": "image/tiff",
        ".bmp": "image/bmp",
    }
    content_type = content_types.get(ext, "application/octet-stream")
    
    with open(file_path, "rb") as f:
        document_bytes = f.read()
    
    return analyze_document_bytes(config, document_bytes, content_type)


def normalize_di_result(result: AnalyzeResult, compact: bool = True) -> Dict[str, Any]:
    """
    Normalize Document Intelligence result to a standard format.
    
    Args:
        result: AnalyzeResult from Document Intelligence
        compact: If True, return simplified structure (text only). 
                 If False, include full details (lines, polygons, pages).
    
    Returns:
        Dict with extracted content. Compact mode returns just text.
    """
    if compact:
        # Simplified structure - just the text content
        return {
            "text": result.content or ""
        }
    
    # Full structure with all details
    output: Dict[str, Any] = {
        "engine": "azure-document-intelligence",
        "text": result.content or "",
        "lines": [],
        "pages": [],
        "tables": [],
    }
    
    # Extract lines from pages
    if result.pages:
        for page in result.pages:
            page_info = {
                "page_number": page.page_number,
                "width": page.width,
                "height": page.height,
                "unit": page.unit,
                "lines": []
            }
            
            if page.lines:
                for line in page.lines:
                    line_data = {
                        "text": line.content,
                        "polygon": line.polygon if line.polygon else None,
                    }
                    output["lines"].append(line_data)
                    page_info["lines"].append(line_data)
            
            output["pages"].append(page_info)
    
    # Extract tables
    if result.tables:
        for table in result.tables:
            table_data = {
                "row_count": table.row_count,
                "column_count": table.column_count,
                "cells": []
            }
            
            if table.cells:
                for cell in table.cells:
                    cell_data = {
                        "row_index": cell.row_index,
                        "column_index": cell.column_index,
                        "content": cell.content,
                        "row_span": cell.row_span or 1,
                        "column_span": cell.column_span or 1,
                    }
                    table_data["cells"].append(cell_data)
            
            output["tables"].append(table_data)
    
    return output


def extract_text_from_result(result: AnalyzeResult) -> str:
    """Extract plain text from Document Intelligence result."""
    return result.content or ""


def extract_tables_from_result(result: AnalyzeResult) -> List[Dict[str, Any]]:
    """
    Extract tables from Document Intelligence result as structured data.
    
    Returns list of tables, each as a 2D list of cell contents.
    """
    tables = []
    
    if result.tables:
        for table in result.tables:
            # Create 2D array for table
            rows = [[None] * table.column_count for _ in range(table.row_count)]
            
            if table.cells:
                for cell in table.cells:
                    rows[cell.row_index][cell.column_index] = cell.content
            
            tables.append({
                "rows": rows,
                "row_count": table.row_count,
                "column_count": table.column_count
            })
    
    return tables
