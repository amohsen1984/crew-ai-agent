# Demo Plan - Intelligent User Feedback Analysis System

## Overview
**Total Duration:** ~15-20 minutes  
**Format:** Side-by-side screen recording (Browser UI + Docker logs)

---

## Section 1: Introduction (2 minutes)

### 1.1 Project Overview (30 seconds)
- **What:** Multi-agent AI system for automated feedback processing
- **Problem:** Manual triaging takes 1-2 hours/day
- **Solution:** Automated classification and ticket generation using CrewAI
- **Impact:** Saves time, improves consistency, enables scalability

### 1.2 Repository Structure (30 seconds)
- Show project structure briefly
- Backend (FastAPI) + Frontend (Streamlit)
- Dockerized deployment
- 7 specialized AI agents

### 1.3 Tech Stack (1 minute)
- CrewAI for multi-agent orchestration
- OpenAI GPT-4 for LLM backend
- FastAPI for REST API
- Streamlit for dashboard
- Docker for containerization

---

## Section 2: Architecture (3 minutes)

### 2.1 System Architecture Diagram (1 minute)
- Show high-level architecture
- Frontend ↔ Backend ↔ CrewAI Agents
- Data flow: CSV → Agents → Tickets

### 2.2 Agent Pipeline (1.5 minutes)
- 7 agents in sequence:
  1. CSV Reader - Data ingestion
  2. Feedback Classifier - Categorization
  3. Bug Analyzer - Technical analysis
  4. Feature Extractor - Impact assessment
  5. Ticket Creator - Structured output
  6. Quality Critic - QA review
  7. Fallback Agent - Error handling

### 2.3 Data Flow (30 seconds)
- Input: app_store_reviews.csv, support_emails.csv
- Processing: Multi-agent pipeline
- Output: generated_tickets.csv, metrics.csv, processing_log.csv

---

## Section 3: Main Features Demonstration (8-10 minutes)

### 3.1 Dashboard & Starting Process (2 minutes)
**Actions:**
- Open browser to http://localhost:8501
- Show dashboard overview
- Click "Process Feedback" button
- Show Docker logs side-by-side showing processing start

**Key Points:**
- Dashboard shows summary cards (Total Tickets, Bugs, Features, etc.)
- Processing status indicator in sidebar
- Real-time progress tracking

### 3.2 Tracking Progress (1.5 minutes)
**Actions:**
- Show progress bar updating
- Show Docker logs showing agent activity
- Show "Current item being processed" messages
- Wait for completion

**Key Points:**
- Real-time progress updates
- Parallel processing (3 workers)
- Status updates every 5 seconds

### 3.3 Configuration - Categorizing & Priority Rules (2 minutes)
**Actions:**
- Navigate to Configuration tab
- Show Bug priority rules configuration
- Modify keywords (e.g., add "critical bug" to critical keywords)
- Save and explain impact
- Show Feature Request rules
- Show Complaint rules

**Key Points:**
- Customizable priority assignment
- Keyword-based escalation
- Rules persist across sessions
- Backend integration

### 3.4 Configuration - Threshold Impact (1.5 minutes)
**Actions:**
- Show Classification Threshold slider (0.5-0.9)
- Explain: Lower = more lenient, Higher = more strict
- Change threshold (e.g., from 0.7 to 0.8)
- Explain how this affects confidence requirements
- Show impact on processing

**Key Points:**
- Threshold controls classification confidence requirements
- Affects false positive/negative rates
- Configurable per processing run

### 3.5 Analytics Dashboard (1 minute)
**Actions:**
- Navigate to Analytics tab
- Show classification distribution pie chart
- Show priority distribution bar chart
- Show confidence score histogram
- Show summary statistics

**Key Points:**
- Visual insights into processed feedback
- Category distribution
- Priority breakdown
- Confidence metrics

