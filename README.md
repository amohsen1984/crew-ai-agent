# Intelligent User Feedback Analysis System

A multi-agent AI system built with CrewAI that automatically processes app store reviews and support emails into structured tickets, replacing manual triaging.

## Architecture

The system is split into **frontend** and **backend** components:

- **Backend**: FastAPI REST API that handles feedback processing using CrewAI agents
- **Frontend**: Streamlit web dashboard that communicates with the backend API
- **Docker**: Both components are containerized and can be run with Docker Compose

## Overview

This system uses 7 specialized AI agents working in sequence to:
1. **Read** feedback from CSV files
2. **Classify** feedback into categories (Bug, Feature Request, Praise, Complaint, Spam, Failed)
3. **Analyze** bugs and feature requests for technical details
4. **Create** structured tickets
5. **Review** tickets for quality assurance
6. **Handle failures** with fallback processing for items that can't be classified

## Features

- Automated feedback classification with confidence scores
- Technical bug analysis with severity assessment
- Feature request impact analysis
- Structured ticket generation
- Quality assurance review
- **Retry mechanism** with up to 3 attempts for failed items
- **Fallback processing** for items that can't be classified (no data loss)
- RESTful API for backend processing
- Streamlit dashboard for visualization and manual override
- QA comparison tab for accuracy analysis
- Dockerized deployment
- Comprehensive test suite

## Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** - REST API framework
- **CrewAI** - Multi-agent orchestration
- **Pydantic v2** - Data validation
- **Pandas** - Data processing
- **OpenAI GPT-4** - LLM backend

### Frontend
- **Streamlit** - Web dashboard
- **Requests** - HTTP client for API communication

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

## Prerequisites

- Docker and Docker Compose (for containerized deployment)
- OR Python 3.11+ (for local development)
- OpenAI API key

## Quick Start with Docker (Recommended)

### Option 1: Automated Setup Script (Easiest)

Run the setup script which will:
1. Create separate virtual environments for backend and frontend
2. Install all dependencies in their respective environments
3. Set up `.env` file (if needed)
4. Start Docker Compose with all services

```bash
./setup.sh
```

**Note**: Make sure to edit the `.env` file and add your `OPENAI_API_KEY` before the script runs docker-compose.

### Option 2: Manual Setup

#### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd crew-ai-agent
```

#### Step 2: Configure Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-your-api-key-here
MODEL_NAME=gpt-4
VERBOSE=false
```

#### Step 3: Run with Docker Compose

```bash
docker-compose up --build
```

This will:
- Build backend and frontend containers
- Start the backend API on `http://localhost:8001`
- Start the frontend dashboard on `http://localhost:8501`
- Set up networking between containers

#### Step 4: Access the Application

- **Frontend Dashboard**: http://localhost:8501
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs

### Stop the Application

```bash
docker-compose down
```

## Local Development

### Backend Setup

1. **Create virtual environment:**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install backend dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables:**
   ```bash
   export OPENAI_API_KEY=sk-your-api-key-here
   export DATA_DIR=data
   export OUTPUT_DIR=output
   ```

3. **Run the backend API:**
   ```bash
   # Make sure backend venv is activated
   python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8001
   ```

### Frontend Setup

