# Project Specification: Intelligent User Feedback Analysis System

## 1. Executive Summary

**Project:** Multi-agent AI system for automated feedback processing
**Framework:** CrewAI
**Purpose:** Replace manual triaging (1-2 hours/day) with automated classification and ticket generation
**Context:** B2C mobile productivity app with ~10,000 active users receiving 10-20 app store reviews and 5-10 support emails daily

---

## 2. System Architecture

### Data Flow

```
┌─────────────────┐     ┌─────────────────┐
│ app_store_      │     │ support_        │
│ reviews.csv     │     │ emails.csv      │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
            ┌────────────────┐
            │ CSV Reader     │
            │ Agent          │
            └───────┬────────┘
                    ▼
            ┌────────────────┐
            │ Feedback       │
            │ Classifier     │
            └───────┬────────┘
                    │
         ┌──────────┼──────────┐
         ▼          ▼          ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │ Bug     │ │ Feature │ │ Other   │
    │ Analyzer│ │Extractor│ │ (pass)  │
    └────┬────┘ └────┬────┘ └────┬────┘
         │           │           │
         └───────────┼───────────┘
                     ▼
            ┌────────────────┐
            │ Ticket Creator │
            └───────┬────────┘
                    ▼
            ┌────────────────┐
            │ Quality Critic │
            └───────┬────────┘
                    ▼
         ┌──────────┴──────────┐
         ▼                     ▼
┌─────────────────┐   ┌─────────────────┐
│ generated_      │   │ processing_     │
│ tickets.csv     │   │ log.csv         │
└─────────────────┘   └─────────────────┘
```

### Tech Stack

| Component       | Technology          |
|-----------------|---------------------|
| Agent Framework | CrewAI              |
| Language        | Python 3.11+        |
| Backend API     | FastAPI             |
| Frontend UI     | Streamlit           |
| Data Processing | Pandas              |
| Validation      | Pydantic v2         |
| LLM             | OpenAI GPT-4 / GPT-3.5 |
| Containerization| Docker & Docker Compose |

---

## 3. Data Schemas

### Input Files

#### `data/app_store_reviews.csv`

| Column       | Type   | Description                          |
|--------------|--------|--------------------------------------|
| review_id    | string | Unique identifier (e.g., "REV001")   |
| platform     | string | "Google Play" or "App Store"         |
| rating       | int    | 1-5 stars                            |
| review_text  | string | User review content                  |
| user_name    | string | Reviewer display name                |
| date         | string | Review date (YYYY-MM-DD)             |
| app_version  | string | App version (e.g., "2.1.3")          |

#### `data/support_emails.csv`

| Column       | Type   | Description                          |
|--------------|--------|--------------------------------------|
| email_id     | string | Unique identifier (e.g., "EMAIL001") |
| subject      | string | Email subject line                   |
| body         | string | Email body content                   |
| sender_email | string | Sender email address                 |
| timestamp    | string | Received timestamp (ISO 8601)        |
| priority     | string | User-indicated priority (optional)   |

#### `data/expected_classifications.csv` (Ground Truth)

| Column            | Type   | Description                      |
|-------------------|--------|----------------------------------|
| source_id         | string | Matches review_id or email_id    |
| source_type       | string | "app_store_review" or "email"    |
| category          | string | Expected classification          |
| priority          | string | Expected priority level          |
| technical_details | string | For bugs: device, OS, steps      |
| suggested_title   | string | Expected ticket title            |

### Output Files

#### `output/generated_tickets.csv`

| Column            | Type   | Description                      |
|-------------------|--------|----------------------------------|
| ticket_id         | string | Generated UUID                   |
| source_id         | string | Original feedback ID             |
| source_type       | string | "app_store_review" or "email"    |
| title             | string | Ticket title                     |
| category          | string | Bug/Feature Request/Praise/etc.  |
| priority          | string | Critical/High/Medium/Low         |
| description       | string | Full ticket description          |
| technical_details | string | For bugs only                    |
| confidence        | float  | Classification confidence (0-1)  |
| created_at        | string | Timestamp                        |

#### `output/processing_log.csv`

| Column        | Type   | Description                        |
|---------------|--------|------------------------------------|
| log_id        | string | Unique log entry ID                |
| timestamp     | string | Processing timestamp               |
| source_id     | string | Feedback being processed           |
| agent         | string | Agent that performed action        |
| action        | string | Action taken                       |
| result        | string | Outcome or decision                |
| confidence    | float  | Confidence score if applicable     |

#### `output/metrics.csv`

