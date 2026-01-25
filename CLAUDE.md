# CLAUDE.md

## Overview

Multi-agent feedback analysis system (CrewAI) that processes app store reviews and support emails into structured tickets. Replaces manual triaging for a B2C mobile app.

## Tech Stack

Python, CrewAI, Streamlit, Pandas, Pydantic

## Commands

```bash
# Install dependencies
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt

# Run with Docker Compose (recommended)
docker-compose up

# Or run locally
# Backend API
cd backend && uvicorn src.api.main:app --reload

# Frontend UI (in another terminal)
cd frontend && streamlit run src/app.py
```

## Architecture

7 agents in sequential pipeline:

1. **CSV Reader** - Ingests feedback from data/*.csv
2. **Classifier** - Categorizes: Bug | Feature Request | Praise | Complaint | Spam | Failed
3. **Bug Analyzer** - Extracts technical details, severity
4. **Feature Extractor** - Assesses user impact/demand
5. **Ticket Creator** - Generates structured tickets
6. **Quality Critic** - Reviews completeness and accuracy
7. **Fallback Agent** - Handles failed items after retries (creates minimal tickets)

## Error Handling

- **Retry mechanism**: Failed items retry up to 3 times
- **Fallback processing**: Items that fail all retries get "Failed" category with summary
- **No pipeline breaks**: Processing continues even when individual items fail

## Key Files

```text
backend/src/                      # Backend source code (API, agents, tools, models)
frontend/src/app.py               # Streamlit UI (API consumer)
config/agents.yaml                # Agent definitions
data/*.csv                        # Input: reviews, emails
output/*.csv                      # Output: tickets, logs, metrics
docker-compose.yml                # Docker orchestration
```

## Testing

```bash
pytest                    # Run all tests
pytest --cov=src         # With coverage
pytest -m unit           # Unit tests only
```

See [memory/testing_strategy.md](memory/testing_strategy.md) for full testing documentation.

## Full Specification

See [memory/project_spec.md](memory/project_spec.md) for detailed requirements, data schemas, and implementation phases.
