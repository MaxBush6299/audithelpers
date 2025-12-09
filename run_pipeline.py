#!/usr/bin/env python3
"""
Unified Pipeline Orchestrator for PI Calibration Evidence Evaluation

This script chains all stages of the evidence evaluation pipeline:
  Stage 1: Extract PI elements from Excel
  Stage 2: Extract evidence from PPTX file(s) using multimodal LLM
  Stage 3: Match evidence slides to PI elements
  Stage 4: Evaluate evidence with LLM agent

Usage:
    python run_pipeline.py --elements-xlsx calib.xlsx --evidence-pptx evidence1.pptx evidence2.pptx

Example:
    python run_pipeline.py \
        --elements-xlsx source-docs/calib_evidence.xlsx \
        --evidence-pptx source-docs/evidence1-6.pptx source-docs/evidence7-15.pptx \
        --output-dir output/ \
        --model gpt-4.1
"""

import argparse
import io
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Fix Windows console encoding for Unicode characters
# Only apply when stdout is a real terminal (not when piped/redirected)
if sys.platform == 'win32' and sys.stdout.isatty():
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass  # Ignore if it fails

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


@dataclass
class PipelineConfig:
    """Configuration for the pipeline run."""
    elements_xlsx: str
    evidence_pptx: List[str]
    output_dir: str = "./output"
    model: str = "gpt-4.1"
    use_di: bool = True
    skip_extraction: bool = False
    skip_evaluation: bool = False
    generate_report: bool = False
    report_options: Dict[str, bool] = field(default_factory=dict)
    verbose: bool = True


@dataclass
class PipelineResult:
    """Result of a pipeline run."""
    success: bool
    elements_count: int = 0
    slides_count: int = 0
    matched_slides: int = 0
    elements_with_evidence: int = 0
    evaluation_results: Dict[str, int] = field(default_factory=dict)
    output_files: Dict[str, str] = field(default_factory=dict)
    report_path: Optional[str] = None
    error_message: Optional[str] = None
    elapsed_seconds: float = 0.0


def print_stage(stage_num: int, total: int, message: str):
    """Print a stage header."""
    print(f"\n[Stage {stage_num}/{total}] {message}")
    print("-" * 60)


def print_progress(message: str, indent: int = 2):
    """Print a progress message with indentation."""
    print(" " * indent + f"-> {message}")


def save_json(filepath: str, data: Any):
    """Save data to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(filepath: str) -> Any:
    """Load data from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_stage1_excel_extraction(config: PipelineConfig, output_dir: Path) -> Dict[str, Any]:
    """
    Stage 1: Extract PI elements from Excel file.
    
    Returns:
        Dict with 'elements' list and 'output_path'
    """
    from extractors.xlsx_extract import extract_pi_rows_xlsx
    
    if config.verbose:
        print_progress(f"Loading: {config.elements_xlsx}")
    
    elements = extract_pi_rows_xlsx(config.elements_xlsx, verbose=config.verbose)
    
    output_path = output_dir / "elements.json"
    save_json(str(output_path), elements)
    
    if config.verbose:
        print_progress(f"Extracted {len(elements)} elements")
        print_progress(f"Saved to: {output_path}")
    
    return {
        "elements": elements,
        "output_path": str(output_path)
    }


def run_stage2_pptx_extraction(config: PipelineConfig, output_dir: Path) -> Dict[str, Any]:
    """
    Stage 2: Extract evidence from PPTX files using multimodal LLM.
    
    Returns:
        Dict with 'evidence' data and 'output_path'
    """
    output_path = output_dir / "evidence.json"
    
    # Check if we should skip extraction
    if config.skip_extraction:
        if output_path.exists():
            if config.verbose:
                print_progress(f"Skipping extraction, loading existing: {output_path}")
            evidence = load_json(str(output_path))
            return {
                "evidence": evidence,
                "output_path": str(output_path)
            }
        else:
            raise FileNotFoundError(
                f"--skip-extraction specified but {output_path} does not exist"
            )
    
    from extractors.helpers.multimodal_extract import quick_extract_multi, quick_extract
    
    if config.verbose:
        print_progress(f"Processing {len(config.evidence_pptx)} PPTX file(s)...")
    
    # Use multi-file extraction
    if len(config.evidence_pptx) == 1:
        evidence = quick_extract(
            config.evidence_pptx[0],
            output_path=str(output_path),
            verbose=config.verbose,
            use_di=config.use_di,
            model=config.model
        )
    else:
        evidence = quick_extract_multi(
            config.evidence_pptx,
            output_path=str(output_path),
            verbose=config.verbose,
            use_di=config.use_di,
            model=config.model
        )
    
    total_slides = evidence.get("total_slides", len(evidence.get("slides", [])))
    
    if config.verbose:
        print_progress(f"Total: {total_slides} slides extracted")
        print_progress(f"Saved to: {output_path}")
    
    return {
        "evidence": evidence,
        "output_path": str(output_path)
    }


