"""
Multimodal PPTX Extraction Pipeline

Combines ALL THREE sources for optimal extraction:
1. Native text extraction from PPTX (cleanest for text boxes)
2. Document Intelligence OCR on embedded images (catches text in screenshots)
3. LLM vision (GPT-4.1) to validate, structure, and reconcile all sources

Output: Clean, simplified JSON per slide with the most accurate text content.
"""
import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .config import DIConfig
from .llm_helpers import LLMConfig, analyze_slide_multimodal
from .slide_renderer import (
    render_slides_with_libreoffice, 
    render_slides_with_powerpoint,
    check_rendering_available
)
from .pptx_helpers import iter_text_shapes, iter_table_cells, iter_images
from .di_helpers import analyze_image_bytes, normalize_di_result

from pptx import Presentation
import sys


@dataclass
class MultimodalConfig:
    """Configuration for the multimodal extraction pipeline."""
    llm: LLMConfig                  # GPT-4.1 for text extraction from images
    di: Optional[DIConfig] = None   # Document Intelligence for embedded image OCR
    render_dpi: int = 150           # Slide render quality
    cache_rendered_slides: bool = True
    use_di_for_images: bool = True  # Whether to OCR embedded images with DI


def extract_native_text(slide, include_tables: bool = True) -> str:
    """Extract native text from a slide (no OCR)."""
    text_parts = []
    
    # Native text boxes
    for t in iter_text_shapes(slide):
        if t.get("text"):
            text_parts.append(t["text"])
    
    # Speaker notes
    if slide.has_notes_slide:
        try:
            notes = slide.notes_slide.notes_text_frame.text
            if notes and notes.strip():
                text_parts.append(f"[Speaker Notes]: {notes}")
        except Exception:
            pass
    
    # Tables
    if include_tables:
        table_text = []
        for c in iter_table_cells(slide):
            if c.get("text"):
                table_text.append(c["text"])
        if table_text:
            text_parts.append(f"[Table]: {' | '.join(table_text)}")
    
    return "\n\n".join(text_parts)


# Supported image formats for Document Intelligence
SUPPORTED_IMAGE_FORMATS = {"jpg", "jpeg", "png", "bmp", "tiff", "tif", "heif", "heic", "pdf"}


def extract_di_ocr_from_images(slide, di_config: DIConfig, slide_index: int) -> str:
    """Extract OCR text from embedded images using Document Intelligence."""
    ocr_parts = []
    
    for img in iter_images(slide):
        # Check if format is supported
        ext = img.get("ext", "").lower().lstrip(".")
        if ext not in SUPPORTED_IMAGE_FORMATS:
            continue
            
        img_bytes = img.get("blob")
        if not img_bytes:
            continue
        
        try:
            result = analyze_image_bytes(di_config, img_bytes, ext)
            normalized = normalize_di_result(result, compact=True)
            text = normalized.get("text", "").strip()
            if text:
                ocr_parts.append(f"[Image OCR]: {text}")
        except Exception:
            # Skip failed OCR silently
            pass
    
    return "\n\n".join(ocr_parts)