| Column              | Type   | Description                    |
|---------------------|--------|--------------------------------|
| run_id              | string | Processing run identifier      |
| timestamp           | string | Run timestamp                  |
| total_processed     | int    | Total feedback items           |
| bugs_found          | int    | Count by category              |
| features_found      | int    |                                |
| praise_found        | int    |                                |
| complaints_found    | int    |                                |
| spam_found          | int    |                                |
| accuracy            | float  | vs expected_classifications    |
| avg_confidence      | float  | Average classification score   |
| processing_time_sec | float  | Total processing duration      |

---

## 4. Agent Specifications

### Agent 1: CSV Reader Agent

**Role:** Data Ingestion Specialist
**Goal:** Read and parse feedback data from CSV files, normalizing different formats into a unified structure
**Backstory:** Expert data engineer specializing in ETL pipelines who ensures data quality and proper formatting before downstream processing

**Input:** File paths to CSV files
**Output:** List of normalized feedback objects with source tracking

**Tools:**
- `read_csv_tool`: Reads CSV files and returns structured data
- `validate_schema_tool`: Validates CSV columns match expected schema

**Success Criteria:**
- All rows parsed without errors
- Source type correctly identified
- Missing fields handled gracefully

---

### Agent 2: Feedback Classifier Agent

**Role:** Senior Feedback Classification Specialist
**Goal:** Accurately categorize user feedback into Bug, Feature Request, Praise, Complaint, or Spam with confidence scores
**Backstory:** NLP expert with years of experience analyzing customer feedback for SaaS products. Understands nuances between frustrated bug reports and feature requests.

**Input:** Normalized feedback object
**Output:** Classification result with category, confidence, and reasoning

**Classification Rules:**

| Category        | Signals                                           | Typical Rating |
|-----------------|---------------------------------------------------|----------------|
| Bug             | "crash", "error", "broken", "doesn't work", "can't" | 1-2 stars     |
| Feature Request | "please add", "would love", "wish", "missing"     | 3-4 stars      |
| Praise          | "love", "amazing", "great", "perfect", "best"     | 4-5 stars      |
| Complaint       | "expensive", "slow", "poor service", "disappointed" | 2-3 stars     |
| Spam            | Promotional, random text, unrelated content       | Any            |

**Tools:**
- None (LLM-based classification)

**Success Criteria:**
- Confidence score > 0.7 for clear cases
- Reasoning provided for each classification
- Edge cases flagged for review

---

### Agent 3: Bug Analysis Agent

**Role:** Bug Analysis Specialist
**Goal:** Extract technical details from bug reports including steps to reproduce, platform info, and severity assessment
**Backstory:** Senior QA engineer with 10 years of experience triaging bug reports across mobile platforms. Expert at identifying critical bugs that need immediate attention.

**Input:** Feedback classified as "Bug"
**Output:** Structured bug analysis

**Extraction Fields:**
- Steps to reproduce (if mentioned)
- Platform/OS version
- App version
- Device model (if mentioned)
- Severity assessment
- Affected functionality

**Severity Levels:**

| Severity | Criteria                                          |
|----------|---------------------------------------------------|
| Critical | Data loss, security issue, app unusable           |
| High     | Major feature broken, affects core functionality  |
| Medium   | Minor bug, workaround exists                      |
| Low      | Cosmetic issue, edge case                         |

**Tools:**
- None (LLM-based extraction)

**Success Criteria:**
- Platform always identified
- Severity always assigned
- Technical details structured consistently

---

### Agent 4: Feature Extractor Agent

**Role:** Product Feature Analyst
**Goal:** Identify feature requests, assess user impact, and estimate demand
**Backstory:** Product manager with deep understanding of user needs. Skilled at translating user wishes into actionable product requirements.

**Input:** Feedback classified as "Feature Request"
**Output:** Structured feature analysis

**Extraction Fields:**
- Requested feature summary
- User pain point
- Potential impact (High/Medium/Low)
- Similar existing features (if any)
- Implementation complexity estimate

**Tools:**
- None (LLM-based extraction)

**Success Criteria:**
- Feature clearly summarized
- Impact assessed based on user language intensity
- Actionable description provided

---

### Agent 5: Ticket Creator Agent

**Role:** Technical Ticket Specialist
**Goal:** Generate structured, actionable tickets with consistent formatting and appropriate metadata
**Backstory:** Engineering team lead experienced in creating clear, actionable tickets that developers can immediately work on.

**Input:** Classified and analyzed feedback
**Output:** Structured ticket object

