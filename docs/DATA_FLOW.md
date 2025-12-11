# Data Flow: Frontend to Backend

This document explains how files flow through the Streamlit UI and pipeline execution.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BROWSER (Frontend)                          │
│  ┌──────────────┐                                                   │
│  │ File Upload  │ → UploadedFile objects (in-memory)                │
│  └──────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ save_uploaded_file()
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    TEMP DIRECTORY (Disk)                            │
│  C:\Users\...\AppData\Local\Temp\audit_abc123\                      │
│  ├── calib_evidence.xlsx     ← Written from upload                  │
│  ├── evidence1-6.pptx        ← Written from upload                  │
│  ├── elements.json           ← Written by Stage 1                   │
│  ├── evidence.json           ← Written by Stage 2                   │
│  ├── matched_evidence.json   ← Written by Stage 3                   │
│  ├── evaluation_progress.json← Written/Updated by Stage 4           │
│  ├── evaluation_results.json ← Written by Stage 4                   │
│  └── evaluation_report.docx  ← Written by Stage 5                   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ subprocess.Popen()
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SUBPROCESS (run_pipeline.py)                     │
│  - Reads uploaded files from temp dir                               │
│  - Writes output JSON/DOCX files to temp dir                        │
│  - Updates evaluation_progress.json in real-time                    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ poll_progress() reads progress
                              │ check_pipeline_complete() reads results
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         BROWSER (Frontend)                          │
│  - Displays progress from JSON                                      │
│  - Shows results table from evaluation_results.json                 │
│  - Download buttons read files from temp dir                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Walkthrough

### Step 1: User Uploads Files in Browser

When a user selects files using the Streamlit file uploaders, the files exist **only in browser memory** as `UploadedFile` objects - they are not yet on disk.

```python
excel_file = st.file_uploader("Elements Excel File", type=['xlsx'])
pptx_files = st.file_uploader("Evidence PPTX Files", type=['pptx'], accept_multiple_files=True)
```

---

### Step 2: User Clicks "Run Pipeline" Button

A temporary directory is created to store all files for this pipeline run:

```python
temp_dir = tempfile.mkdtemp(prefix="audit_")
# Creates: C:\Users\...\AppData\Local\Temp\audit_abc123\
```

---

### Step 3: Save Uploaded Files to Temp Directory

The uploaded files are written from browser memory to the temp directory:

```python
excel_path = save_uploaded_file(excel_file, temp_dir)
pptx_paths = [save_uploaded_file(f, temp_dir) for f in pptx_files]

def save_uploaded_file(uploaded_file, temp_dir: str) -> str:
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())  # Write bytes to disk
    return file_path
```

**After Step 3, files on disk:**
```
C:\Users\...\AppData\Local\Temp\audit_abc123\
├── calib_evidence.xlsx        ← Saved from browser upload
├── evidence1-6.pptx           ← Saved from browser upload
└── evidence7-15.pptx          ← Saved from browser upload (if multiple)
```

---

### Step 4: Launch Pipeline Subprocess

The pipeline is executed as a separate Python process:

```python
process = run_pipeline_subprocess(excel_path, pptx_paths, temp_dir, model)

def run_pipeline_subprocess(...) -> subprocess.Popen:
    cmd = [
        sys.executable, 'run_pipeline.py',
        '--elements-xlsx', elements_xlsx,    # Full path to temp file
        '--evidence-pptx', *evidence_pptx,   # Full paths to temp files
        '--output-dir', output_dir,          # Temp directory
        '--model', model,
        '--report'
    ]
    process = subprocess.Popen(cmd, ...)
    return process
```

**Actual command executed:**
```bash
python run_pipeline.py \
  --elements-xlsx "C:\...\Temp\audit_abc123\audit_evidence.xlsx" \
  --evidence-pptx "C:\...\Temp\audit_abc123\evidence1-6.pptx" \
  --output-dir "C:\...\Temp\audit_abc123" \
  --model gpt-4.1 \
  --report
```

