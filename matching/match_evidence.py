#!/usr/bin/env python3
"""
Evidence-to-Element Matcher

This utility matches slide evidence to PI calibration elements, creating a structured
JSON output that links each PI element with its calibrator instructions and supporting
evidence slides.

Usage:
    python match_evidence_to_elements.py <elements_json> <evidence_json> [-o output_file]

Example:
    python match_evidence_to_elements.py source-docs/elements.json source-docs/evidence1-6_multimodal_gpt-51.json -o source-docs/matched_evidence.json
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from utils.element_extract import (
        extract_element_references,
        get_primary_element,
        get_all_elements,
        normalize_element_id,
        element_to_float,
        is_section_header
    )
except ImportError:
    # If utils not found, define inline (for standalone usage)
    import re
    
    ELEMENT_PATTERNS = [
        (r'(\d+\.\d+[A-Za-z]?)\s*>', 'arrow_format'),
        (r'NEXT\s+(\d+\.\d+[A-Za-z]?)\s*>', 'next_arrow_format'),
        (r'PI[\s-]?(\d+)', 'pi_header'),
        (r'\((\d+\.\d+[A-Za-z]?)\)', 'parentheses_format'),
        (r'[Ee]lement\s+(\d+\.\d+[A-Za-z]?)', 'element_explicit'),
        (r'PI\s+\d+\s*[–-]\s*\w+.*?\((\d+\.\d+[A-Za-z]?)\)', 'slide_title_format'),
    ]
    COMPILED_PATTERNS = [(re.compile(p, re.IGNORECASE), n) for p, n in ELEMENT_PATTERNS]
    
    def normalize_element_id(element_id: str) -> str:
        element_id = element_id.strip()
        if element_id and element_id[-1].isalpha():
            element_id = element_id[:-1] + element_id[-1].upper()
        return element_id
    
    def extract_element_references(text: str) -> List[tuple]:
        matches = []
        for pattern, pattern_name in COMPILED_PATTERNS:
            for match in pattern.finditer(text):
                element_id = normalize_element_id(match.group(1))
                matches.append((element_id, pattern_name))
        return matches
    
    def get_primary_element(text: str) -> Optional[str]:
        matches = extract_element_references(text)
        if not matches:
            return None
        priority = ['arrow_format', 'next_arrow_format', 'slide_title_format', 
                    'element_explicit', 'parentheses_format', 'pi_header']
        for pattern_type in priority:
            for element_id, match_type in matches:
                if match_type == pattern_type:
                    return element_id
        return matches[0][0] if matches else None
    
    def get_all_elements(text: str) -> Set[str]:
        matches = extract_element_references(text)
        return {element_id for element_id, _ in matches}
    
    def element_to_float(element_id: str) -> float:
        numeric_part = re.sub(r'[A-Za-z]+$', '', element_id)
        try:
            return float(numeric_part)
        except ValueError:
            return 0.0
    
    def is_section_header(text: str) -> bool:
        lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
        if len(lines) <= 3:
            header_pattern = re.compile(r'^PI\s*\d+\s*[–-]', re.IGNORECASE)
            for line in lines:
                if header_pattern.match(line):
                    if 'ask/look for' not in text.lower() and '>' not in text:
                        return True
        return False


@dataclass
class EvidenceSlide:
    """Represents evidence from a slide matched to an element."""
    slide_index: int
    text: str
    text_preview: str  # First 200 chars for quick reference
    match_pattern: str
    all_elements_in_slide: List[str]
    is_primary_match: bool
    source_file: str = ""  # Which PPTX file this slide came from
    source_index: int = 0  # Original slide number within that file


@dataclass
class MatchedElement:
    """Represents a PI element with its calibrator instructions and matched evidence."""
    pi_element: str
    ask_look_for: str
    calibrator_notes: str
    evidence: List[EvidenceSlide] = field(default_factory=list)
    evidence_count: int = 0


@dataclass
class MatchingResult:
    """Complete result of the matching process."""
    metadata: Dict[str, Any]
    matched_elements: List[MatchedElement]
    unmatched_slides: List[Dict[str, Any]]
    statistics: Dict[str, Any]


def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_elements_lookup(elements_data: List[Dict]) -> Dict[str, Dict]:
    """
    Build a lookup dictionary from elements data.
    
    Handles both numeric (1.1) and string ("1.1") PI-Element values.
    Also creates entries for variant formats (2.1 and 2.1A).
    """
    lookup = {}
    
    for element in elements_data:
        # Get the element ID, handling both float and string formats
        element_id = element.get("PI-Element")
        if element_id is None:
            continue
            
        # Convert to string and normalize
        if isinstance(element_id, (int, float)):
            # Handle float formatting (1.1, 2.3, etc.)
            element_id = f"{element_id:.1f}" if element_id == int(element_id) else str(element_id)
            # Remove trailing zeros after decimal for whole numbers
            if '.' in element_id:
                element_id = element_id.rstrip('0').rstrip('.')
                # But ensure we have at least one decimal place
                if '.' not in element_id:
                    element_id += ".0"
        
        element_id = str(element_id)
        
        lookup[element_id] = {
            "PI-Element": element_id,
            "Ask/Look For": element.get("Ask/Look For", ""),
            "Calibrator notes": element.get("Calibrator notes", "")
        }
    
    return lookup


def match_slides_to_elements(
    evidence_data: Dict[str, Any],
    elements_lookup: Dict[str, Dict]
) -> MatchingResult:
    """
    Match evidence slides to PI elements.
    
    Args:
        evidence_data: Parsed evidence JSON (with 'slides' array)
        elements_lookup: Dictionary mapping element IDs to element data
        
    Returns:
        MatchingResult with matched elements and unmatched slides
    """
    slides = evidence_data.get("slides", [])
    
    # Track which elements have evidence
    element_evidence: Dict[str, List[EvidenceSlide]] = {
        elem_id: [] for elem_id in elements_lookup.keys()
    }
    
    # Track unmatched slides
    unmatched_slides = []
    
    # Track statistics
    stats = {
        "total_slides": len(slides),
        "matched_slides": 0,
        "unmatched_slides": 0,
        "section_headers": 0,
        "empty_slides": 0,
        "elements_with_evidence": 0,
        "elements_without_evidence": 0,
        "multi_element_slides": 0
    }
    
    for slide in slides:
        slide_index = slide.get("index", 0)
        text = slide.get("text", "")
        # Source tracking for multi-PPTX support
        source_file = slide.get("source_file", evidence_data.get("source_file", "unknown"))
        source_index = slide.get("source_index", slide_index)
        
        # Skip empty slides
        if not text.strip():
            stats["empty_slides"] += 1
            continue
        
        # Check if it's a section header
        if is_section_header(text):
            stats["section_headers"] += 1
            # Still process it, but mark it
            pass
        
        # Extract all element references from the slide
        all_elements = get_all_elements(text)
        primary_element = get_primary_element(text)
        
        if not all_elements:
            stats["unmatched_slides"] += 1
            unmatched_slides.append({
                "slide_index": slide_index,
                "text_preview": text[:300] + "..." if len(text) > 300 else text,
                "reason": "No element reference found"
            })
            continue
        
        # Track multi-element slides
        if len(all_elements) > 1:
            stats["multi_element_slides"] += 1
        
        stats["matched_slides"] += 1
        
        # Get the match pattern for the primary element
        matches = extract_element_references(text)
        primary_pattern = "unknown"
        for elem_id, pattern in matches:
            if elem_id == primary_element:
                primary_pattern = pattern
                break
        
        # Create evidence slide object
        evidence_slide = EvidenceSlide(
            slide_index=slide_index,
            text=text,
            text_preview=text[:200] + "..." if len(text) > 200 else text,
            match_pattern=primary_pattern,
            all_elements_in_slide=sorted(all_elements, key=element_to_float),
            is_primary_match=True,
            source_file=source_file,
            source_index=source_index
        )
        
        # Match to elements - track which target elements we've already matched
        # to avoid duplicates when both "2.1" and "2.1A" map to the same element
        matched = False
        matched_target_elements = set()
        
        for elem_id in all_elements:
            target_elem = None
            
            # Try exact match first
            if elem_id in element_evidence:
                target_elem = elem_id
            else:
                # Try to match numeric portion only (e.g., "2.1A" -> "2.1")
                base_elem = re.sub(r'[A-Za-z]+$', '', elem_id)
                if base_elem in element_evidence:
                    target_elem = base_elem
            
            # Only add if we haven't already matched this slide to this target element
            if target_elem and target_elem not in matched_target_elements:
                matched_target_elements.add(target_elem)
                is_primary = (elem_id == primary_element)
                evidence_entry = EvidenceSlide(
                    slide_index=slide_index,
                    text=text,
                    text_preview=text[:200] + "..." if len(text) > 200 else text,
                    match_pattern=primary_pattern if is_primary else "secondary_reference",
                    all_elements_in_slide=sorted(all_elements, key=element_to_float),
                    is_primary_match=is_primary,
                    source_file=source_file,
                    source_index=source_index
                )
                element_evidence[target_elem].append(evidence_entry)
                matched = True
        
        if not matched:
            # Element referenced but not in our elements list
            unmatched_slides.append({
                "slide_index": slide_index,
                "text_preview": text[:300] + "..." if len(text) > 300 else text,
                "reason": f"Element(s) {all_elements} not found in elements list"
            })
    
    # Build matched elements list
    matched_elements = []
    for elem_id, elem_data in sorted(elements_lookup.items(), key=lambda x: element_to_float(x[0])):
        evidence_list = element_evidence.get(elem_id, [])
        
        if evidence_list:
            stats["elements_with_evidence"] += 1
        else:
            stats["elements_without_evidence"] += 1
        
        matched_elem = MatchedElement(
            pi_element=elem_id,
            ask_look_for=elem_data.get("Ask/Look For", ""),
            calibrator_notes=elem_data.get("Calibrator notes", ""),
            evidence=evidence_list,
            evidence_count=len(evidence_list)
        )
        matched_elements.append(matched_elem)
    
    # Build metadata - handle both single and multi-PPTX formats
    source_files = evidence_data.get("source_files")  # Multi-PPTX format
    if not source_files:
        # Fallback to single file format
        single_source = evidence_data.get("source_file", "unknown")
        source_files = [single_source] if single_source != "unknown" else []
    
    metadata = {
        "source_evidence_files": source_files,
        "total_source_slides": evidence_data.get("total_slides", len(slides)),
        "generated_at": datetime.now().isoformat(),
        "generator": "match_evidence_to_elements.py"
    }
    
    return MatchingResult(
        metadata=metadata,
        matched_elements=matched_elements,
        unmatched_slides=unmatched_slides,
        statistics=stats
    )


def serialize_result(result: MatchingResult) -> Dict[str, Any]:
    """Convert MatchingResult to JSON-serializable dictionary."""
    return {
        "metadata": result.metadata,
        "statistics": result.statistics,
        "matched_elements": [
            {
                "PI-Element": elem.pi_element,
                "Calibrator instructions": {
                    "Ask/Look For": elem.ask_look_for,
                    "Calibrator notes": elem.calibrator_notes
                },
                "Evidence": [
                    {
                        "slide_index": ev.slide_index,
                        "source_file": ev.source_file,
                        "source_index": ev.source_index,
                        "text_preview": ev.text_preview,
                        "match_pattern": ev.match_pattern,
                        "all_elements_in_slide": ev.all_elements_in_slide,
                        "is_primary_match": ev.is_primary_match,
                        "full_text": ev.text
                    }
                    for ev in elem.evidence
                ],
                "evidence_count": elem.evidence_count
            }
            for elem in result.matched_elements
        ],
        "unmatched_slides": result.unmatched_slides
    }


def print_summary(result: MatchingResult):
    """Print a summary of the matching results."""
    stats = result.statistics
    
    print("\n" + "="*60)
    print("MATCHING SUMMARY")
    print("="*60)
    
    print(f"\nSlide Statistics:")
    print(f"  Total slides processed: {stats['total_slides']}")
    print(f"  Matched to elements:    {stats['matched_slides']}")
    print(f"  Unmatched slides:       {stats['unmatched_slides']}")
    print(f"  Section headers:        {stats['section_headers']}")
    print(f"  Empty slides:           {stats['empty_slides']}")
    print(f"  Multi-element slides:   {stats['multi_element_slides']}")
    
    print(f"\nElement Statistics:")
    print(f"  Elements with evidence:    {stats['elements_with_evidence']}")
    print(f"  Elements without evidence: {stats['elements_without_evidence']}")
    
    # Show elements without evidence
    elements_missing = [
        elem for elem in result.matched_elements 
        if elem.evidence_count == 0
    ]
    
    if elements_missing:
        print(f"\nElements without evidence ({len(elements_missing)}):")
        for elem in elements_missing[:10]:
            print(f"  - {elem.pi_element}: {elem.ask_look_for[:60]}...")
        if len(elements_missing) > 10:
            print(f"  ... and {len(elements_missing) - 10} more")
    
    # Show top elements by evidence count
    top_elements = sorted(
        result.matched_elements, 
        key=lambda x: x.evidence_count, 
        reverse=True
    )[:5]
    
    if top_elements and top_elements[0].evidence_count > 0:
        print(f"\nTop elements by evidence count:")
        for elem in top_elements:
            if elem.evidence_count > 0:
                print(f"  - {elem.pi_element}: {elem.evidence_count} slides")
    
    print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(
        description="Match evidence slides to PI calibration elements",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python match_evidence_to_elements.py source-docs/elements.json source-docs/evidence1-6_multimodal_gpt-51.json
  python match_evidence_to_elements.py source-docs/elements.json source-docs/evidence1-6_multimodal_gpt-51.json -o matched.json
        """
    )
    
    parser.add_argument(
        "elements_json",
        help="Path to the elements JSON file (PI calibration elements)"
    )
    
    parser.add_argument(
        "evidence_json",
        help="Path to the evidence JSON file (extracted slides)"
    )
    
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output file path (default: matched_<evidence_filename>.json)"
    )
    
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress summary output"
    )
    
    parser.add_argument(
        "--include-full-text",
        action="store_true",
        default=True,
        help="Include full slide text in output (default: True)"
    )
    
    args = parser.parse_args()
    
    # Validate input files
    elements_path = Path(args.elements_json)
    evidence_path = Path(args.evidence_json)
    
    if not elements_path.exists():
        print(f"Error: Elements file not found: {elements_path}")
        sys.exit(1)
    
    if not evidence_path.exists():
        print(f"Error: Evidence file not found: {evidence_path}")
        sys.exit(1)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = evidence_path.parent / f"matched_{evidence_path.stem}.json"
    
    # Load input files
    print(f"Loading elements from: {elements_path}")
    elements_data = load_json_file(elements_path)
    
    print(f"Loading evidence from: {evidence_path}")
    evidence_data = load_json_file(evidence_path)
    
    # Handle elements as either list or dict with list
    if isinstance(elements_data, list):
        elements_list = elements_data
    else:
        elements_list = elements_data.get("elements", elements_data)
    
    print(f"Found {len(elements_list)} elements")
    print(f"Found {len(evidence_data.get('slides', []))} slides")
    
    # Build lookup and perform matching
    elements_lookup = build_elements_lookup(elements_list)
    result = match_slides_to_elements(evidence_data, elements_lookup)
    
    # Serialize and save
    output_data = serialize_result(result)
    
    # Optionally remove full text to reduce file size
    if not args.include_full_text:
        for elem in output_data["matched_elements"]:
            for ev in elem["Evidence"]:
                del ev["full_text"]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nOutput written to: {output_path}")
    
    # Print summary
    if not args.quiet:
        print_summary(result)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