**Ticket Template:**

```
Title: [Category] Brief description
Priority: [Critical|High|Medium|Low]
Category: [Bug|Feature Request|Praise|Complaint|Spam]
Source: [source_type] - [source_id]

Description:
[Detailed description based on analysis]

Technical Details: (for bugs)
[Platform, steps to reproduce, severity]

User Impact: (for features)
[Impact assessment, user pain point]

Original Feedback:
[Quoted original text]
```

**Tools:**
- `write_csv_tool`: Appends ticket to generated_tickets.csv
- `log_processing_tool`: Records processing decisions

**Success Criteria:**
- All required fields populated
- Consistent formatting
- Traceability to source maintained

---

### Agent 6: Quality Critic Agent

**Role:** Quality Assurance Reviewer
**Goal:** Review generated tickets for completeness, accuracy, and actionability
**Backstory:** Senior QA lead who ensures every ticket meets quality standards before reaching the engineering team.

**Input:** Generated ticket
**Output:** Quality assessment with approval or revision requests

**Quality Checks:**
- Title is descriptive and actionable
- Priority matches severity/impact
- Description is complete
- Technical details present for bugs
- No duplicate tickets
- Proper categorization

**Tools:**
- `read_csv_tool`: Check for duplicate tickets
- `update_ticket_tool`: Apply revisions

**Success Criteria:**
- 95% of tickets pass quality checks
- Clear feedback for rejected tickets
- No critical information missing

---

### Agent 7: Fallback Agent

**Role:** Emergency Fallback Processor
**Goal:** Create a minimal, valid ticket from feedback that failed normal processing. Summarize the feedback content and mark it for manual review.
**Backstory:** Reliable backup processor that ensures no feedback is lost. When the main processing pipeline fails, steps in to create a basic ticket with the essential information. Always produces valid output, even from difficult or malformed input.

**Input:** Failed feedback item with error details
**Output:** Minimal ticket with "Failed" category

**Ticket Template:**
```
Title: [Failed] Manual review required - {source_id}
Priority: Medium
Category: Failed
Description: Summary of original feedback content
Technical Details: Error information and retry attempts
```

**Tools:**
- `write_csv_tool`: Appends fallback ticket to generated_tickets.csv

**Success Criteria:**
- Always produces valid output
- No feedback lost due to processing errors
- Clear flagging for manual review
- Error details captured for debugging

---

## 5. Error Handling & Retry Mechanism

### Retry Logic

When processing fails for a feedback item:
1. **Retry up to 3 times** - Each attempt logs the error and retries
2. **On final failure** - Fallback Agent creates a minimal ticket
3. **No pipeline break** - Processing continues with remaining items

### Fallback Ticket Properties

| Field           | Value                                    |
|-----------------|------------------------------------------|
| category        | "Failed"                                 |
| priority        | "Medium"                                 |
| title           | "[Failed] Manual review required - {id}" |
| description     | Summary of original feedback             |
| technical_details | Error type and retry count             |
| confidence      | 0.0                                      |

### Error Tracking

Failed items are logged with:
- `retry_attempts`: Number of attempts made (max 3)
- `error_type`: Exception class name
- `error_message`: Full error description
- `status`: "fallback" (vs "success" for normal items)

---

## 6. Priority Assignment Rules

| Category        | Default Priority | Upgrade Conditions                    |
|-----------------|------------------|---------------------------------------|
| Bug             | Medium           | Critical if: data loss, security, crash |
| Bug             | High             | If: affects core functionality        |
| Feature Request | Low              | Medium if: high user demand signals   |
| Praise          | Low              | N/A                                   |
| Complaint       | Medium           | High if: subscription/payment related |
| Spam            | Low              | N/A (may auto-discard)                |

**Priority Escalation Signals:**
- Multiple users reporting same issue
- Words: "urgent", "critical", "immediately", "data loss"
- Low ratings (1 star) combined with bug report
- Payment/subscription issues

---

## 7. Streamlit UI Requirements

### Page 1: Dashboard

**Components:**
- Summary cards: Total processed, by category, by priority
- Recent tickets table (last 20)
- Processing status indicator
- Quick filters by category/priority

### Page 2: Configuration Panel

**Components:**
- Classification threshold slider (0.5-0.9)
- Priority override rules
- Agent verbosity toggle
- LLM model selection
- Input file path configuration

### Page 3: Manual Override

**Components:**
- Ticket editor form
- Category/priority dropdowns
- Approve/reject buttons
- Batch approval for similar tickets
- Edit history log

