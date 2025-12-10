"""Slide rendering helpers - convert PPTX slides to images."""
from __future__ import annotations
import io
import subprocess
import tempfile
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple
import shutil


def render_slides_with_powerpoint(
    pptx_path: str,
    output_dir: str,
    dpi: int = 150
) -> List[str]:
    """
    Render all slides in a PPTX to PNG images using PowerPoint COM (Windows only).
    
    Args:
        pptx_path: Path to the PPTX file
        output_dir: Directory to save PNG files
        dpi: Resolution (higher = better quality, larger files)
        
    Returns:
        List of paths to generated PNG files, sorted by slide number
    """
    if sys.platform != "win32":
        raise RuntimeError("PowerPoint COM automation only works on Windows")
    
    try:
        import comtypes.client
    except ImportError:
        raise RuntimeError("comtypes not installed. Run: pip install comtypes")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Absolute paths required for COM
    pptx_path = os.path.abspath(pptx_path)
    output_dir = os.path.abspath(output_dir)
    
    # Calculate export dimensions based on DPI
    # PowerPoint default is 96 DPI, we scale from there
    scale_factor = dpi / 96.0
    width = int(1920 * scale_factor)  # Full HD base width
    height = int(1080 * scale_factor)  # Full HD base height
    
    powerpoint = None
    presentation = None
    
    try:
        # Create PowerPoint COM object
        powerpoint = comtypes.client.CreateObject("PowerPoint.Application")
        powerpoint.Visible = 1  # Required for export to work properly
        
        # Open the presentation
        presentation = powerpoint.Presentations.Open(pptx_path, WithWindow=False)
        
        png_paths = []
        
        # Export each slide
        for i, slide in enumerate(presentation.Slides, 1):
            output_path = os.path.join(output_dir, f"slide_{i:03d}.png")
            slide.Export(output_path, "PNG", width, height)
            png_paths.append(output_path)
        
        return png_paths
        
    finally:
        # Clean up COM objects
        if presentation:
            presentation.Close()
        if powerpoint:
            powerpoint.Quit()


def render_slides_with_libreoffice(
    pptx_path: str,
    output_dir: str,
    dpi: int = 150
) -> List[str]:
    """
    Render all slides in a PPTX to PNG images using LibreOffice.
    
    Requires LibreOffice to be installed:
    - Windows: choco install libreoffice-fresh
    - Mac: brew install --cask libreoffice
    - Linux: apt install libreoffice
    
    Args:
        pptx_path: Path to the PPTX file
        output_dir: Directory to save PNG files
        dpi: Resolution (150 is good balance of quality/size)
        
    Returns:
        List of paths to generated PNG files, sorted by slide number
    """
    # Find LibreOffice
    soffice = _find_libreoffice()
    if not soffice:
        raise RuntimeError(
            "LibreOffice not found. Install it:\n"
            "  Windows: choco install libreoffice-fresh\n"
            "  Mac: brew install --cask libreoffice\n"
            "  Linux: apt install libreoffice"
        )
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert PPTX to PDF first (LibreOffice does this well)
    # Then we can use other tools or LibreOffice to convert to images
    
    # LibreOffice's direct PNG export only creates ONE image for the whole presentation,
    # not one per slide. So we ALWAYS use the PDF method for PPTX files to get per-slide images.
    # The direct PNG export is kept as a fallback only for single-page documents.
    
    # Always use PDF method for PPTX (multi-slide documents)
    return _render_via_pdf(pptx_path, output_dir, soffice, dpi)


