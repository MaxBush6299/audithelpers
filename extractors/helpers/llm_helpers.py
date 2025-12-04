"""LLM helpers for multimodal slide analysis using Azure AI Foundry."""
from __future__ import annotations
import base64
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from openai import AzureOpenAI


@dataclass
class LLMConfig:
    """Azure AI Foundry / OpenAI configuration."""
    endpoint: str
    api_key: str
    deployment: str
    api_version: str = "2024-12-01-preview"
    
    def get_client(self) -> AzureOpenAI:
        """Create an Azure OpenAI client."""
        return AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )


# Simple text extraction prompt - combines native text + DI OCR from images
TEXT_EXTRACTION_PROMPT = """Analyze this slide image and provide an accurate text representation of ALL visible content.

## Previously Extracted Text (from multiple sources - may be incomplete or out of order):
{extracted_text}

Note: The extracted text above comes from:
- Native text boxes in the slide
- OCR from embedded images/screenshots (marked with [Image OCR])
- Speaker notes and tables

## Instructions:
1. Look at the slide image carefully - this is the ground truth
2. Use the extracted text as a reference, but trust the image for accuracy
3. Transcribe ALL visible text in logical reading order (top to bottom, left to right)
4. Preserve the structure - use headers, bullet points, and line breaks appropriately
5. Include text from any embedded images, charts, tables, or screenshots
6. If there are forms or tables, represent them clearly
7. Do NOT summarize or interpret - just extract the text accurately

Return the text content only, formatted for readability.
"""


def encode_image_base64(image_bytes: bytes) -> str:
    """Encode image bytes to base64 string."""
    return base64.b64encode(image_bytes).decode("utf-8")


def analyze_slide_multimodal(
    config: LLMConfig,
    slide_image_bytes: bytes,
    extracted_text: str,
    image_media_type: str = "image/png",
    use_max_completion_tokens: bool = False
) -> str:
    """
    Extract accurate text representation from a slide using LLM vision.
    
    Args:
        config: LLM configuration
        slide_image_bytes: The slide rendered as an image (PNG/JPEG)
        extracted_text: Pre-extracted text from the slide (for reference)
        image_media_type: MIME type of the image
        use_max_completion_tokens: If True, use max_completion_tokens instead of max_tokens
                                   (required for GPT-5.1 and newer o-series models)
        
    Returns:
        Clean text representation of the slide content
    """
    client = config.get_client()
    
    # Encode image
    image_b64 = encode_image_base64(slide_image_bytes)
    
    # Build the prompt
    prompt = TEXT_EXTRACTION_PROMPT.format(extracted_text=extracted_text)
    
    # Build completion kwargs - GPT-5.1 uses max_completion_tokens instead of max_tokens
    completion_kwargs = {
        "model": config.deployment,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{image_media_type};base64,{image_b64}",
                            "detail": "high"  # Use high detail for document analysis
                        }
                    }
                ]
            }
        ],
        "temperature": 0.1,  # Low temperature for accurate extraction
    }
    
    # Use appropriate token parameter based on model
    if use_max_completion_tokens:
        completion_kwargs["max_completion_tokens"] = 4000
    else:
        completion_kwargs["max_tokens"] = 4000
    
    # Call the model with vision
    response = client.chat.completions.create(**completion_kwargs)
    
    return response.choices[0].message.content.strip()


def batch_analyze_slides(
    config: LLMConfig,
    slides_data: List[Dict[str, Any]],
    render_slide_func,
    verbose: bool = True
) -> List[Dict[str, Any]]:
    """
    Analyze multiple slides with multimodal fusion.
    
    Args:
        config: LLM configuration
        slides_data: List of slide dictionaries with 'index', 'text', 'images' keys
        render_slide_func: Function that takes (pptx_path, slide_index) and returns PNG bytes
        verbose: Print progress
        
    Returns:
        List of structured evidence for each slide
    """
    results = []
    
    for slide in slides_data:
        slide_idx = slide["index"]
        
        if verbose:
            print(f"[LLM] Analyzing slide {slide_idx}...")
        
        # Combine all extracted text for this slide
        text_parts = []
        
        # Native text
        for t in slide.get("text", []):
            if isinstance(t, dict) and t.get("text"):
                text_parts.append(t["text"])
            elif isinstance(t, str):
                text_parts.append(t)
        
        # OCR from images
        for img in slide.get("images", []):
            ocr = img.get("ocr", {})
            if isinstance(ocr, dict) and ocr.get("text"):
                text_parts.append(f"[Image OCR]: {ocr['text']}")
        
        extracted_text = "\n\n".join(text_parts)
        
        # Get slide image
        # Note: render_slide_func needs to be provided by caller
        # For now, we'll store the extracted text and note that image is needed
        
        results.append({
            "slide_index": slide_idx,
            "extracted_text": extracted_text,
            "analysis": None,  # Will be filled when image is provided
            "needs_image": True
        })
    
    return results


def flatten_extracted_text(slide: Dict[str, Any]) -> str:
    """
    Flatten all text from a slide (native text + OCR) into a single string.
    
    Args:
        slide: Slide dictionary with 'text' and 'images' keys
        
    Returns:
        Combined text string
    """
    text_parts = []
    
    # Native text
    for t in slide.get("text", []):
        if isinstance(t, dict):
            text = t.get("text", "")
            text_type = t.get("type", "")
            if text and text_type != "table_cell":  # Skip individual table cells
                text_parts.append(text)
        elif isinstance(t, str):
            text_parts.append(t)
    
    # OCR from images
    for img in slide.get("images", []):
        ocr = img.get("ocr", {})
        if isinstance(ocr, dict):
            ocr_text = ocr.get("text", "")
            if ocr_text and not ocr.get("skipped"):
                text_parts.append(f"[From embedded image]: {ocr_text}")
    
    return "\n\n".join(text_parts)
