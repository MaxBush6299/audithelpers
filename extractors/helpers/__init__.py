# Helper modules for PPTX extraction
from .config import StorageConfig, DIConfig, CUConfig
from .pptx_helpers import iter_text_shapes, iter_table_cells, iter_images
from .blob_helpers import get_blob_service, ensure_container, upload_and_sas_url
from .di_helpers import (
    analyze_document_bytes,
    analyze_image_bytes,
    analyze_document_file,
    normalize_di_result,
    extract_text_from_result,
    extract_tables_from_result,
)
from .llm_helpers import LLMConfig, analyze_slide_multimodal, flatten_extracted_text
from .slide_renderer import (
    render_slides_with_libreoffice,
    render_slides_with_powerpoint,
    render_slide_to_bytes,
    check_rendering_available,
)
from .multimodal_extract import (
    MultimodalConfig,
    multimodal_extract,
    quick_extract,
)
# Legacy CU imports (deprecated)
from .cu_helpers import cu_analyze_binary, cu_analyze_url, normalize_cu_ocr

__all__ = [
    # Config
    "StorageConfig",
    "DIConfig",
    "CUConfig",  # Deprecated
    "LLMConfig",
    "MultimodalConfig",
    # PPTX helpers
    "iter_text_shapes",
    "iter_table_cells",
    "iter_images",
    # Blob helpers
    "get_blob_service",
    "ensure_container",
    "upload_and_sas_url",
    # Document Intelligence helpers (recommended)
    "analyze_document_bytes",
    "analyze_image_bytes",
    "analyze_document_file",
    "normalize_di_result",
    "extract_text_from_result",
    "extract_tables_from_result",
    # LLM helpers
    "analyze_slide_multimodal",
    "flatten_extracted_text",
    # Slide rendering
    "render_slides_with_libreoffice",
    "render_slide_to_bytes",
    "check_rendering_available",
    # Multimodal extraction
    "multimodal_extract",
    "quick_extract",
    # Content Understanding helpers (deprecated)
    "cu_analyze_binary",
    "cu_analyze_url",
    "normalize_cu_ocr",
]
