#!/usr/bin/env python3
"""
Evidence Evaluation CLI

This utility evaluates matched evidence against PI calibration elements using an LLM agent.
It processes elements one-at-a-time and writes incremental progress to a JSON file
for real-time monitoring (e.g., by a Streamlit frontend).

Usage:
    python -m evaluation.evaluate <matched_evidence_json> [-o output_file] [-p progress_file]

Example:
    python -m evaluation.evaluate source-docs/matched_evidence.json -o source-docs/evaluation_results.json
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.evidence_evaluator import EvidenceEvaluationAgent, EvaluationResult, EvaluationStatus


def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(filepath: str, data: Any) -> None:
    """Save data to a JSON file with pretty formatting."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_progress(
    filepath: str,
    status: str,
    completed: int,
    total: int,
    current_element: Optional[str],
    latest_result: Optional[Dict[str, Any]],
    all_results: List[Dict[str, Any]],
    start_time: datetime
) -> None:
    """Write progress to the progress file for real-time monitoring."""
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Calculate estimated time remaining
    if completed > 0:
        avg_time_per_element = elapsed / completed
        remaining = total - completed
        eta_seconds = avg_time_per_element * remaining
    else:
        eta_seconds = None
    
    progress_data = {
        "status": status,
        "completed": completed,
        "total": total,
        "current_element": current_element,
        "latest_result": latest_result,
        "elapsed_seconds": round(elapsed, 1),
        "eta_seconds": round(eta_seconds, 1) if eta_seconds is not None else None,
        "timestamp": datetime.now().isoformat(),
        "all_results": all_results
    }
    
    save_json_file(filepath, progress_data)


def evaluate_matched_evidence(
    matched_evidence_path: str,
    output_path: str,
    progress_path: str
) -> List[Dict[str, Any]]:
    """
    Evaluate all matched evidence and return results.
    
    Args:
        matched_evidence_path: Path to the matched_evidence.json file
        output_path: Path to write final evaluation_results.json
        progress_path: Path to write incremental progress updates
        
    Returns:
        List of evaluation result dictionaries
    """
    # Load matched evidence
    print(f"Loading matched evidence from: {matched_evidence_path}")
    matched_data = load_json_file(matched_evidence_path)
    
    matched_elements = matched_data.get("matched_elements", [])
    total_elements = len(matched_elements)
    
    print(f"Found {total_elements} elements to evaluate")
    
    # Initialize the evaluation agent
    print("Initializing evaluation agent...")
    agent = EvidenceEvaluationAgent()
    
    # Track results and timing
    all_results: List[Dict[str, Any]] = []
    start_time = datetime.now()
    
    # Write initial progress
    write_progress(
        filepath=progress_path,
        status="in_progress",
        completed=0,
        total=total_elements,
        current_element=None,
        latest_result=None,
        all_results=[],
        start_time=start_time
    )
    
    # Process each element one at a time
    for idx, element in enumerate(matched_elements):
        pi_element = element.get("PI-Element", "Unknown")
        evidence_count = element.get("evidence_count", 0)
        evidence = element.get("Evidence", [])
        
        # Get calibrator instructions
        calibrator_instructions = element.get("Calibrator instructions", {})
        ask_look_for = calibrator_instructions.get("Ask/Look For", "")
        calibrator_notes = calibrator_instructions.get("Calibrator notes", "")
        
        print(f"\n[{idx + 1}/{total_elements}] Evaluating element {pi_element} ({evidence_count} evidence slides)...")
        
        # Evaluate the element
        result = agent.evaluate_element(
            pi_element=pi_element,
            ask_look_for=ask_look_for,
            calibrator_notes=calibrator_notes,
            evidence=evidence
        )
        
        # Convert to dict and store
        result_dict = result.to_dict()
        all_results.append(result_dict)
        
        # Print status
        status_symbol = {
            EvaluationStatus.PASS: "✓",
            EvaluationStatus.FAIL: "✗",
            EvaluationStatus.NEEDS_MORE_EVIDENCE: "?",
            EvaluationStatus.ERROR: "!"
        }.get(result.status, "?")
        
        print(f"  {status_symbol} {result.status.value}: {result.llm_response[:100]}...")
        
        # Write progress update
        write_progress(
            filepath=progress_path,
            status="in_progress",
            completed=idx + 1,
            total=total_elements,
            current_element=pi_element,
            latest_result=result_dict,
            all_results=all_results,
            start_time=start_time
        )
    
    # Write final progress
    write_progress(
        filepath=progress_path,
        status="completed",
        completed=total_elements,
        total=total_elements,
        current_element=None,
        latest_result=all_results[-1] if all_results else None,
        all_results=all_results,
        start_time=start_time
    )
    
    # Write final results
    print(f"\nWriting results to: {output_path}")
    
    # Build final output with metadata
    final_output = {
        "metadata": {
            "source_file": matched_evidence_path,
            "evaluation_timestamp": datetime.now().isoformat(),
            "total_elements": total_elements,
            "model": agent.deployment
        },
        "statistics": {
            "total": total_elements,
            "pass": sum(1 for r in all_results if r["Status"] == "Pass"),
            "fail": sum(1 for r in all_results if r["Status"] == "Fail"),
            "needs_more_evidence": sum(1 for r in all_results if r["Status"] == "Needs More Evidence"),
            "error": sum(1 for r in all_results if r["Status"] == "Error")
        },
        "results": all_results
    }
    
    save_json_file(output_path, final_output)
    
    # Print summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total elements:        {final_output['statistics']['total']}")
    print(f"  Pass:                {final_output['statistics']['pass']}")
    print(f"  Fail:                {final_output['statistics']['fail']}")
    print(f"  Needs More Evidence: {final_output['statistics']['needs_more_evidence']}")
    print(f"  Error:               {final_output['statistics']['error']}")
    print("=" * 60)
    
    return all_results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate matched evidence against PI calibration elements using LLM"
    )
    parser.add_argument(
        "matched_evidence",
        help="Path to matched_evidence.json file"
    )
    parser.add_argument(
        "-o", "--output",
        default="source-docs/evaluation_results.json",
        help="Output path for evaluation results (default: source-docs/evaluation_results.json)"
    )
    parser.add_argument(
        "-p", "--progress",
        default="source-docs/evaluation_progress.json",
        help="Progress file path for real-time monitoring (default: source-docs/evaluation_progress.json)"
    )
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not Path(args.matched_evidence).exists():
        print(f"Error: Input file not found: {args.matched_evidence}")
        sys.exit(1)
    
    # Ensure output directory exists
    output_dir = Path(args.output).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    progress_dir = Path(args.progress).parent
    progress_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        evaluate_matched_evidence(
            matched_evidence_path=args.matched_evidence,
            output_path=args.output,
            progress_path=args.progress
        )
        print(f"\nEvaluation complete. Results written to: {args.output}")
        print(f"Progress file: {args.progress}")
    except Exception as e:
        print(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
