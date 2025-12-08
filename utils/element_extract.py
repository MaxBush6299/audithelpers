"""
Element Pattern Extraction Utilities

This module provides regex patterns and functions for extracting PI element references
from slide text content. Used by match_evidence_to_elements.py for evidence matching.
"""

import re
from typing import List, Tuple, Optional, Set

# ============================================================================
# REGEX PATTERNS FOR PI ELEMENT EXTRACTION
# ============================================================================

# Primary patterns for element references in slides
ELEMENT_PATTERNS = [
    # Pattern 1: "X.Y >" or "X.Y>" format (most common in slides)
    # Examples: "1.1 >", "2.3 >", "6.17 >"
    (r'(\d+\.\d+[A-Za-z]?)\s*>', 'arrow_format'),
    
    # Pattern 2: "NEXT X.Y >" format for new/updated elements  
    # Examples: "NEXT 4.6 >", "NEXT 6.17 >"
    (r'NEXT\s+(\d+\.\d+[A-Za-z]?)\s*>', 'next_arrow_format'),
    
    # Pattern 3: "PI-X" or "PI X" header format
    # Examples: "PI 1", "PI-2", "PI 6"
    (r'PI[\s-]?(\d+)', 'pi_header'),
    
    # Pattern 4: Element in parentheses "(X.Y)"
    # Examples: "(4.1)", "(6.12)"
    (r'\((\d+\.\d+[A-Za-z]?)\)', 'parentheses_format'),
    
    # Pattern 5: "Element X.Y" explicit format
    (r'[Ee]lement\s+(\d+\.\d+[A-Za-z]?)', 'element_explicit'),
    
    # Pattern 6: Slide titles like "PI 6 – Training (6.1)"
    (r'PI\s+\d+\s*[–-]\s*\w+.*?\((\d+\.\d+[A-Za-z]?)\)', 'slide_title_format'),
]

# Compiled patterns for efficiency
COMPILED_PATTERNS = [(re.compile(pattern, re.IGNORECASE), name) for pattern, name in ELEMENT_PATTERNS]


def extract_element_references(text: str) -> List[Tuple[str, str]]:
    """
    Extract all PI element references from slide text.
    
    Args:
        text: The slide text content
        
    Returns:
        List of tuples (element_id, pattern_name) for each match found
    """
    matches = []
    
    for pattern, pattern_name in COMPILED_PATTERNS:
        for match in pattern.finditer(text):
            element_id = match.group(1)
            # Normalize element ID (remove trailing letters if they're lowercase)
            normalized = normalize_element_id(element_id)
            matches.append((normalized, pattern_name))
    
    return matches


def normalize_element_id(element_id: str) -> str:
    """
    Normalize element ID to standard format.
    
    Examples:
        "1.1" -> "1.1"
        "2.3" -> "2.3"
        "6.17" -> "6.17"
        "2.1A" -> "2.1A" (keep uppercase letters)
    """
    # Handle cases like "6.1" vs "6.10" - keep as-is
    # Remove any trailing whitespace
    element_id = element_id.strip()
    
    # Convert any lowercase suffix letters to uppercase
    if element_id and element_id[-1].isalpha():
        element_id = element_id[:-1] + element_id[-1].upper()
    
    return element_id


def get_primary_element(text: str) -> Optional[str]:
    """
    Get the primary (most prominent) element reference from slide text.
    
    Priority order:
    1. "X.Y >" format (explicit ask/look for reference)
    2. NEXT format
    3. Slide title format
    4. Other formats
    
    Args:
        text: The slide text content
        
    Returns:
        Primary element ID or None if no element found
    """
    matches = extract_element_references(text)
    
    if not matches:
        return None
    
    # Priority order for pattern types
    priority = ['arrow_format', 'next_arrow_format', 'slide_title_format', 
                'element_explicit', 'parentheses_format', 'pi_header']
    
    for pattern_type in priority:
        for element_id, match_type in matches:
            if match_type == pattern_type:
                return element_id
    
    # Return first match if no priority match found
    return matches[0][0] if matches else None


def get_all_elements(text: str) -> Set[str]:
    """
    Get all unique element IDs referenced in the text.
    
    Args:
        text: The slide text content
        
    Returns:
        Set of unique element IDs
    """
    matches = extract_element_references(text)
    return {element_id for element_id, _ in matches}


def element_to_float(element_id: str) -> float:
    """
    Convert element ID to float for comparison/sorting.
    
    Examples:
        "1.1" -> 1.1
        "2.3" -> 2.3
        "6.17" -> 6.17
        "2.1A" -> 2.1 (letter suffix ignored for numeric comparison)
    """
    # Remove any letter suffixes
    numeric_part = re.sub(r'[A-Za-z]+$', '', element_id)
    try:
        return float(numeric_part)
    except ValueError:
        return 0.0


def is_section_header(text: str) -> bool:
    """
    Check if slide text appears to be a section header (title slide).
    
    Section headers typically contain minimal text like:
    "PI 1 – Purpose & Values, Plant Mission"
    "PI 6- Training"
    """
    # Check for short text that's primarily a header
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    
    if len(lines) <= 3:
        # Check if it matches header patterns
        header_pattern = re.compile(r'^PI\s*\d+\s*[–-]', re.IGNORECASE)
        for line in lines:
            if header_pattern.match(line):
                # Check if there's no "Ask/Look for" content
                if 'ask/look for' not in text.lower() and '>' not in text:
                    return True
    
    return False


# For testing the module directly
if __name__ == "__main__":
    test_cases = [
        "PI 1 – Purpose & Values, Plant Mission",
        "1.1 > Ask senior plant leadership how the Plant Mission Statement was developed.",
        "NEXT 6.17 > Plant should evaluate key training courses",
        "PI-2 Workplace Safety System\n2.3 > Ask for evidence",
        "PI 6 – Training (6.1)\n6.1 > Review the Training Plan",
        "Ask/Look for:\n2.1A > Ask for examples of GCTA",
    ]
    
    for test in test_cases:
        print(f"\nText: {test[:60]}...")
        print(f"  Primary element: {get_primary_element(test)}")
        print(f"  All elements: {get_all_elements(test)}")
        print(f"  Is header: {is_section_header(test)}")