### 3.6 Quality Metrics (QA Comparison) (2 minutes)
**Actions:**
- Navigate to QA tab
- Show accuracy summary (Category Accuracy, Priority Accuracy, Full Match)
- Show accuracy by category bar chart
- Show confusion matrix
- Show priority accuracy breakdown
- Show detailed comparison table

**Key Points:**
- Compares actual vs expected classifications
- Measures system performance
- Identifies areas for improvement
- Detailed mismatch analysis

---

## Section 4: Production Deployment to AWS (3-4 minutes)

### 4.1 Current Architecture Limitations (30 seconds)
- CSV file-based storage
- No real-time event processing
- Limited scalability
- Manual file management

### 4.2 AWS Production Architecture (2 minutes)
**Show High-Level Diagram:**

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS Production Architecture                │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   App Store  │      │   Support    │      │   Webhook    │
│   Reviews    │      │   Emails     │      │   Endpoints  │
│   (S3/API)   │      │   (SES)      │      │              │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                    │                      │
       └────────────────────┼──────────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  EventBridge     │
                   │  (Event Bus)     │
                   └────────┬─────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   Lambda        │
                   │   (Ingestion)   │
                   └────────┬─────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   SQS Queue     │
                   │   (Buffering)    │
                   └────────┬─────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   ECS Fargate    │
                   │   (CrewAI Agents)│
                   └────────┬─────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   RDS PostgreSQL │
                   │   (Tickets DB)   │
                   └────────┬─────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   DynamoDB      │
                   │   (Metrics)     │
                   └────────┬─────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │   S3 Bucket     │
                   │   (Artifacts)   │
                   └─────────────────┘
```

### 4.3 Component Details (1 minute)

**Event Sources:**
- App Store Reviews → S3 bucket or API Gateway
- Support Emails → Amazon SES → EventBridge
- Webhook endpoints → API Gateway → EventBridge

**Processing:**
- EventBridge routes events to Lambda
- Lambda validates and enqueues to SQS
- ECS Fargate tasks consume from SQS
- CrewAI agents process feedback
- Results written to RDS PostgreSQL

**Storage:**
- RDS PostgreSQL: Structured ticket data
- DynamoDB: Metrics and analytics
- S3: Processing logs, artifacts

**Frontend:**
- Streamlit app on ECS Fargate
- CloudFront CDN for static assets
- ALB for load balancing

### 4.4 Migration Strategy (30 seconds)
1. **Phase 1:** Replace CSV reader with EventBridge listener
2. **Phase 2:** Migrate ticket storage to RDS PostgreSQL
3. **Phase 3:** Move metrics to DynamoDB
4. **Phase 4:** Deploy ECS Fargate with auto-scaling
5. **Phase 5:** Add CloudWatch monitoring and alerts

---

## Section 5: Closing (1 minute)

### 5.1 Key Takeaways
- Automated feedback processing saves 1-2 hours/day
- Multi-agent system ensures quality and accuracy
- Configurable rules and thresholds
- Production-ready AWS architecture designed

### 5.2 Next Steps
- Implement AWS migration
- Add more agent capabilities
- Expand to other feedback sources
- Continuous improvement based on QA metrics

---

## Technical Setup for Demo

### Prerequisites
- Docker and Docker Compose running
- Backend API: http://localhost:8001
- Frontend UI: http://localhost:8501
- Sample data files in `data/` directory
- Docker logs visible in terminal

### Screen Layout
- **Left Side (60%):** Browser with Streamlit UI
- **Right Side (40%):** Terminal with Docker logs (`docker-compose logs -f`)

### Recording Settings
- Resolution: 1920x1080
- Frame rate: 30 fps
- Audio: Voice narration + system sounds
- Format: MP4

---

## Timing Summary

| Section | Duration | Cumulative |
|---------|----------|------------|
| Introduction | 2 min | 2 min |
| Architecture | 3 min | 5 min |
| Features Demo | 8-10 min | 13-15 min |
| AWS Production | 3-4 min | 16-19 min |
| Closing | 1 min | 17-20 min |

**Total: ~17-20 minutes**
