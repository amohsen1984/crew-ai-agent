# Demo Script - Intelligent User Feedback Analysis System

## Pre-Recording Checklist
- [ ] Docker containers running (`docker-compose up`)
- [ ] Browser open to http://localhost:8501
- [ ] Terminal with `docker-compose logs -f` running
- [ ] Sample data files in `data/` directory
- [ ] Screen recording software ready
- [ ] Microphone tested

---

## Section 1: Introduction (2 minutes)

**[Screen: Show project repository in IDE]**

"Hello, and welcome to this demonstration of the Intelligent User Feedback Analysis System. This is a multi-agent AI system built with CrewAI that automatically processes app store reviews and support emails into structured tickets, replacing manual triaging that typically takes one to two hours per day."

**[Switch to browser showing dashboard]**

"The system consists of a FastAPI backend that handles feedback processing using CrewAI agents, and a Streamlit frontend dashboard for visualization and configuration. Both components are containerized with Docker for easy deployment."

**[Show project structure briefly]**

"The tech stack includes CrewAI for multi-agent orchestration, OpenAI GPT-4 as the LLM backend, FastAPI for the REST API, Streamlit for the dashboard, and Docker for containerization. This combination provides a scalable, production-ready solution for automated feedback processing."

---

## Section 2: Architecture (3 minutes)

**[Show architecture diagram]**

"Let me walk you through the system architecture. The frontend Streamlit dashboard communicates with the FastAPI backend via REST API calls. The backend orchestrates a pipeline of seven specialized AI agents using CrewAI."

**[Show agent pipeline diagram]**

"The processing pipeline consists of seven agents working in sequence:

1. **CSV Reader Agent** - Reads and normalizes feedback data from CSV files
2. **Feedback Classifier Agent** - Categorizes feedback into Bug, Feature Request, Praise, Complaint, or Spam
3. **Bug Analyzer Agent** - Extracts technical details and assesses severity for bug reports
4. **Feature Extractor Agent** - Analyzes feature requests for impact and user needs
5. **Ticket Creator Agent** - Generates structured tickets with consistent formatting
6. **Quality Critic Agent** - Reviews tickets for completeness and accuracy
7. **Fallback Agent** - Handles failures and ensures no feedback is lost

Each agent has a specific role and expertise, ensuring high-quality output at each stage."

**[Show data flow]**

"The system processes feedback from two sources: app store reviews and support emails, both stored as CSV files. The agents process this data through the pipeline, generating structured tickets, processing logs, and metrics as output."

---

## Section 3: Main Features Demonstration (8-10 minutes)

### 3.1 Dashboard & Starting Process (2 minutes)

**[Screen: Browser showing dashboard]**

"Let's start by exploring the main dashboard. Here we can see summary cards showing total tickets, bugs found, features requested, critical priority items, high priority items, and average confidence scores."

**[Scroll down]**

"The dashboard also provides quick filters by category, priority, and status, as well as a table of recent tickets and a category distribution chart."

**[Point to sidebar]**

"In the sidebar, we have the processing status indicator and a button to start processing feedback."

**[Click "Process Feedback" button]**

"Let me start a processing run. When I click 'Process Feedback', the system will begin processing all feedback items in the data directory."

**[Switch to show Docker logs]**

"As you can see in the Docker logs, the backend has received the processing request and is starting the CrewAI pipeline. The system loads feedback items from the CSV files and begins parallel processing with up to three workers to optimize throughput while respecting API rate limits."

**[Switch back to browser]**

"Back in the UI, we can see the processing status has changed to 'Pending' and then 'Running', with a progress bar showing the current progress percentage."

### 3.2 Tracking Progress (1.5 minutes)

**[Show progress bar updating]**

"The progress bar updates in real-time, showing the percentage of items completed. The system polls the backend every five seconds for status updates."

**[Show Docker logs]**

"In the Docker logs, we can see each agent working through the feedback items. The CSV Reader loads the data, the Classifier categorizes each item, and specialized agents analyze bugs and feature requests. Each successful processing is logged with the source ID."

**[Wait for completion]**

