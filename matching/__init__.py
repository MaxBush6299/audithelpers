"""
Matching module - matches evidence slides to PI calibration elements.
"""

from .match_evidence import (
    build_elements_lookup,
    match_slides_to_elements,
    serialize_result,
    EvidenceSlide,
    MatchedElement,
    MatchingResult,
)

__all__ = [
    "build_elements_lookup",
    "match_slides_to_elements",
    "serialize_result",
    "EvidenceSlide",
    "MatchedElement",
    "MatchingResult",
]
