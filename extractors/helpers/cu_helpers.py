"""Azure Content Understanding helpers.

This module provides direct binary upload to Content Understanding,
avoiding the need for intermediate blob storage.
"""
from __future__ import annotations
import time
from typing import Dict, Any, Optional

import requests

from .config import CUConfig


def cu_analyze_binary(
    cu: CUConfig,
    image_bytes: bytes,
    content_type: str = "image/png"
) -> Dict[str, Any]:
    """
    POST binary image data directly to CU analyzer and poll until done.
    Uses the :analyzeBinary endpoint per the official sample.
    
    Args:
        cu: Configuration for Content Understanding API
        image_bytes: Raw binary image data
        content_type: MIME type of the image (default: image/png)
    
    Returns:
        Raw analyzer result JSON
    """
    # Strip trailing slash from endpoint
    endpoint = cu.endpoint.rstrip("/")
    
    # Use :analyzeBinary endpoint for direct binary upload
    submit_url = (
        f"{endpoint}/contentunderstanding/analyzers/{cu.analyzer}:analyzeBinary"
        f"?api-version={cu.api_version}"
    )
    
    headers = {
        "Ocp-Apim-Subscription-Key": cu.key,
        "Content-Type": content_type,
    }
    
    # POST binary data directly
    resp = requests.post(submit_url, headers=headers, data=image_bytes, timeout=60)
    resp.raise_for_status()
    
    result_id = resp.json().get("id")
    if not result_id:
        raise RuntimeError("CU: no result id returned from analyzeBinary")
    
    # Poll for result
    return _poll_result(cu, result_id)


def cu_analyze_url(
    cu: CUConfig,
    image_url: str
) -> Dict[str, Any]:
    """
    POST URL to CU analyzer and poll until done.
    Uses the :analyze endpoint with inputs array for URL-based analysis.
    
    Args:
        cu: Configuration for Content Understanding API
        image_url: Publicly accessible URL to the image
    
    Returns:
        Raw analyzer result JSON
    """
    # Strip trailing slash from endpoint
    endpoint = cu.endpoint.rstrip("/")
    
    # Use :analyze endpoint with inputs array for URL
    submit_url = (
        f"{endpoint}/contentunderstanding/analyzers/{cu.analyzer}:analyze"
        f"?api-version={cu.api_version}"
    )
    
    headers = {
        "Ocp-Apim-Subscription-Key": cu.key,
        "Content-Type": "application/json",
    }
    
    # URL must be wrapped in inputs array per GA API spec
    payload = {"inputs": [{"source": {"type": "url", "url": image_url}}]}
    
    resp = requests.post(submit_url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    
    result_id = resp.json().get("id")
    if not result_id:
        raise RuntimeError("CU: no result id returned from analyze")
    
    # Poll for result
    return _poll_result(cu, result_id)


def _poll_result(cu: CUConfig, result_id: str) -> Dict[str, Any]:
    """Poll for analysis result until complete or timeout."""
    endpoint = cu.endpoint.rstrip("/")
    result_url = (
        f"{endpoint}/contentunderstanding/analyzerResults/{result_id}"
        f"?api-version={cu.api_version}"
    )
    
    headers = {"Ocp-Apim-Subscription-Key": cu.key}
    
    t0 = time.time()
    while True:
        resp = requests.get(result_url, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            j = resp.json()
            status = j.get("status", "").lower()
            
            if status in ("succeeded", "completed"):
                return j
            if status == "failed":
                raise RuntimeError(f"CU analysis failed: {j}")
        
        if time.time() - t0 > cu.timeout_seconds:
            raise TimeoutError("CU analysis timed out.")
        
        time.sleep(cu.poll_interval_seconds)


def normalize_cu_ocr(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Best-effort normalizer that tries to surface:
    - full text
    - per-line entries with text, confidence, polygon/bbox when available

    CU result schemas can evolve; this function is defensive.
    """
    out: Dict[str, Any] = {"engine": "azure-content-understanding", "text": "", "lines": []}

    def _push_line(text, conf=None, polygon=None):
        line = {"text": text}
        if conf is not None:
            line["confidence"] = conf
        if polygon is not None:
            line["polygon"] = polygon
        out["lines"].append(line)

    def _maybe_add_fulltext(s: Optional[str]):
        if s and s.strip():
            if out["text"]:
                out["text"] += "\n" + s
            else:
                out["text"] = s

    j = result

    # Case A: pages -> lines
    pages = j.get("pages") or j.get("content", {}).get("pages")
    if isinstance(pages, list):
        for pg in pages:
            lines = pg.get("lines")
            if isinstance(lines, list):
                for ln in lines:
                    txt = ln.get("content") or ln.get("text") or ""
                    conf = ln.get("confidence")
                    poly = ln.get("polygon") or ln.get("boundingBox") or None
                    if txt.strip():
                        _push_line(txt, conf, poly)
                        _maybe_add_fulltext(txt)

    # Case B: blocks
    blocks = j.get("blocks") or j.get("content", {}).get("blocks")
    if isinstance(blocks, list) and not out["lines"]:
        for b in blocks:
            txt = b.get("text") or b.get("content") or ""
            conf = b.get("confidence")
            poly = b.get("polygon") or b.get("boundingBox")
            if txt.strip():
                _push_line(txt, conf, poly)
                _maybe_add_fulltext(txt)

    # Case C: markdown/plain
    md = j.get("markdown") or j.get("content", {}).get("markdown")
    plain = j.get("text") or j.get("content", {}).get("text")
    _maybe_add_fulltext(plain)
    _maybe_add_fulltext(md)

    return out