1. **Create virtual environment:**
   ```bash
   cd frontend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install frontend dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set API URL:**
   ```bash
   export API_BASE_URL=http://localhost:8001
   ```

3. **Run the frontend:**
   ```bash
   # Make sure frontend venv is activated
   streamlit run src/app.py
   ```

## Project Structure

```
crew-ai-agent/
├── backend/
│   ├── src/                     # All backend source code
│   │   ├── api/                 # REST API endpoints
│   │   │   └── main.py
│   │   ├── core/                # Service layer
│   │   │   └── feedback_service.py
│   │   ├── agents/              # Agent definitions
│   │   ├── tools/               # Agent tools
│   │   ├── models/              # Pydantic models
│   │   └── crew.py              # Crew orchestration
│   ├── Dockerfile               # Backend container
│   └── requirements.txt          # Backend dependencies
├── frontend/
│   ├── src/                     # Frontend source code
│   │   └── app.py               # Streamlit dashboard
│   ├── Dockerfile               # Frontend container
│   └── requirements.txt         # Frontend dependencies
├── config/                      # Configuration files
├── data/                        # Input CSV files
├── output/                      # Generated files
├── tests/
│   ├── api/                     # API tests
│   ├── integration_api/         # API integration tests
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
├── docker-compose.yml           # Docker Compose config
└── README.md                    # This file
```

## API Endpoints

### Health Check
- `GET /api/v1/health` - Health check endpoint

### Processing
- `POST /api/v1/process` - Process feedback and generate tickets

### Tickets
- `GET /api/v1/tickets` - Get all tickets (with optional filters)
  - Query params: `category`, `priority`, `limit`
- `GET /api/v1/tickets/{ticket_id}` - Get specific ticket
- `PATCH /api/v1/tickets/{ticket_id}` - Update ticket

### Metrics & Stats
- `GET /api/v1/metrics` - Get processing metrics
- `GET /api/v1/stats` - Get summary statistics

### API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## Docker Commands

### Build containers
```bash
docker-compose build
```

### Start services
```bash
docker-compose up
```

### Start in background
```bash
docker-compose up -d
```

### View logs
```bash
docker-compose logs -f
```

### Stop services
```bash
docker-compose down
```

### Rebuild and restart
```bash
docker-compose up --build
```

### Execute commands in containers
```bash
# Backend shell
docker-compose exec backend bash

# Frontend shell
docker-compose exec frontend bash
```

## Testing

**Note**: Tests should be run from the backend virtual environment since they test backend functionality.

### Run All Tests

```bash
# Activate backend venv first
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
cd ..
pytest
```

### Run API Tests

```bash
pytest tests/api/
```

### Run Integration Tests

```bash
pytest tests/integration_api/
```

### Run with Coverage

```bash
pytest --cov=backend --cov-report=html
```

## Environment Variables

### Backend

```env
OPENAI_API_KEY=sk-your-api-key-here  # Required
MODEL_NAME=gpt-4                      # Optional, default: gpt-4
DATA_DIR=/app/data                   # Optional, default: data
OUTPUT_DIR=/app/output                # Optional, default: output
VERBOSE=false                         # Optional, default: false
CREWAI_TELEMETRY_OPT_OUT=1            # Optional, disables telemetry
```

### Frontend

```env
API_BASE_URL=http://localhost:8001   # Backend API URL
```

## Data Format

### Input Files

See the main README section on data format. Input files should be placed in the `data/` directory.

### Output Files

All output files are generated in the `output/` directory:
- `generated_tickets.csv` - Structured tickets
- `processing_log.csv` - Processing log
- `metrics.csv` - Processing metrics

## Troubleshooting

### Backend won't start

1. Check environment variables are set correctly
2. Verify OpenAI API key is valid
3. Check logs: `docker-compose logs backend`

### Frontend can't connect to backend

1. Verify backend is running: `curl http://localhost:8001/api/v1/health`
2. Check `API_BASE_URL` environment variable
3. In Docker, ensure both services are on the same network

### Docker build fails

1. Check Docker is running: `docker ps`
2. Verify Dockerfile syntax
3. Check build logs: `docker-compose build --no-cache`

### Port conflicts

If ports 8000 or 8501 are in use, modify `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Change host port
```

## Development Workflow

1. **Make code changes** in `backend/` or `frontend/`
2. **Rebuild containers**: `docker-compose up --build`
3. **Run tests**: `pytest`
4. **Check API**: Visit http://localhost:8001/docs
5. **Test frontend**: Visit http://localhost:8501

## Production Deployment

For production:

1. Set `CORS_ORIGINS` in backend to specific frontend URL
2. Use environment-specific `.env` files
3. Set up proper volume mounts for data persistence
4. Configure logging and monitoring
5. Use reverse proxy (nginx) for SSL termination
6. Set resource limits in docker-compose.yml

## License

[Your License Here]

## Contributing

[Contributing Guidelines Here]