---

### Step 5: Pipeline Reads Files & Writes Outputs

The `run_pipeline.py` processes files and creates outputs in the same temp directory:

| File | Type | Created By | Description |
|------|------|------------|-------------|
| `audit_evidence.xlsx` | INPUT | User upload | Audit elements spreadsheet |
| `evidence1-6.pptx` | INPUT | User upload | Evidence slides |
| `elements.json` | OUTPUT | Stage 1 | Extracted audit elements |
| `evidence.json` | OUTPUT | Stage 2 | Extracted slide text (multimodal) |
| `matched_evidence.json` | OUTPUT | Stage 3 | Elements matched to slides |
| `evaluation_progress.json` | OUTPUT | Stage 4 | Live progress updates |
| `evaluation_results.json` | OUTPUT | Stage 4 | Final evaluation verdicts |
| `evaluation_report.docx` | OUTPUT | Stage 5 | Word report document |

---

### Step 6: Streamlit Polls Progress File

While the subprocess runs, Streamlit continuously reads the progress file to update the UI:

```python
while process.poll() is None:
    progress_data = poll_progress(temp_dir)  # Reads evaluation_progress.json
    # Update progress bar and status text...
    time.sleep(0.5)

def poll_progress(output_dir: str) -> dict:
    progress_path = os.path.join(output_dir, 'evaluation_progress.json')
    if os.path.exists(progress_path):
        with open(progress_path, 'r') as f:
            return json.load(f)
    return {}
```

**Progress file format (`evaluation_progress.json`):**
```json
{
  "total": 54,
  "completed": 23,
  "current_element": "3.2",
  "status": "evaluating"
}
```

---

### Step 7: Load Results for Display

After the pipeline completes successfully:

```python
completed, data = check_pipeline_complete(temp_dir)
if completed:
    st.session_state.results = data['results']
    st.session_state.output_files = data['output_files']
```

---

### Step 8: Download Buttons Read from Temp Directory

When the user clicks a download button, the file is read from the temp directory:

```python
report_path = output_files.get('report')  # Path in temp dir
if report_path and os.path.exists(report_path):
    with open(report_path, 'rb') as f:
        st.download_button(
            data=f.read(),  # Read bytes from temp file
            file_name="evaluation_report.docx",
            ...
        )
```

---

## File Lifecycle

```
Upload        →  Temp Storage  →  Processing  →  Download  →  Cleanup
(browser)        (disk)           (pipeline)      (user)       (system)

┌─────────┐    ┌──────────┐    ┌───────────┐   ┌─────────┐   ┌─────────┐
│ Browser │ →  │  Temp    │ →  │ Pipeline  │ → │ Results │ → │ Deleted │
│ Memory  │    │  Dir     │    │ Subprocess│   │ Display │   │ by OS   │
└─────────┘    └──────────┘    └───────────┘   └─────────┘   └─────────┘
```

### Notes on Cleanup

- **Temp directory**: Files remain in `%TEMP%` until the operating system cleans them up (typically on reboot or when disk space is low)
- **Session state**: If the user refreshes the page mid-pipeline, the `temp_dir` path stored in session state is lost, but files remain on disk
- **No explicit cleanup**: The current implementation does not delete temp files after download

---

## Security Considerations

1. **File validation**: Only `.xlsx` and `.pptx` file types are accepted by the uploader
2. **Temp isolation**: Each pipeline run gets its own temp directory
3. **No persistent storage**: Files are not stored permanently on the server
4. **Subprocess isolation**: Pipeline runs in a separate process

---

## Troubleshooting

### Progress not updating?
- Check that `evaluation_progress.json` is being written by the pipeline
- Verify the `poll_progress()` function can read the file

### Files not found?
- Ensure the temp directory wasn't deleted mid-run
- Check file paths in subprocess command

### Download button not working?
- Verify output files exist in temp directory
- Check `output_files` dictionary has correct paths