"As processing completes, we can see the final metrics being calculated and written to the output files. The status indicator changes to 'Completed' with a success message."

**[Show updated dashboard]**

"Now the dashboard reflects the newly processed tickets, with updated counts and statistics."

### 3.3 Configuration - Categorizing & Priority Rules (2 minutes)

**[Navigate to Configuration tab]**

"One of the key features of this system is the ability to configure how feedback is categorized and prioritized. Let's explore the Configuration panel."

**[Show Bug Priority Rules]**

"Here we have priority rules for different categories. Let's look at Bug priority rules. We can set a default priority - in this case, Medium - and define keywords that trigger different priority levels."

**[Expand Bug rules]**

"For example, if a bug report contains keywords like 'data loss', 'unusable', or 'app won't start', it will be escalated to Critical priority. Keywords like 'crash', 'freeze', or 'not responding' trigger High priority."

**[Modify keywords]**

"Let me add a new keyword to the critical list - say 'security breach' - and save the rules."

**[Click Save]**

"When I save these rules, they're sent to the backend and persisted. These rules will be applied in the next processing run, ensuring that tickets matching these keywords are automatically prioritized correctly."

**[Show Feature Request rules]**

"Similarly, we can configure priority rules for Feature Requests. By default, feature requests start at Low priority, but we can define keywords that escalate them to Medium or High based on user demand signals."

**[Show Complaint rules]**

"And for Complaints, we can prioritize payment-related issues or billing problems as High priority, while general pricing concerns remain Medium."

### 3.4 Configuration - Threshold Impact (1.5 minutes)

**[Show Classification Threshold slider]**

"Another important configuration is the Classification Threshold. This slider controls the minimum confidence score required for a classification to be accepted."

**[Explain threshold]**

"At 0.5, the system is more lenient and will accept classifications with lower confidence. At 0.9, the system is very strict and only accepts high-confidence classifications."

**[Change threshold]**

"Currently, it's set to 0.7, which is a balanced default. If I increase it to 0.8, the system will be more conservative, potentially rejecting some borderline cases that would have been accepted at 0.7."

"This threshold affects the trade-off between false positives and false negatives. A lower threshold means more items get classified but potentially with lower accuracy. A higher threshold means fewer items get classified but with higher confidence."

"The threshold setting is stored in session state and will be used for the next processing run."

### 3.5 Analytics Dashboard (1 minute)

**[Navigate to Analytics tab]**

"Now let's look at the Analytics dashboard, which provides insights into the processed feedback."

**[Show pie chart]**

"Here we have a pie chart showing the distribution of classifications - how many bugs, feature requests, praise, complaints, and spam items were found."

**[Show bar chart]**

"This bar chart shows the priority distribution - how many tickets are Critical, High, Medium, or Low priority."

**[Show histogram]**

"The confidence score histogram shows the distribution of classification confidence scores. Most items should cluster around higher confidence values, indicating reliable classifications."

**[Show summary stats]**

"And here are summary statistics including total tickets processed, average confidence, and the last processing run metrics."

### 3.6 Quality Metrics (QA Comparison) (2 minutes)

**[Navigate to QA tab]**

"One of the most important features is the Quality Assurance comparison, which measures how well the system performs against expected classifications."

**[Show accuracy summary]**

"At the top, we see accuracy metrics: Category Accuracy, Priority Accuracy, and Full Match Accuracy. These compare the system's output against a ground truth file - expected_classifications.csv."

**[Show category accuracy chart]**

"This bar chart shows accuracy broken down by category. We can see which categories the system handles well and which need improvement."

**[Show confusion matrix]**

"The confusion matrix is particularly useful. It shows where the system makes mistakes - for example, if bugs are sometimes misclassified as feature requests, or vice versa. The diagonal represents correct classifications."

**[Show priority accuracy]**

"Similarly, we have priority accuracy metrics showing how well the system assigns priorities compared to expected values."

**[Show comparison table]**

"Finally, the detailed comparison table shows each feedback item side-by-side with expected and actual classifications. We can filter to show only mismatches to identify patterns in errors."

