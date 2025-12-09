# Use Python 3.11 slim image (Debian bookworm)
FROM python:3.11-slim-bookworm AS builder

# Set working directory
WORKDIR /app

# Install ONLY headless LibreOffice components needed for PPTX→PDF conversion
# Avoid full libreoffice meta-package which pulls GUI, help packs, and locales
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Core headless LibreOffice for document conversion
    libreoffice-core-nogui \
    libreoffice-impress-nogui \
    libreoffice-writer-nogui \
    # PDF utilities for pdf2image
    poppler-utils \
    # Minimal fonts for document rendering
    fonts-liberation \
    fonts-dejavu-core \
    # curl for healthcheck
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    # Remove unnecessary LibreOffice components
    && rm -rf /usr/share/libreoffice/help \
    && rm -rf /usr/share/libreoffice/readmes \
    && rm -rf /usr/share/doc/libreoffice* \
    # Remove unnecessary locales (keep only en_US)
    && find /usr/share/locale -mindepth 1 -maxdepth 1 ! -name 'en*' -exec rm -rf {} + 2>/dev/null || true \
    # Remove unnecessary fonts documentation
    && rm -rf /usr/share/fonts/truetype/dejavu/DejaVu*Condensed* \
    && rm -rf /usr/share/fonts/truetype/dejavu/DejaVu*ExtraLight*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --pre -r requirements.txt

# Copy application code
COPY . .

# Pre-warm LibreOffice during build to avoid cold-start initialization at runtime
# This creates the user profile and font cache ahead of time
RUN mkdir -p /tmp/lo_warmup \
    && echo "Warming up LibreOffice..." \
    && timeout 60 soffice --headless --invisible --nologo --nofirststartwizard \
       --convert-to pdf --outdir /tmp/lo_warmup /dev/null 2>/dev/null || true \
    && rm -rf /tmp/lo_warmup \
    && echo "LibreOffice pre-warm complete"

# Expose Streamlit port
EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
# Disable LibreOffice recovery/crash handling for faster startup
ENV SAL_DISABLE_COMPONENTREGISTRATION=1

# Health check with longer interval for large app
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