### Page 4: Analytics

**Components:**
- Classification distribution pie chart
- Priority distribution bar chart
- Accuracy over time line chart
- Processing time metrics
- Confidence score histogram

---

## 8. Project Structure

```
crew-ai-agent/
├── backend/
│   ├── src/                     # All backend source code
│   │   ├── api/
│   │   │   └── main.py              # FastAPI application
│   │   ├── core/
│   │   │   └── feedback_service.py  # Service layer
│   │   ├── agents/
│   │   │   └── feedback_agents.py   # Agent definitions
│   │   ├── tools/
│   │   │   ├── csv_tools.py         # Read/write CSV operations
│   │   │   └── logging_tools.py     # Processing log utilities
│   │   ├── models/
│   │   │   ├── feedback.py          # Pydantic input models
│   │   │   └── ticket.py            # Pydantic output models
│   │   └── crew.py                  # Crew orchestration logic
│   ├── Dockerfile               # Backend container
│   └── requirements.txt         # Backend dependencies
├── frontend/
│   ├── src/                     # Frontend source code
│   │   └── app.py               # Streamlit dashboard
│   ├── Dockerfile               # Frontend container
│   └── requirements.txt         # Frontend dependencies
├── config/
│   └── agents.yaml              # Agent role/goal/backstory definitions
├── data/
│   ├── app_store_reviews.csv
│   ├── support_emails.csv
│   └── expected_classifications.csv
├── output/                      # Generated at runtime
│   ├── generated_tickets.csv
│   ├── processing_log.csv
│   └── metrics.csv
├── tests/
│   ├── __init__.py
│   ├── api/                     # API endpoint tests
│   ├── integration_api/         # API integration tests
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
├── memory/
│   ├── project_spec.md          # This file
│   └── agent_development/
│       ├── agent_development.md
│       └── python_best_practices.md
├── documents/
│   └── requirements.pdf
├── docker-compose.yml           # Docker Compose configuration
├── .dockerignore
├── .env.example
├── .gitignore
└── README.md
```

---

## 9. Implementation Phases

### Phase 1: Mock Data Creation

- Create `app_store_reviews.csv` with 20-30 realistic reviews
- Create `support_emails.csv` with 10-15 support emails
- Create `expected_classifications.csv` for accuracy testing
- Cover all 5 categories with varied examples

### Phase 2: Core Agents & Tools

- Implement Pydantic models for data validation
- Create CSV read/write tools
- Implement 6 agents with proper role/goal/backstory
- Unit test each agent independently

### Phase 3: Crew Orchestration

- Define task dependencies in tasks.yaml
- Configure sequential processing pipeline
- Implement error handling and retries
- Test end-to-end pipeline

### Phase 4: Backend API

- Implement FastAPI backend with REST endpoints
- Create feedback service layer
- Add API documentation (Swagger/ReDoc)
- Implement error handling and validation

### Phase 5: Frontend UI

- Refactor Streamlit to use API calls
- Build dashboard page with metrics
- Implement configuration panel
- Add manual override functionality
- Create analytics visualizations

### Phase 6: Dockerization

- Create Dockerfiles for backend and frontend
- Set up Docker Compose configuration
- Configure networking and volumes
- Test containerized deployment

### Phase 5: Testing & Validation

- Run accuracy tests against expected_classifications.csv
- Performance benchmarking
- Edge case testing
- Documentation finalization

---

## 10. Testing Strategy

See [memory/testing_strategy.md](testing_strategy.md) for comprehensive testing documentation including:

- Test structure and organization
- Unit, integration, and accuracy tests
- Running tests and coverage
- CI/CD automation with GitHub Actions
- Guidelines for adding/updating tests

### Quick Reference

```bash
pytest                          # Run all tests
pytest --cov=src               # Run with coverage
pytest -m unit                 # Unit tests only
pytest -m integration          # Integration tests
pytest -m accuracy             # Accuracy validation
```

### Accuracy Targets

| Metric           | Target |
|------------------|--------|
| Overall accuracy | >= 80% |
| Bug recall       | >= 90% |
| Spam precision   | >= 95% |

---

## 11. Configuration

### Environment Variables (`.env`)

```
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-4
CLASSIFICATION_THRESHOLD=0.7
VERBOSE=true
```

### `requirements.txt`

```
crewai>=0.28.0
streamlit>=1.30.0
pandas>=2.0.0
pydantic>=2.0.0
python-dotenv>=1.0.0
openai>=1.0.0
pytest>=7.0.0
```
