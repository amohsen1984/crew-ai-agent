# AWS Production Architecture

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Production Architecture                    │
│              Intelligent User Feedback Analysis System            │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   App Store  │      │   Support    │      │   Webhook    │
│   Reviews    │      │   Emails     │      │   Endpoints  │
│              │      │              │      │              │
│  (S3/API)    │      │   (SES)      │      │  (API GW)    │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                      │
       │                     │                      │
       └─────────────────────┼──────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Amazon         │
                    │  EventBridge    │
                    │  (Event Bus)    │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   AWS Lambda    │
                    │   (Ingestion)   │
                    │                 │
                    │  - Validate     │
                    │  - Transform    │
                    │  - Enqueue      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Amazon SQS    │
                    │   (Buffering)   │
                    │                 │
                    │  - Queue        │
                    │  - Retry Logic  │
                    │  - DLQ          │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   ECS Fargate   │
                    │                 │
                    │  CrewAI Agents  │
                    │                 │
                    │  - Auto-scaling │
                    │  - Health checks│
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  RDS          │   │  DynamoDB     │   │  S3 Bucket     │
│  PostgreSQL   │   │               │   │               │
│               │   │  - Metrics    │   │  - Logs        │
│  - Tickets    │   │  - Analytics  │   │  - Artifacts   │
│  - Metadata   │   │  - Time-series│   │  - Backups     │
└───────────────┘   └───────────────┘   └───────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Streamlit     │
                    │   Dashboard     │
                    │                 │
                    │  - ECS Fargate  │
                    │  - ALB          │
                    │  - CloudFront   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │     Users       │
                    │   (Browser)     │
                    └─────────────────┘