def run_stage3_matching(
    config: PipelineConfig, 
    output_dir: Path,
    elements: List[Dict],
    evidence: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Stage 3: Match evidence slides to PI elements.
    
    Returns:
        Dict with 'matched' data, 'statistics', and 'output_path'
    """
    from matching.match_evidence import (
        build_elements_lookup,
        match_slides_to_elements,
        serialize_result
    )
    
    if config.verbose:
        print_progress("Building elements lookup...")
    
    elements_lookup = build_elements_lookup(elements)
    
    if config.verbose:
        print_progress("Matching slides to elements...")
    
    result = match_slides_to_elements(evidence, elements_lookup)
    
    output_path = output_dir / "matched_evidence.json"
    output_data = serialize_result(result)
    save_json(str(output_path), output_data)
    
    stats = result.statistics
    
    if config.verbose:
        print_progress(f"Matched {stats['matched_slides']} slides to elements")
        print_progress(f"Elements with evidence: {stats['elements_with_evidence']}")
        print_progress(f"Elements without evidence: {stats['elements_without_evidence']}")
        print_progress(f"Saved to: {output_path}")
    
    return {
        "matched": output_data,
        "statistics": stats,
        "output_path": str(output_path)
    }


def run_stage4_evaluation(
    config: PipelineConfig,
    output_dir: Path,
    matched_evidence_path: str
) -> Dict[str, Any]:
    """
    Stage 4: Evaluate evidence with LLM agent.
    
    Returns:
        Dict with 'results', 'statistics', and output paths
    """
    if config.skip_evaluation:
        if config.verbose:
            print_progress("Skipping evaluation (--skip-evaluation specified)")
        return {
            "results": None,
            "statistics": None,
            "output_path": None,
            "progress_path": None
        }
    
    from evaluation.evaluate import evaluate_matched_evidence
    
    output_path = output_dir / "evaluation_results.json"
    progress_path = output_dir / "evaluation_progress.json"
    
    if config.verbose:
        print_progress(f"Evaluating with {config.model}...")
    
    # Run evaluation
    results = evaluate_matched_evidence(
        matched_evidence_path=matched_evidence_path,
        output_path=str(output_path),
        progress_path=str(progress_path)
    )
    
    # Load final results for statistics
    final_output = load_json(str(output_path))
    stats = final_output.get("statistics", {})
    
    if config.verbose:
        print_progress(f"Results: {stats.get('pass', 0)} Pass, {stats.get('fail', 0)} Fail, "
                      f"{stats.get('needs_more_evidence', 0)} Needs More Evidence")
        print_progress(f"Saved to: {output_path}")
    
    return {
        "results": results,
        "statistics": stats,
        "output_path": str(output_path),
        "progress_path": str(progress_path)
    }


def run_stage5_report(
    config: PipelineConfig,
    output_dir: Path,
    evaluation_path: str,
    matched_path: str
) -> Dict[str, Any]:
    """
    Stage 5: Generate Word report from evaluation results.
    
    Returns:
        Dict with 'report_path'
    """
    from reports.word_report import generate_word_report
    
    report_path = output_dir / "evaluation_report.docx"
    
    if config.verbose:
        print_progress("Generating Word report...")
    
    # Build report options
    options = {
        'include_pass': config.report_options.get('include_pass', True),
        'include_fail': config.report_options.get('include_fail', True),
        'include_needs_more': config.report_options.get('include_needs_more', True),
        'include_excerpts': config.report_options.get('include_excerpts', True),
        'include_reasoning': True,
        'include_description': True,
        'max_excerpt_length': 500,
    }
    
    # Get evidence file names for metadata
    evidence_files = [Path(p).name for p in config.evidence_pptx]
    
    # Generate report
    generate_word_report(
        evaluation_results_path=evaluation_path,
        output_path=str(report_path),
        matched_evidence_path=matched_path,
        evidence_files=evidence_files,
        options=options
    )
    
    if config.verbose:
        print_progress(f"Report saved to: {report_path}")
    
    return {
        "report_path": str(report_path)
    }


def run_pipeline(config: PipelineConfig) -> PipelineResult:
    """
    Run the complete evidence evaluation pipeline.
    
    Args:
        config: Pipeline configuration
        
    Returns:
        PipelineResult with outcomes and statistics
    """
    start_time = time.time()
    
    print("=" * 60)
    print("PI CALIBRATION EVIDENCE EVALUATION PIPELINE")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Model: {config.model}")
    print(f"Output directory: {config.output_dir}")
    
    # Create output directory
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    result = PipelineResult(success=False)
    
    # Calculate total stages based on options
    total_stages = 3  # Base: Excel, PPTX, Matching
    if not config.skip_evaluation:
        total_stages += 1  # Evaluation
    if config.generate_report and not config.skip_evaluation:
        total_stages += 1  # Report
    
    try:
        # Stage 1: Excel Extraction
        print_stage(1, total_stages, "Extracting elements from Excel")
        stage1 = run_stage1_excel_extraction(config, output_dir)
        result.elements_count = len(stage1["elements"])
        result.output_files["elements"] = stage1["output_path"]
        
        # Stage 2: PPTX Extraction
        print_stage(2, total_stages, "Extracting evidence from PPTX")
        stage2 = run_stage2_pptx_extraction(config, output_dir)
        result.slides_count = stage2["evidence"].get("total_slides", 0)
        result.output_files["evidence"] = stage2["output_path"]
        
        # Stage 3: Matching
        print_stage(3, total_stages, "Matching evidence to elements")
        stage3 = run_stage3_matching(
            config, output_dir,
            stage1["elements"],
            stage2["evidence"]
        )
        result.matched_slides = stage3["statistics"]["matched_slides"]
        result.elements_with_evidence = stage3["statistics"]["elements_with_evidence"]
        result.output_files["matched"] = stage3["output_path"]
        
        # Stage 4: Evaluation
        current_stage = 4
        if not config.skip_evaluation:
            print_stage(current_stage, total_stages, "Evaluating evidence with LLM")
            stage4 = run_stage4_evaluation(config, output_dir, stage3["output_path"])
            if stage4["statistics"]:
                result.evaluation_results = stage4["statistics"]
                result.output_files["evaluation"] = stage4["output_path"]
                result.output_files["progress"] = stage4["progress_path"]
            
            # Stage 5: Report Generation
            if config.generate_report and stage4["output_path"]:
                current_stage += 1
                print_stage(current_stage, total_stages, "Generating Word report")
                stage5 = run_stage5_report(
                    config, output_dir,
                    stage4["output_path"],
                    stage3["output_path"]
                )
                result.report_path = stage5["report_path"]
                result.output_files["report"] = stage5["report_path"]
        
        result.success = True
        
    except Exception as e:
        result.error_message = str(e)
        print(f"\n[ERROR] Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Calculate elapsed time
    result.elapsed_seconds = time.time() - start_time
    
    # Print summary
    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    
    if result.success:
        print(f"[OK] Pipeline completed successfully!")
    else:
        print(f"[ERROR] Pipeline failed: {result.error_message}")
    
    print(f"\nStatistics:")
    print(f"  Elements extracted:     {result.elements_count}")
    print(f"  Slides extracted:       {result.slides_count}")
    print(f"  Slides matched:         {result.matched_slides}")
    print(f"  Elements with evidence: {result.elements_with_evidence}")
    
    if result.evaluation_results:
        print(f"\nEvaluation Results:")
        print(f"  Pass:                 {result.evaluation_results.get('pass', 0)}")
        print(f"  Fail:                 {result.evaluation_results.get('fail', 0)}")
        print(f"  Needs More Evidence:  {result.evaluation_results.get('needs_more_evidence', 0)}")
        print(f"  Error:                {result.evaluation_results.get('error', 0)}")
    
    print(f"\nOutput Files:")
    for name, path in result.output_files.items():
        print(f"  {name}: {path}")
    
    if result.report_path:
        print(f"\nWord Report: {result.report_path}")
    
    minutes, seconds = divmod(result.elapsed_seconds, 60)
    print(f"\nTotal time: {int(minutes)}m {int(seconds)}s")
    print("=" * 60)
    
    return result


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run the complete PI calibration evidence evaluation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with single PPTX
  python run_pipeline.py --elements-xlsx calib.xlsx --evidence-pptx evidence.pptx

  # Multiple PPTX files with Word report
  python run_pipeline.py \\
      --elements-xlsx source-docs/calib_evidence.xlsx \\
      --evidence-pptx source-docs/evidence1-6.pptx source-docs/evidence7-15.pptx \\
      --output-dir output/ \\
      --report

  # Use GPT-5.1 model
  python run_pipeline.py --elements-xlsx calib.xlsx --evidence-pptx evidence.pptx --model gpt-5.1

  # Generate report without passed elements
  python run_pipeline.py --elements-xlsx calib.xlsx --evidence-pptx evidence.pptx --report --report-no-pass

  # Skip PPTX extraction (reuse existing evidence.json)
  python run_pipeline.py --elements-xlsx calib.xlsx --evidence-pptx dummy.pptx --skip-extraction

  # Stop after matching (no LLM evaluation)
  python run_pipeline.py --elements-xlsx calib.xlsx --evidence-pptx evidence.pptx --skip-evaluation

Required environment variables:
  AZURE_AI_ENDPOINT, AZURE_AI_API_KEY, GPT_4_1_DEPLOYMENT (for GPT-4.1)
  AZURE_AI_GPT5_ENDPOINT, AZURE_AI_GPT5_API_KEY, GPT_5_1_DEPLOYMENT (for GPT-5.1)
  AZURE_DI_ENDPOINT, AZURE_DI_KEY (optional, for embedded image OCR)
"""
    )
    
    parser.add_argument(
        "--elements-xlsx",
        required=True,
        help="Path to Excel file with PI elements (columns L and M)"
    )
    
    parser.add_argument(
        "--evidence-pptx",
        nargs="+",
        required=True,
        help="One or more PPTX files containing evidence slides"
    )
    
    parser.add_argument(
        "--output-dir",
        default="./output",
        help="Output directory for all generated files (default: ./output)"
    )
    
    parser.add_argument(
        "--model",
        choices=["gpt-4.1", "gpt-5.1"],
        default="gpt-4.1",
        help="LLM model to use for extraction and evaluation (default: gpt-4.1)"
    )
    
    parser.add_argument(
        "--no-di",
        action="store_true",
        help="Skip Document Intelligence OCR for embedded images"
    )
    
    parser.add_argument(
        "--skip-extraction",
        action="store_true",
        help="Skip PPTX extraction, reuse existing evidence.json in output directory"
    )
    
    parser.add_argument(
        "--skip-evaluation",
        action="store_true",
        help="Skip LLM evaluation, stop after matching stage"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate Word report (.docx) after evaluation"
    )
    
    parser.add_argument(
        "--report-no-pass",
        action="store_true",
        help="Exclude passed elements from report"
    )
    
    parser.add_argument(
        "--report-no-excerpts",
        action="store_true",
        help="Exclude evidence text excerpts from report"
    )
    
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )
    
    args = parser.parse_args()
    
    # Validate input files exist
    if not Path(args.elements_xlsx).exists():
        print(f"Error: Elements file not found: {args.elements_xlsx}")
        sys.exit(1)
    
    if not args.skip_extraction:
        for pptx_path in args.evidence_pptx:
            if not Path(pptx_path).exists():
                print(f"Error: PPTX file not found: {pptx_path}")
                sys.exit(1)
    
    # Build config
    report_options = {
        'include_pass': not args.report_no_pass,
        'include_excerpts': not args.report_no_excerpts,
    }
    
    config = PipelineConfig(
        elements_xlsx=args.elements_xlsx,
        evidence_pptx=args.evidence_pptx,
        output_dir=args.output_dir,
        model=args.model,
        use_di=not args.no_di,
        skip_extraction=args.skip_extraction,
        skip_evaluation=args.skip_evaluation,
        generate_report=args.report,
        report_options=report_options,
        verbose=not args.quiet
    )
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run pipeline
    result = run_pipeline(config)
    
    # Exit with appropriate code
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
