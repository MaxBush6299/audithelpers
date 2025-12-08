#!/usr/bin/env python3
"""
Utility to convert slides from extracted JSON to Markdown files.

Usage:
    python slide_to_markdown.py <json_file> <slide_number> [slide_number2 ...]
    python slide_to_markdown.py <json_file> --all
    python slide_to_markdown.py <json_file> 1-10  # Range of slides
    
Examples:
    python slide_to_markdown.py source-docs/evidence1-6_multimodal_gpt-51.json 4
    python slide_to_markdown.py source-docs/evidence1-6_multimodal_gpt-51.json 3 4 5
    python slide_to_markdown.py source-docs/evidence1-6_multimodal_gpt-51.json 1-10
    python slide_to_markdown.py source-docs/evidence1-6_multimodal_gpt-51.json --all -o output/
"""

import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional


def load_json(file_path: str) -> Dict[str, Any]:
    """Load the extracted JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_slide_by_index(data: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
    """Get a slide by its index number."""
    for slide in data.get('slides', []):
        if slide.get('index') == index:
            return slide
    return None


def extract_title(text: str) -> str:
    """Extract the title from the first line of text."""
    if not text:
        return "Untitled Slide"
    
    lines = text.strip().split('\n')
    first_line = lines[0].strip()
    
    # Clean up common artifacts
    first_line = re.sub(r'^#+\s*', '', first_line)  # Remove markdown headers
    first_line = first_line.strip()
    
    # Truncate if too long
    if len(first_line) > 80:
        first_line = first_line[:77] + "..."
    
    return first_line if first_line else "Untitled Slide"


def slide_to_markdown(slide: Dict[str, Any], source_file: str = "") -> str:
    """Convert a slide dictionary to markdown format."""
    index = slide.get('index', 0)
    text = slide.get('text', '')
    
    # Extract title from first meaningful line
    title = extract_title(text)
    
    # Build markdown
    lines = [
        f"# Slide {index}: {title}",
        "",
        "---",
        "",
        text,
        "",
        "---",
        "",
        f"*Source: {source_file} | Slide Index: {index}*"
    ]
    
    return '\n'.join(lines)


def parse_slide_range(range_str: str) -> List[int]:
    """Parse a range string like '1-10' into a list of integers."""
    if '-' in range_str:
        start, end = range_str.split('-')
        return list(range(int(start), int(end) + 1))
    return [int(range_str)]


def main():
    parser = argparse.ArgumentParser(
        description='Convert slides from extracted JSON to Markdown files.'
    )
    parser.add_argument('json_file', help='Path to the extracted JSON file')
    parser.add_argument('slides', nargs='*', help='Slide numbers to convert (e.g., 4, 3-10, or --all)')
    parser.add_argument('--all', action='store_true', help='Convert all slides')
    parser.add_argument('-o', '--output', default='.', help='Output directory (default: current directory)')
    
    args = parser.parse_args()
    
    # Load JSON
    data = load_json(args.json_file)
    source_name = Path(args.json_file).stem
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine which slides to convert
    slide_indices = []
    
    if args.all:
        slide_indices = [s['index'] for s in data.get('slides', [])]
    else:
        for s in args.slides:
            if '-' in s:
                slide_indices.extend(parse_slide_range(s))
            else:
                slide_indices.append(int(s))
    
    if not slide_indices:
        print("No slides specified. Use --all or provide slide numbers.")
        return
    
    # Convert each slide
    converted = []
    for idx in slide_indices:
        slide = get_slide_by_index(data, idx)
        if slide:
            md_content = slide_to_markdown(slide, Path(args.json_file).name)
            
            # Write individual file
            output_file = output_dir / f"slide_{idx:03d}.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            converted.append((idx, output_file))
            print(f"✅ Slide {idx} -> {output_file}")
        else:
            print(f"❌ Slide {idx} not found in JSON")
    
    # If multiple slides, also create a combined file
    if len(converted) > 1:
        combined_file = output_dir / f"{source_name}_slides.md"
        with open(combined_file, 'w', encoding='utf-8') as f:
            f.write(f"# Combined Slides from {Path(args.json_file).name}\n\n")
            for idx in slide_indices:
                slide = get_slide_by_index(data, idx)
                if slide:
                    f.write(slide_to_markdown(slide, Path(args.json_file).name))
                    f.write("\n\n---\n\n")
        print(f"\n📄 Combined file: {combined_file}")
    
    print(f"\n✨ Converted {len(converted)} slide(s)")


if __name__ == '__main__':
    main()
