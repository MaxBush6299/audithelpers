"""Test script for PPTX extraction with Azure Document Intelligence.

This script uses Document Intelligence for OCR with simplified output structure.
"""
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extractors.ppt_extract import pptx_to_unified_json
from extractors.helpers.config import DIConfig

def main():
    # Configure Document Intelligence from environment
    di = DIConfig(
        endpoint=os.getenv("AZURE_DI_ENDPOINT"),
        key=os.getenv("AZURE_DI_KEY"),
        model_id=os.getenv("AZURE_DI_MODEL", "prebuilt-layout"),
    )
    
    # Path to test PPTX
    pptx_path = os.path.join(
        os.path.dirname(__file__), 
        "source-docs", 
        "evidence1-6.pptx"
    )
    
    print(f"Processing: {pptx_path}")
    print(f"Using endpoint: {di.endpoint}")
    print(f"Using model: {di.model_id}")
    print("-" * 50)
    
    # Extract content with compact mode (simplified structure)
    result = pptx_to_unified_json(pptx_path, di, compact=True)
    
    # Save output
    output_path = os.path.join(
        os.path.dirname(__file__), 
        "source-docs", 
        "evidence1-6_extracted.json"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Save unsupported images list separately if any exist
    unsupported = result.get("unsupported_images", [])
    if unsupported:
        unsupported_path = os.path.join(
            os.path.dirname(__file__), 
            "source-docs", 
            "evidence1-6_unsupported_images.json"
        )
        with open(unsupported_path, "w", encoding="utf-8") as f:
            json.dump({
                "source_file": os.path.basename(pptx_path),
                "total_unsupported": len(unsupported),
                "images": unsupported
            }, f, indent=2, ensure_ascii=False)
        print(f"\n⚠️  {len(unsupported)} unsupported images found - saved to: {unsupported_path}")
    
    # Summary
    print(f"\nExtracted {len(result['slides'])} slides")
    for slide in result["slides"][:10]:  # Show first 10
        title = slide.get("title", "(no title)")
        text_count = len(slide.get("text", []))
        image_count = len(slide.get("images", []))
        print(f"  Slide {slide['index']}: {title[:40]}... | {text_count} text blocks, {image_count} images")
    
    if len(result['slides']) > 10:
        print(f"  ... and {len(result['slides']) - 10} more slides")
    
    print(f"\n✅ Output saved to: {output_path}")
    
    # Show file size comparison
    file_size = os.path.getsize(output_path)
    print(f"📊 Output file size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")

if __name__ == "__main__":
    main()