```

## Component Details

### Event Sources

#### 1. App Store Reviews
- **Ingestion Method:** 
  - Option A: S3 bucket with lifecycle policies
  - Option B: API Gateway endpoint for real-time ingestion
- **Format:** JSON events from App Store Connect API or manual uploads
- **Volume:** ~10-20 reviews/day (scalable to thousands)

#### 2. Support Emails
- **Service:** Amazon SES (Simple Email Service)
- **Configuration:** 
  - Email receiving rule set
  - S3 bucket for email storage (optional)
  - EventBridge rule for email events
- **Volume:** ~5-10 emails/day (scalable)

#### 3. Webhook Endpoints
- **Service:** API Gateway
- **Purpose:** Accept feedback from other sources (Zendesk, Intercom, etc.)
- **Authentication:** API keys or IAM authentication

### Event Processing

#### Amazon EventBridge
- **Role:** Central event bus
- **Benefits:**
  - Decouples event sources from processors
  - Event routing and filtering
  - Event replay capabilities
  - Integration with 100+ AWS services

#### AWS Lambda (Ingestion)
- **Function:** Event validation and transformation
- **Responsibilities:**
  - Validate event schema
  - Transform to standard format
  - Enqueue to SQS
  - Error handling and dead letter queue
- **Timeout:** 30 seconds
- **Memory:** 256 MB

#### Amazon SQS
- **Type:** Standard Queue (or FIFO for ordering)
- **Purpose:** 
  - Buffer between ingestion and processing
  - Handle traffic spikes
  - Retry failed messages
- **Configuration:**
  - Visibility timeout: 5 minutes
  - Message retention: 14 days
  - Dead letter queue for failed messages

### Processing Layer

#### ECS Fargate (CrewAI Agents)
- **Service:** ECS Fargate tasks
- **Configuration:**
  - Task definition with CrewAI agents
  - Auto-scaling based on SQS queue depth
  - Health checks
  - Logging to CloudWatch
- **Scaling:**
  - Min tasks: 1
  - Max tasks: 10
  - Target: 70% CPU utilization
  - Scale based on SQS queue depth
- **Resources:**
  - CPU: 2 vCPU per task
  - Memory: 4 GB per task

### Data Storage

#### Amazon RDS PostgreSQL
- **Purpose:** Primary ticket storage
- **Schema:**
  - `tickets` table (structured ticket data)
  - `processing_logs` table (audit trail)
  - `configurations` table (priority rules, thresholds)
- **Configuration:**
  - Instance: db.t3.medium (or larger for production)
  - Multi-AZ for high availability
  - Automated backups (7-day retention)
  - Read replicas for analytics queries

#### Amazon DynamoDB
- **Purpose:** Metrics and analytics
- **Tables:**
  - `metrics` - Time-series metrics
  - `analytics` - Aggregated statistics
- **Configuration:**
  - On-demand billing
  - TTL for old data (90 days)
  - Global secondary indexes for queries

#### Amazon S3
- **Buckets:**
  - `feedback-artifacts` - Processing logs, CSV exports
  - `feedback-backups` - Database backups
- **Lifecycle Policies:**
  - Move to Glacier after 30 days
  - Delete after 1 year

### Frontend

#### Streamlit Dashboard (ECS Fargate)
- **Deployment:** Containerized Streamlit app
- **Configuration:**
  - ECS Fargate service
  - Application Load Balancer (ALB)
  - CloudFront CDN for static assets
- **Scaling:**
  - Auto-scaling based on CPU/memory
  - Min: 2 tasks (for HA)
  - Max: 10 tasks

#### Application Load Balancer (ALB)
- **Type:** Application Load Balancer
- **Features:**
  - SSL termination
  - Health checks
  - Path-based routing
  - Sticky sessions (if needed)

#### CloudFront CDN
- **Purpose:** Distribute static assets globally
- **Configuration:**
  - Origin: ALB
  - Caching policies
  - HTTPS only

### Monitoring & Observability

#### Amazon CloudWatch
- **Metrics:**
  - Lambda invocations, errors, duration
  - SQS queue depth, message age
  - ECS task count, CPU, memory
  - RDS connections, CPU, storage
  - API Gateway requests, latency, errors
- **Logs:**
  - Lambda execution logs
  - ECS container logs
  - Application logs
- **Alarms:**
  - High error rates
  - Queue depth thresholds
  - Database connection issues
  - API latency spikes

#### AWS X-Ray
- **Purpose:** Distributed tracing
- **Coverage:**
  - Lambda functions
  - ECS tasks
  - API Gateway
- **Benefits:** End-to-end request tracing

## Migration Strategy

### Phase 1: Event Ingestion (Week 1-2)
1. Set up EventBridge event bus
2. Create Lambda function for ingestion
3. Configure SQS queue
4. Test with sample events
5. **Deliverable:** Events flowing from sources to SQS

### Phase 2: Database Migration (Week 2-3)
1. Set up RDS PostgreSQL instance
2. Create database schema
3. Migrate CSV data to RDS
4. Update CrewAI agents to write to RDS
5. Test end-to-end flow
6. **Deliverable:** Tickets stored in RDS instead of CSV

### Phase 3: Metrics Migration (Week 3-4)
1. Set up DynamoDB tables
2. Migrate metrics calculation to DynamoDB
3. Update analytics queries
4. **Deliverable:** Metrics in DynamoDB

### Phase 4: ECS Deployment (Week 4-5)
1. Containerize CrewAI agents
2. Create ECS task definition
3. Set up ECS Fargate service
4. Configure auto-scaling
5. Test processing pipeline
6. **Deliverable:** Processing running on ECS

### Phase 5: Frontend Deployment (Week 5-6)
1. Containerize Streamlit app
2. Deploy to ECS Fargate
3. Set up ALB
4. Configure CloudFront
5. Update API endpoints
6. **Deliverable:** Frontend accessible via CloudFront

### Phase 6: Monitoring & Optimization (Week 6-7)
1. Set up CloudWatch dashboards
2. Configure alarms
3. Set up X-Ray tracing
4. Performance testing
5. Cost optimization
6. **Deliverable:** Production-ready system with monitoring

## Cost Estimation (Monthly)

### Small Scale (~100 feedback items/day)
- **EventBridge:** $1 (first 1M events free)
- **Lambda:** $5 (1M requests, 400K GB-seconds)
- **SQS:** $1 (first 1M requests free)
- **ECS Fargate:** $30 (1 task, 2 vCPU, 4GB, 50% utilization)
- **RDS PostgreSQL:** $50 (db.t3.small, single-AZ)
- **DynamoDB:** $5 (on-demand, minimal usage)
- **S3:** $2 (storage + requests)
- **ALB:** $20 (standard ALB)
- **CloudFront:** $5 (minimal traffic)
- **Data Transfer:** $5
- **Total:** ~$124/month

### Medium Scale (~1,000 feedback items/day)
- **EventBridge:** $5
- **Lambda:** $20
- **SQS:** $5
- **ECS Fargate:** $150 (2-3 tasks average)
- **RDS PostgreSQL:** $150 (db.t3.medium, multi-AZ)
- **DynamoDB:** $20
- **S3:** $10
- **ALB:** $20
- **CloudFront:** $20
- **Data Transfer:** $20
- **Total:** ~$430/month

### Large Scale (~10,000+ feedback items/day)
- **EventBridge:** $50
- **Lambda:** $100
- **SQS:** $50
- **ECS Fargate:** $500 (5-10 tasks average)
- **RDS PostgreSQL:** $500 (db.r5.large, multi-AZ + read replicas)
- **DynamoDB:** $100
- **S3:** $50
- **ALB:** $20
- **CloudFront:** $100
- **Data Transfer:** $100
- **Total:** ~$1,590/month

## Security Considerations

1. **Network Security:**
   - VPC with private subnets for ECS and RDS
   - Security groups with least privilege
   - NAT Gateway for outbound internet access

2. **Data Security:**
   - Encryption at rest (RDS, S3, DynamoDB)
   - Encryption in transit (TLS/SSL)
   - Secrets Manager for API keys and credentials

3. **Access Control:**
   - IAM roles with least privilege
   - API Gateway authentication
   - RDS database users with restricted permissions

4. **Compliance:**
   - CloudTrail for audit logging
   - VPC Flow Logs for network monitoring
   - GuardDuty for threat detection

## High Availability & Disaster Recovery

1. **Multi-AZ Deployment:**
   - RDS in multiple availability zones
   - ECS tasks across multiple AZs
   - ALB with health checks

2. **Backup Strategy:**
   - RDS automated backups (7-day retention)
   - S3 versioning and lifecycle policies
   - Cross-region replication for critical data

3. **Disaster Recovery:**
   - RDS snapshots to S3
   - Infrastructure as Code (Terraform/CloudFormation)
   - Runbook for recovery procedures
