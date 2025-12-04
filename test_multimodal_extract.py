"""
Test script for multimodal PPTX extraction.

This pipeline:
1. Renders slides as images using PowerPoint/LibreOffice
2. Extracts native text from the PPTX
3. Extracts OCR from embedded images using Document Intelligence
4. Sends ALL to LLM (GPT-4.1 or GPT-5.1) for accurate text extraction
5. Returns clean, structured JSON

Usage:
    python test_multimodal_extract.py          # Uses GPT-4.1 (default)
    python test_multimodal_extract.py --gpt5   # Uses GPT-5.1

Requires:
- PowerPoint (Windows) or LibreOffice (for slide rendering)
- pip install openai pymupdf comtypes
"""
import os
import sys
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from extractors.helpers import check_rendering_available


def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Multimodal PPTX extraction test")
    parser.add_argument("--gpt5", action="store_true", help="Use GPT-5.1 instead of GPT-4.1")
    args = parser.parse_args()
    
    model = "gpt-5.1" if args.gpt5 else "gpt-4.1"
    
    # Check prerequisites
    print("=" * 60)
    print(f"Multimodal PPTX Extraction Test ({model.upper()})")
    print("=" * 60)
    
    # Check rendering
    can_render, msg = check_rendering_available()
    if not can_render:
        print(f"\n❌ Rendering not available: {msg}")
        print("\nPlease install PowerPoint or LibreOffice first.")
        return
    
    print(f"✅ Rendering available: {msg}")
    
    # Check environment variables based on model
    if model == "gpt-5.1":
        required_vars = [
            "AZURE_AI_GPT5_ENDPOINT",
            "AZURE_AI_GPT5_API_KEY", 
            "GPT_5_1_DEPLOYMENT"
        ]
    else:
        required_vars = [
            "AZURE_AI_ENDPOINT",
            "AZURE_AI_API_KEY", 
            "GPT_4_1_DEPLOYMENT"
        ]
    
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        print(f"\n❌ Missing environment variables: {missing}")
        return
    
    print(f"✅ Environment variables configured for {model.upper()}")
    
    # Import after checks
    from extractors.helpers import quick_extract
    
    # Path to test PPTX
    pptx_path = os.path.join(
        os.path.dirname(__file__),
        "source-docs",
        "evidence1-6.pptx"
    )
    
    # Output path includes model name
    output_filename = f"evidence1-6_multimodal_{model.replace('.', '')}.json"
    output_path = os.path.join(
        os.path.dirname(__file__),
        "source-docs",
        output_filename
    )
    
    print(f"\n📄 Input: {pptx_path}")
    print(f"📝 Output: {output_path}")
    print(f"🤖 Model: {model.upper()}")
    print("-" * 60)
    
    # Run extraction with selected model
    result = quick_extract(pptx_path, output_path, verbose=True, model=model)
    
    # Summary
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"Total slides: {result['total_slides']}")
    
    # Show sample results
    print("\nSample results (first 5 slides):")
    for slide in result["slides"][:5]:
        slide_idx = slide.get("index", "?")
        text_preview = slide.get("text", "")[:60].replace("\n", " ")
        print(f"  Slide {slide_idx}: {text_preview}...")
    
    # Show file size
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        print(f"\n📊 Output file size: {size:,} bytes ({size/1024:.1f} KB)")
    
    print(f"\n✅ Full results saved to: {output_path}")


if __name__ == "__main__":
    main()
