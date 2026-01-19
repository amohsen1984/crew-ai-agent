FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .
COPY requirements.txt ./root_requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code (src is now part of backend)
COPY backend/ ./backend/
COPY config/ ./config/
COPY data/ ./data/

# Create output directory
RUN mkdir -p output

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app/backend/src
ENV DATA_DIR=/app/data
ENV OUTPUT_DIR=/app/output

# Run the API (api.main is in backend/src/api/)
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