def _render_via_pdf(
    pptx_path: str,
    output_dir: str,
    soffice: str,
    dpi: int
) -> List[str]:
    """Fallback: Convert PPTX -> PDF -> PNG images."""
    import fitz  # PyMuPDF
    
    # Convert to PDF
    with tempfile.TemporaryDirectory() as tmp_dir:
        cmd = [
            soffice,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", tmp_dir,
            pptx_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Find the PDF
        pdf_files = list(Path(tmp_dir).glob("*.pdf"))
        if not pdf_files:
            raise RuntimeError("LibreOffice failed to create PDF")
        
        pdf_path = pdf_files[0]
        
        # Convert PDF pages to PNG
        doc = fitz.open(str(pdf_path))
        png_paths = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Render at higher DPI for readability
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)
            
            output_path = os.path.join(output_dir, f"slide_{page_num + 1:03d}.png")
            pix.save(output_path)
            png_paths.append(output_path)
        
        doc.close()
        
    return png_paths


def _find_libreoffice() -> Optional[str]:
    """Find LibreOffice executable on the system."""
    # Common paths
    candidates = [
        # Windows
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        # Mac
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        # Linux
        "/usr/bin/soffice",
        "/usr/bin/libreoffice",
    ]
    
    # Check PATH first
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        return soffice
    
    # Check common paths
    for path in candidates:
        if os.path.isfile(path):
            return path
    
    return None


def _extract_slide_number(filename: str) -> int:
    """Extract slide number from filename for sorting."""
    import re
    match = re.search(r'(\d+)', filename)
    return int(match.group(1)) if match else 0


def render_slide_to_bytes(
    pptx_path: str,
    slide_index: int,
    dpi: int = 150,
    cache_dir: Optional[str] = None
) -> bytes:
    """
    Render a single slide to PNG bytes.
    
    Args:
        pptx_path: Path to the PPTX file
        slide_index: 1-based slide index
        dpi: Resolution
        cache_dir: Optional directory to cache rendered slides
        
    Returns:
        PNG image as bytes
    """
    # Use cache if available
    if cache_dir:
        cache_path = os.path.join(cache_dir, f"slide_{slide_index:03d}.png")
        if os.path.exists(cache_path):
            with open(cache_path, "rb") as f:
                return f.read()
    
    # Render all slides (LibreOffice doesn't support single-slide export easily)
    with tempfile.TemporaryDirectory() as tmp_dir:
        png_paths = render_slides_with_libreoffice(pptx_path, tmp_dir, dpi)
        
        if slide_index > len(png_paths):
            raise ValueError(f"Slide {slide_index} not found (only {len(png_paths)} slides)")
        
        slide_path = png_paths[slide_index - 1]
        
        with open(slide_path, "rb") as f:
            image_bytes = f.read()
        
        # Cache if requested
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
            # Copy all rendered slides to cache
            for i, p in enumerate(png_paths, 1):
                cache_path = os.path.join(cache_dir, f"slide_{i:03d}.png")
                if not os.path.exists(cache_path):
                    shutil.copy(p, cache_path)
        
        return image_bytes


def check_rendering_available() -> Tuple[bool, str]:
    """
    Check if slide rendering is available.
    
    Checks in order:
    1. PowerPoint COM (Windows only)
    2. LibreOffice
    
    Returns:
        (is_available, message)
    """
    # On Windows, check for PowerPoint first
    if sys.platform == "win32":
        try:
            import comtypes.client
            # Try to create PowerPoint - will fail if not installed
            ppt = comtypes.client.CreateObject("PowerPoint.Application")
            ppt.Quit()
            return True, "Ready (PowerPoint COM)"
        except Exception:
            pass  # Fall through to LibreOffice check
    
    # Check LibreOffice
    soffice = _find_libreoffice()
    if soffice:
        try:
            import fitz
            return True, f"Ready (LibreOffice: {soffice})"
        except ImportError:
            return False, "PyMuPDF not installed. Run: pip install pymupdf"
    
    # Nothing available
    if sys.platform == "win32":
        return False, (
            "No rendering engine found. Options:\n"
            "  1. Install Microsoft PowerPoint\n"
            "  2. Install LibreOffice: choco install libreoffice-fresh"
        )
    else:
        return False, (
            "LibreOffice not found. Install it:\n"
            "  Mac: brew install --cask libreoffice\n"
            "  Linux: apt install libreoffice"
        )
