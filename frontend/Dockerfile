FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY frontend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend code
COPY frontend/ ./frontend/

# Expose port
EXPOSE 8501

# Set environment variables
ENV PYTHONPATH=/app
ENV API_BASE_URL=http://backend:8000

# Run Streamlit
CMD ["streamlit", "run", "frontend/src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