"This QA functionality is crucial for continuous improvement - by analyzing mismatches, we can refine agent prompts, adjust priority rules, or improve classification logic."

---

## Section 4: Production Deployment to AWS (3-4 minutes)

### 4.1 Current Architecture Limitations (30 seconds)

**[Show current architecture]**

"The current implementation uses CSV files for storage and processing, which works well for demonstration and small-scale use. However, for production deployment, we need a more scalable, event-driven architecture."

**[List limitations]**

"CSV-based storage has limitations: it doesn't support real-time event processing, has limited scalability, and requires manual file management. For production, we need to handle events as they arrive and store data in a proper database."

### 4.2 AWS Production Architecture (2 minutes)

**[Show AWS architecture diagram]**

"Here's a high-level architecture for deploying this system to AWS. Let me walk through the components:"

**[Point to event sources]**

"Feedback arrives from multiple sources: App Store reviews can be ingested via S3 or API Gateway, support emails come through Amazon SES, and we can add webhook endpoints for other integrations."

**[Point to EventBridge]**

"All events are routed through Amazon EventBridge, which acts as a central event bus. This decouples event sources from processing logic."

**[Point to Lambda]**

"An AWS Lambda function handles initial ingestion - it validates events and enqueues them to an SQS queue for buffering and reliability."

**[Point to SQS]**

"Amazon SQS provides a buffer between event ingestion and processing, ensuring we can handle traffic spikes and providing retry capabilities."

**[Point to ECS Fargate]**

"The actual processing happens in ECS Fargate tasks running our CrewAI agents. These tasks consume messages from SQS, process feedback through the agent pipeline, and write results to the database."

**[Point to RDS]**

"Amazon RDS PostgreSQL stores all structured ticket data, providing ACID compliance, relationships, and query capabilities that CSV files can't offer."

**[Point to DynamoDB]**

"DynamoDB stores metrics and analytics data, optimized for fast reads and time-series queries."

**[Point to S3]**

"S3 stores processing logs, artifacts, and any large files generated during processing."

**[Point to frontend]**

"The Streamlit frontend runs on ECS Fargate behind an Application Load Balancer, with CloudFront CDN for static assets. This provides scalability and high availability."

### 4.3 Component Details (1 minute)

**[Explain event flow]**

"The event flow is straightforward: events arrive, get validated by Lambda, queued in SQS, processed by ECS tasks, and results are stored in RDS and DynamoDB."

**[Explain scaling]**

"ECS Fargate can auto-scale based on SQS queue depth, ensuring we process events quickly even during traffic spikes. CloudWatch monitors the entire pipeline and can trigger alerts for errors or performance issues."

**[Explain data access]**

"The frontend queries RDS for ticket data and DynamoDB for metrics, providing real-time dashboards and analytics."

### 4.4 Migration Strategy (30 seconds)

**[Show migration phases]**

"The migration can be done in phases:

1. Replace CSV reader with EventBridge listener
2. Migrate ticket storage to RDS PostgreSQL
3. Move metrics to DynamoDB
4. Deploy ECS Fargate with auto-scaling
5. Add CloudWatch monitoring and alerts

This phased approach minimizes risk and allows testing at each stage."

---

## Section 5: Closing (1 minute)

**[Return to dashboard]**

"To summarize, this Intelligent User Feedback Analysis System provides:

- **Automated processing** that saves 1-2 hours per day of manual triaging
- **Multi-agent architecture** that ensures quality and accuracy through specialized agents
- **Configurable rules** for categorization and prioritization
- **Real-time tracking** of processing progress
- **Comprehensive analytics** and quality metrics
- **Production-ready AWS architecture** designed for scalability"

**[Show architecture diagram again]**

"The system is designed to be both powerful and flexible - you can adjust priority rules, classification thresholds, and agent behavior to match your specific needs."

**[Final screen]**

"Thank you for watching this demonstration. The codebase is available in the repository, and I'm happy to answer any questions about the implementation or AWS deployment strategy."

---

## Post-Recording Notes

- Add transitions between sections
- Include close-ups of important UI elements
- Add text overlays for key points
- Include timestamps in final video
- Add background music (optional, low volume)