def multimodal_extract(
    pptx_path: str,
    config: MultimodalConfig,
    output_path: Optional[str] = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Extract text from a PPTX using multimodal LLM analysis.
    
    Pipeline:
    1. Render all slides to images
    2. Extract native text from each slide (for reference)
    3. Send image + text to GPT-4.1 for accurate text extraction
    4. Return simplified JSON
    
    Args:
        pptx_path: Path to the PPTX file
        config: Multimodal configuration
        output_path: Optional path to save output JSON
        verbose: Print progress
        
    Returns:
        Simplified JSON with slides containing index, title, and text content
    """
    import tempfile
    
    # Check rendering availability
    can_render, msg = check_rendering_available()
    if not can_render:
        raise RuntimeError(f"Slide rendering not available: {msg}")
    
    if verbose:
        print(f"[Pipeline] Opening: {pptx_path}")
    
    prs = Presentation(pptx_path)
    total_slides = len(prs.slides)
    
    if verbose:
        print(f"[Pipeline] Found {total_slides} slides")
    
    # Step 1: Render slides to images
    if verbose:
        print(f"[Pipeline] Rendering slides to images...")
    
    if config.cache_rendered_slides:
        cache_dir = os.path.join(os.path.dirname(pptx_path), ".slide_cache")
        os.makedirs(cache_dir, exist_ok=True)
    else:
        cache_dir = tempfile.mkdtemp()
    
    # Use PowerPoint on Windows if available, else LibreOffice
    try:
        if sys.platform == "win32":
            try:
                import comtypes.client
                slide_images = render_slides_with_powerpoint(pptx_path, cache_dir, config.render_dpi)
                if verbose:
                    print(f"[Pipeline] Using PowerPoint COM for rendering")
            except Exception as e:
                if verbose:
                    print(f"[Pipeline] PowerPoint not available, trying LibreOffice: {e}")
                slide_images = render_slides_with_libreoffice(pptx_path, cache_dir, config.render_dpi)
        else:
            slide_images = render_slides_with_libreoffice(pptx_path, cache_dir, config.render_dpi)
    except Exception as e:
        raise RuntimeError(f"Failed to render slides: {e}")
    
    if verbose:
        print(f"[Pipeline] Rendered {len(slide_images)} slide images")
    
    # Check if DI is configured for embedded image OCR
    use_di = config.use_di_for_images and config.di is not None
    if verbose:
        if use_di:
            print(f"[Pipeline] Document Intelligence enabled for embedded image OCR")
        else:
            print(f"[Pipeline] Document Intelligence not configured (using native text only)")
    
    # Step 2 & 3: Process each slide with all three sources
    results = []
    
    for i, slide in enumerate(prs.slides, start=1):
        if verbose:
            print(f"[Pipeline] Processing slide {i}/{total_slides}...")
        
        # Source 1: Native text from PPTX (cleanest for text boxes)
        native_text = extract_native_text(slide)
        
        # Source 2: DI OCR from embedded images (catches text in screenshots)
        di_ocr_text = ""
        if use_di:
            try:
                di_ocr_text = extract_di_ocr_from_images(slide, config.di, i)
                if di_ocr_text and verbose:
                    print(f"[Pipeline]   DI OCR extracted from embedded images")
            except Exception as e:
                if verbose:
                    print(f"[Pipeline]   DI OCR failed: {e}")
        
        # Combine native text + DI OCR for LLM context
        combined_extracted_text = native_text
        if di_ocr_text:
            combined_extracted_text = f"{native_text}\n\n{di_ocr_text}"
        
        # Source 3: LLM vision on rendered slide image
        if i <= len(slide_images):
            with open(slide_images[i - 1], "rb") as f:
                slide_image_bytes = f.read()
        else:
            if verbose:
                print(f"[Pipeline]   Warning: No image for slide {i}")
            slide_image_bytes = None
        
        # Send ALL sources to LLM for final reconciliation
        if slide_image_bytes:
            try:
                llm_text = analyze_slide_multimodal(
                    config.llm,
                    slide_image_bytes,
                    combined_extracted_text  # Now includes both native + DI OCR
                )
                
                if verbose:
                    preview = llm_text[:60].replace("\n", " ") if llm_text else "(empty)"
                    print(f"[Pipeline]   -> Extracted: {preview}...")
                    
            except Exception as e:
                if verbose:
                    print(f"[Pipeline]   Error analyzing slide {i}: {e}")
                llm_text = combined_extracted_text  # Fallback to combined text
        else:
            llm_text = combined_extracted_text
        
        results.append({
            "index": i,
            "text": llm_text
        })
    
    output = {
        "source_file": os.path.basename(pptx_path),
        "total_slides": total_slides,
        "slides": results
    }
    
    # Save if requested
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        if verbose:
            print(f"[Pipeline] Output saved to: {output_path}")
    
    return output


def quick_extract(
    pptx_path: str,
    output_path: Optional[str] = None,
    verbose: bool = True,
    use_di: bool = True
) -> Dict[str, Any]:
    """
    Convenience function that loads config from environment variables.
    
    Combines ALL THREE sources for optimal extraction:
    1. Native text from PPTX (cleanest for text boxes)
    2. Document Intelligence OCR on embedded images (catches text in screenshots)
    3. LLM vision (GPT-4.1) to validate and reconcile all sources
    
    Required env vars:
    - AZURE_AI_ENDPOINT, AZURE_AI_API_KEY, GPT_4_1_DEPLOYMENT
    
    Optional env vars (for DI OCR):
    - AZURE_DI_ENDPOINT, AZURE_DI_KEY
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    # LLM config (required)
    llm_config = LLMConfig(
        endpoint=os.environ["AZURE_AI_ENDPOINT"],
        api_key=os.environ["AZURE_AI_API_KEY"],
        deployment=os.environ["GPT_4_1_DEPLOYMENT"]
    )
    
    # DI config (optional - for embedded image OCR)
    di_config = None
    if use_di and os.getenv("AZURE_DI_ENDPOINT") and os.getenv("AZURE_DI_KEY"):
        di_config = DIConfig(
            endpoint=os.environ["AZURE_DI_ENDPOINT"],
            key=os.environ["AZURE_DI_KEY"]
        )
    
    config = MultimodalConfig(
        llm=llm_config,
        di=di_config,
        use_di_for_images=use_di and di_config is not None
    )
    
    return multimodal_extract(pptx_path, config, output_path, verbose)
