"""
Streamlit Web UI for PI Calibration Evidence Evaluation Pipeline.

Single-page application with:
- File upload (Excel elements + PPTX evidence)
- Model selection
- Element filtering (optional)
- Pipeline execution with live progress
- Results display with expandable details
- Word report download

Usage:
    streamlit run streamlit_app.py
"""

import streamlit as st
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Page config must be first Streamlit command
st.set_page_config(
    page_title="PI Calibration Evidence Evaluator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #0066cc;
    }
    .status-pass { color: #28a745; font-weight: bold; }
    .status-fail { color: #dc3545; font-weight: bold; }
    .status-needs { color: #fd7e14; font-weight: bold; }
    .stage-complete { color: #28a745; }
    .stage-active { color: #0066cc; }
    .stage-pending { color: #6c757d; }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        'pipeline_status': 'idle',  # idle, running, completed, error
        'current_stage': 0,
        'progress_percent': 0,
        'current_element': '',
        'results': None,
        'evaluation_stats': None,
        'activity_log': [],
        'output_dir': None,
        'error_message': None,
        'elements_data': None,
        'selected_elements': [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def save_uploaded_file(uploaded_file, temp_dir: str) -> str:
    """Save uploaded file to temp directory and return path."""
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def load_elements_from_excel(excel_path: str) -> List[Dict]:
    """Load elements from Excel file for filtering UI."""
    try:
        from extractors.xlsx_extract import extract_pi_rows_xlsx
        return extract_pi_rows_xlsx(excel_path, verbose=False)
    except Exception as e:
        st.error(f"Error loading elements: {e}")
        return []


def run_pipeline_thread(
    elements_xlsx: str,
    evidence_pptx: List[str],
    output_dir: str,
    model: str,
    selected_elements: List[str]
):
    """Run pipeline in background thread (kept for reference but not used)."""
    pass  # Using subprocess approach instead


def run_pipeline_subprocess(
    elements_xlsx: str,
    evidence_pptx: List[str],
    output_dir: str,
    model: str
) -> subprocess.Popen:
    """Start pipeline as subprocess and return process handle."""
    cmd = [
        sys.executable, '-u',  # Unbuffered output
        'run_pipeline.py',
        '--elements-xlsx', elements_xlsx,
        '--evidence-pptx', *evidence_pptx,
        '--output-dir', output_dir,
        '--model', model,
        '--report'
    ]
    
    # Set environment for unbuffered output
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    
    # Log file path
    log_path = os.path.join(output_dir, 'pipeline.log')
    
    # Start subprocess with pipe
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=str(Path(__file__).parent),
        env=env,
        bufsize=1,  # Line buffered
        universal_newlines=True  # Text mode
    )
    
    # Thread to read output and write to log file
    import threading
    
    def stream_output():
        with open(log_path, 'w', encoding='utf-8') as log_file:
            for line in process.stdout:
                log_file.write(line)
                log_file.flush()
    
    thread = threading.Thread(target=stream_output, daemon=True)
    thread.start()
    process._log_thread = thread
    
    return process


def render_stage_progress():
    """Render pipeline stage indicators."""
    stages = ['Excel', 'PPTX', 'Matching', 'Evaluation', 'Report']
    current = st.session_state.current_stage
    
    cols = st.columns(len(stages))
    for i, (col, stage) in enumerate(zip(cols, stages)):
        stage_num = i + 1
        with col:
            if stage_num < current:
                st.markdown(f"✅ **{stage}**")
            elif stage_num == current:
                st.markdown(f"🔄 **{stage}**")
            else:
                st.markdown(f"⬜ {stage}")


def render_results_table():
    """Render results as an interactive table."""
    if not st.session_state.results:
        return
    
    results = st.session_state.results.get('results', [])
    if not results:
        st.info("No evaluation results available.")
        return
    
    # Build dataframe
    data = []
    for r in results:
        status = r.get('Status', 'Unknown')
        
        # Status icon
        if status.lower() == 'pass':
            status_display = '✅ Pass'
        elif status.lower() == 'fail':
            status_display = '❌ Fail'
        elif 'needs' in status.lower():
            status_display = '⚠️ Needs More'
        else:
            status_display = f'❓ {status}'
        
        slides = r.get('Evidence Slide num', [])
        slides_str = ', '.join(str(s) for s in slides) if slides else '-'
        
        reasoning = r.get('LLM response', '')
        summary = reasoning[:100] + '...' if len(reasoning) > 100 else reasoning
        
        data.append({
            'Element': r.get('PI-Element', '?'),
            'Status': status_display,
            'Slides': slides_str,
            'Summary': summary,
            '_full_reasoning': reasoning,
        })
    
    df = pd.DataFrame(data)
    
    # Display table
    st.dataframe(
        df[['Element', 'Status', 'Slides', 'Summary']],
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Expandable details
    with st.expander("🔍 View Full Evaluation Details"):
        for r in results:
            elem_id = r.get('PI-Element', '?')
            status = r.get('Status', 'Unknown')
            reasoning = r.get('LLM response', '')
            slides = r.get('Evidence Slide num', [])
            
            st.markdown(f"### Element {elem_id}")
            st.markdown(f"**Status:** {status}")
            st.markdown(f"**Slides:** {', '.join(str(s) for s in slides) if slides else 'None'}")
            st.markdown(f"**Reasoning:** {reasoning}")
            st.markdown("---")


def render_download_section():
    """Render report download buttons."""
    if st.session_state.pipeline_status != 'completed':
        return
    
    output_files = getattr(st.session_state, 'output_files', {})
    
    col1, col2 = st.columns(2)
    
    # Word Report
    with col1:
        report_path = output_files.get('report')
        if report_path and os.path.exists(report_path):
            with open(report_path, 'rb') as f:
                st.download_button(
                    label="📥 Download Word Report",
                    data=f.read(),
                    file_name=f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
        else:
            st.info("Word report not available")
    
    # JSON Results
    with col2:
        eval_path = output_files.get('evaluation')
        if eval_path and os.path.exists(eval_path):
            with open(eval_path, 'r') as f:
                st.download_button(
                    label="📥 Download JSON Results",
                    data=f.read(),
                    file_name=f"evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json",
                    use_container_width=True
                )
        else:
            st.info("JSON results not available")


def poll_progress(output_dir: str) -> dict:
    """Poll progress file and return progress data."""
    progress_path = os.path.join(output_dir, 'evaluation_progress.json')
    
    if os.path.exists(progress_path):
        try:
            with open(progress_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    return {'total': 0, 'completed': 0, 'current_element': ''}


def poll_extraction_progress(output_dir: str) -> dict:
    """Poll pipeline log for PPTX extraction progress."""
    log_path = os.path.join(output_dir, 'pipeline.log')
    
    if not os.path.exists(log_path):
        return {'current_slide': 0, 'total_slides': 0, 'stage': 'starting'}
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Check for total slides
        import re
        total_match = re.search(r'\[Pipeline\] Found (\d+) slides', content)
        total_slides = int(total_match.group(1)) if total_match else 0
        
        # Find last "Processing slide X/Y" line
        slide_matches = re.findall(r'\[Pipeline\] Processing slide (\d+)/(\d+)', content)
        if slide_matches:
            current_slide = int(slide_matches[-1][0])
            return {'current_slide': current_slide, 'total_slides': total_slides, 'stage': 'extracting'}
        
        # Check if rendering
        if '[Pipeline] Rendering slides' in content:
            return {'current_slide': 0, 'total_slides': total_slides, 'stage': 'rendering'}
        
        # Check if found slides
        if total_slides > 0:
            return {'current_slide': 0, 'total_slides': total_slides, 'stage': 'opening'}
            
    except Exception:
        pass
    
    return {'current_slide': 0, 'total_slides': 0, 'stage': 'starting'}


def check_pipeline_complete(output_dir: str) -> tuple[bool, dict]:
    """Check if pipeline completed by looking for output files."""
    eval_path = os.path.join(output_dir, 'evaluation_results.json')
    report_path = os.path.join(output_dir, 'evaluation_report.docx')
    
    if os.path.exists(eval_path):
        try:
            with open(eval_path, 'r') as f:
                results = json.load(f)
            
            output_files = {
                'evaluation': eval_path,
                'matched': os.path.join(output_dir, 'matched_evidence.json'),
                'elements': os.path.join(output_dir, 'elements.json'),
                'evidence': os.path.join(output_dir, 'evidence.json'),
            }
            
            if os.path.exists(report_path):
                output_files['report'] = report_path
            
            return True, {
                'results': results,
                'stats': results.get('statistics', {}),
                'output_files': output_files
            }
        except:
            pass
    
    return False, {}


def main():
    """Main Streamlit app."""
    init_session_state()
    
    # Header
    st.title("📊 PI Calibration Evidence Evaluator")
    st.markdown("Upload your evidence files and run the evaluation pipeline.")
    
    # ===================
    # CONFIGURATION SECTION
    # ===================
    with st.container():
        st.subheader("📁 Configuration")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # File uploads
            st.markdown("**Upload Files**")
            
            excel_file = st.file_uploader(
                "Elements Excel File (.xlsx)",
                type=['xlsx'],
                help="Excel file with PI elements (columns L and M)",
                key="excel_upload"
            )
            
            pptx_files = st.file_uploader(
                "Evidence PPTX Files",
                type=['pptx'],
                accept_multiple_files=True,
                help="One or more PowerPoint files with evidence slides",
                key="pptx_upload"
            )
        
        with col2:
            # Settings
            st.markdown("**Settings**")
            
            model = st.selectbox(
                "LLM Model",
                options=['gpt-4.1', 'gpt-5.1'],
                index=0,
                help="Select the model for extraction and evaluation"
            )
            
            # Show file status
            if excel_file:
                st.success(f"✅ {excel_file.name}")
            else:
                st.warning("⚠️ No Excel file")
            
            if pptx_files:
                st.success(f"✅ {len(pptx_files)} PPTX file(s)")
                for f in pptx_files:
                    st.caption(f"  • {f.name}")
            else:
                st.warning("⚠️ No PPTX files")
    
    st.markdown("---")
    
    # ===================
    # RUN BUTTON & EXECUTION
    # ===================
    run_disabled = not (excel_file and pptx_files)
    
    if st.button(
        "▶️ Run Full Pipeline",
        disabled=run_disabled,
        use_container_width=True,
        type="primary"
    ):
        # Create temp directory for files
        temp_dir = tempfile.mkdtemp(prefix="calibration_")
        
        # Save uploaded files
        excel_path = save_uploaded_file(excel_file, temp_dir)
        pptx_paths = [save_uploaded_file(f, temp_dir) for f in pptx_files]
        
        # Run pipeline with live progress display
        with st.status("Running pipeline...", expanded=True) as status:
            
            # Stage 1: Excel
            st.write("📋 Stage 1: Extracting elements from Excel...")
            stage1_placeholder = st.empty()
            
            # Stage 2: PPTX
            st.write("📸 Stage 2: Extracting evidence from PPTX...")
            stage2_placeholder = st.empty()
            stage2_progress = st.progress(0)
            stage2_status = st.empty()
            
            # Stage 3: Matching
            st.write("🔗 Stage 3: Matching evidence to elements...")
            stage3_placeholder = st.empty()
            
            # Stage 4: Evaluation
            st.write("🤖 Stage 4: Evaluating with LLM...")
            eval_progress = st.progress(0)
            eval_status = st.empty()
            
            # Stage 5: Report
            st.write("📄 Stage 5: Generating report...")
            stage5_placeholder = st.empty()
            
            # Live log viewer
            with st.expander("📜 Live Pipeline Log", expanded=True):
                log_container = st.empty()
            
            # Start subprocess
            process = run_pipeline_subprocess(excel_path, pptx_paths, temp_dir, model)
            
            # Monitor progress while subprocess runs
            start_time = time.time()
            last_progress = 0
            stage2_done = False
            last_log_size = 0
            
            while process.poll() is None:
                elapsed = time.time() - start_time
                
                # Update live log viewer
                log_path = os.path.join(temp_dir, 'pipeline.log')
                if os.path.exists(log_path):
                    try:
                        current_size = os.path.getsize(log_path)
                        if current_size > last_log_size:
                            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                                log_content = f.read()
                            # Show last 50 lines
                            lines = log_content.strip().split('\n')
                            display_lines = lines[-50:] if len(lines) > 50 else lines
                            log_container.code('\n'.join(display_lines), language='text')
                            last_log_size = current_size
                    except Exception:
                        pass
                
                # Check Stage 2 (PPTX extraction) progress from log
                if not stage2_done:
                    ext_progress = poll_extraction_progress(temp_dir)
                    total_slides = ext_progress.get('total_slides', 0)
                    current_slide = ext_progress.get('current_slide', 0)
                    stage = ext_progress.get('stage', 'starting')
                    
                    if stage == 'rendering':
                        stage2_status.text(f"Rendering {total_slides} slides to images...")
                    elif stage == 'extracting' and total_slides > 0:
                        pct = current_slide / total_slides
                        stage2_progress.progress(pct)
                        stage2_status.text(f"Extracting slide {current_slide}/{total_slides} (this may take several minutes)...")
                    elif stage == 'opening' and total_slides > 0:
                        stage2_status.text(f"Opening PPTX ({total_slides} slides)...")
                
                # Check for evaluation progress
                progress_data = poll_progress(temp_dir)
                total = progress_data.get('total', 0)
                completed = progress_data.get('completed', 0)
                current = progress_data.get('current_element', '')
                
                if total > 0:
                    pct = completed / total
                    eval_progress.progress(pct)
                    eval_status.text(f"Evaluating element {current}... ({completed}/{total})")
                    last_progress = pct
                
                # Check stage files to update indicators
                if os.path.exists(os.path.join(temp_dir, 'elements.json')):
                    stage1_placeholder.success("✅ Elements extracted")
                
                if os.path.exists(os.path.join(temp_dir, 'evidence.json')):
                    if not stage2_done:
                        stage2_progress.progress(1.0)
                        stage2_status.empty()
                        stage2_done = True
                    stage2_placeholder.success("✅ Evidence extracted")
                
                if os.path.exists(os.path.join(temp_dir, 'matched_evidence.json')):
                    stage3_placeholder.success("✅ Evidence matched")
                
                time.sleep(0.5)
            
            # Wait for log thread to finish
            if hasattr(process, '_log_thread'):
                process._log_thread.join(timeout=2)
            
            # Show final log
            log_path = os.path.join(temp_dir, 'pipeline.log')
            if os.path.exists(log_path):
                try:
                    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                        log_content = f.read()
                    lines = log_content.strip().split('\n')
                    display_lines = lines[-50:] if len(lines) > 50 else lines
                    log_container.code('\n'.join(display_lines), language='text')
                except Exception:
                    pass
            
            # Process finished - check result
            return_code = process.returncode
            
            if return_code == 0:
                eval_progress.progress(1.0)
                eval_status.success("✅ Evaluation complete")
                
                if os.path.exists(os.path.join(temp_dir, 'evaluation_report.docx')):
                    stage5_placeholder.success("✅ Report generated")
                
                status.update(label="✅ Pipeline completed!", state="complete", expanded=False)
                
                # Load results
                completed, data = check_pipeline_complete(temp_dir)
                if completed:
                    st.session_state.pipeline_status = 'completed'
                    st.session_state.results = data['results']
                    st.session_state.evaluation_stats = data['stats']
                    st.session_state.output_files = data['output_files']
                    st.session_state.output_dir = temp_dir
            else:
                status.update(label="❌ Pipeline failed", state="error", expanded=True)
                st.session_state.pipeline_status = 'error'
                
                # Try to get error from log file
                log_path = os.path.join(temp_dir, 'pipeline.log')
                error_msg = "Unknown error"
                if os.path.exists(log_path):
                    try:
                        with open(log_path, 'r', encoding='utf-8') as f:
                            error_msg = f.read()[-2000:]  # Last 2000 chars
                    except Exception:
                        pass
                st.session_state.error_message = error_msg
        
        st.rerun()
    
    # ===================
    # ERROR DISPLAY
    # ===================
    if st.session_state.pipeline_status == 'error':
        st.error(f"❌ Pipeline failed: {st.session_state.error_message}")
        
        if st.button("🔄 Reset"):
            st.session_state.pipeline_status = 'idle'
            st.session_state.error_message = None
            st.rerun()
    
    # ===================
    # RESULTS SECTION
    # ===================
    if st.session_state.pipeline_status == 'completed':
        st.success("✅ Pipeline completed successfully!")
        
        # Summary metrics
        st.subheader("📈 Evaluation Summary")
        
        stats = st.session_state.evaluation_stats or {}
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total", stats.get('total', 0))
        with col2:
            st.metric("✅ Pass", stats.get('pass', 0))
        with col3:
            st.metric("⚠️ Needs More", stats.get('needs_more_evidence', 0))
        with col4:
            st.metric("❌ Fail", stats.get('fail', 0))
        
        st.markdown("---")
        
        # Results table
        st.subheader("📋 Evaluation Results")
        render_results_table()
        
        st.markdown("---")
        
        # Download section
        st.subheader("📥 Download Reports")
        render_download_section()


if __name__ == "__main__":
    main()
