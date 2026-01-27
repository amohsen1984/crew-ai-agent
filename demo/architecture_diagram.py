#!/usr/bin/env python3
"""Generate architecture diagrams for the demo."""

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import ECS, Lambda
from diagrams.aws.database import RDS, Dynamodb, S3
from diagrams.aws.integration import SQS, Eventbridge, SNS
from diagrams.aws.network import CloudFront, ALB, APIGateway
from diagrams.aws.storage import SimpleStorageServiceS3
from diagrams.onprem.client import User
from diagrams.programming.language import Python
from diagrams.onprem.container import Docker
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.inmemory import Redis
from diagrams.custom import Custom
import os

def create_current_architecture():
    """Create diagram of current architecture."""
    with Diagram("Current Architecture - CSV-Based", filename="demo/diagrams/current_architecture", show=False, direction="LR"):
        csv_files = Custom("CSV Files\n(app_store_reviews.csv\nsupport_emails.csv)", "./diagrams/csv.png")
        
        with Cluster("Docker Containers"):
            frontend = Docker("Streamlit\nFrontend\n:8501")
            backend = Docker("FastAPI\nBackend\n:8001")
        
        with Cluster("CrewAI Agents"):
            csv_reader = Python("CSV Reader")
            classifier = Python("Classifier")
            bug_analyzer = Python("Bug Analyzer")
            feature_extractor = Python("Feature Extractor")
            ticket_creator = Python("Ticket Creator")
            quality_critic = Python("Quality Critic")
            fallback = Python("Fallback")
        
        output_files = Custom("Output Files\n(generated_tickets.csv\nmetrics.csv\nprocessing_log.csv)", "./diagrams/csv.png")
        
        csv_files >> csv_reader
        csv_reader >> classifier
        classifier >> bug_analyzer
        classifier >> feature_extractor
        bug_analyzer >> ticket_creator
        feature_extractor >> ticket_creator
        ticket_creator >> quality_critic
        quality_critic >> output_files
        
        User("User") >> frontend
        frontend >> backend
        backend >> csv_reader
        output_files >> frontend

def create_agent_pipeline():
    """Create diagram of agent pipeline."""
    with Diagram("Agent Processing Pipeline", filename="demo/diagrams/agent_pipeline", show=False, direction="LR"):
        csv_input = Custom("CSV Input\n(app_store_reviews.csv\nsupport_emails.csv)", "./diagrams/csv.png")
        
        csv_reader = Python("1. CSV Reader\nData Ingestion")
        classifier = Python("2. Classifier\nCategorization")
        
        with Cluster("Specialized Analysis"):
            bug_analyzer = Python("3. Bug Analyzer\nTechnical Details")
            feature_extractor = Python("4. Feature Extractor\nImpact Assessment")
        
        ticket_creator = Python("5. Ticket Creator\nStructured Output")
        quality_critic = Python("6. Quality Critic\nQA Review")
        fallback = Python("7. Fallback\nError Handling")
        
        output = Custom("Output\n(generated_tickets.csv\nmetrics.csv)", "./diagrams/csv.png")
        
        csv_input >> csv_reader
        csv_reader >> classifier
        classifier >> bug_analyzer
        classifier >> feature_extractor
        bug_analyzer >> ticket_creator
        feature_extractor >> ticket_creator
        ticket_creator >> quality_critic
        quality_critic >> output
        classifier - Edge(style="dashed", color="red") >> fallback
        bug_analyzer - Edge(style="dashed", color="red") >> fallback
        feature_extractor - Edge(style="dashed", color="red") >> fallback
        ticket_creator - Edge(style="dashed", color="red") >> fallback
        fallback >> output

def create_aws_architecture():
    """Create AWS production architecture diagram."""
    with Diagram("AWS Production Architecture", filename="demo/diagrams/aws_architecture", show=False, direction="TB"):
        with Cluster("Event Sources"):
            app_store = Custom("App Store\nReviews", "./diagrams/app_store.png")
            emails = Custom("Support\nEmails", "./diagrams/email.png")
            webhooks = APIGateway("Webhook\nEndpoints")
        
        with Cluster("Event Ingestion"):
            eventbridge = Eventbridge("EventBridge\nEvent Bus")
            ses = Custom("Amazon SES\n(Email)", "./diagrams/ses.png")
            s3_ingest = SimpleStorageServiceS3("S3 Bucket\n(Reviews)")
        
        with Cluster("Processing Layer"):
            lambda_ingest = Lambda("Lambda\n(Ingestion)")
            sqs = SQS("SQS Queue\n(Buffering)")
            
            with Cluster("ECS Fargate"):
                crew_agents = ECS("CrewAI\nAgents")
        
        with Cluster("Data Storage"):
            rds = RDS("RDS PostgreSQL\n(Tickets)")
            dynamodb = Dynamodb("DynamoDB\n(Metrics)")
            s3_artifacts = SimpleStorageServiceS3("S3\n(Logs/Artifacts)")
        
        with Cluster("Frontend"):
            alb = ALB("Application\nLoad Balancer")
            cdn = CloudFront("CloudFront\nCDN")
            streamlit = ECS("Streamlit\nDashboard")
        
        user = User("Users")
        
        # Event flow
        app_store >> s3_ingest
        emails >> ses
        s3_ingest >> eventbridge
        ses >> eventbridge
        webhooks >> eventbridge
        
        eventbridge >> lambda_ingest
        lambda_ingest >> sqs
        sqs >> crew_agents
        
        crew_agents >> rds
        crew_agents >> dynamodb
        crew_agents >> s3_artifacts
        
        user >> cdn
        cdn >> alb
        alb >> streamlit
        streamlit >> rds
        streamlit >> dynamodb

def create_data_flow():
    """Create data flow diagram."""
    with Diagram("Data Flow", filename="demo/diagrams/data_flow", show=False, direction="LR"):
        input_data = Custom("Input Data\nCSV Files", "./diagrams/csv.png")
        
        with Cluster("Processing"):
            normalize = Python("Normalize")
            classify = Python("Classify")
            analyze = Python("Analyze")
            create = Python("Create Ticket")
            review = Python("Review")
        
        with Cluster("Output"):
            tickets = Custom("Tickets\nCSV", "./diagrams/csv.png")
            metrics = Custom("Metrics\nCSV", "./diagrams/csv.png")
            logs = Custom("Logs\nCSV", "./diagrams/csv.png")
        
        input_data >> normalize
        normalize >> classify
        classify >> analyze
        analyze >> create
        create >> review
        review >> tickets
        review >> metrics
        review >> logs

if __name__ == "__main__":
    # Create diagrams directory
    os.makedirs("demo/diagrams", exist_ok=True)
    
    print("Generating architecture diagrams...")
    try:
        create_current_architecture()
        print("✓ Current architecture diagram created")
    except Exception as e:
        print(f"✗ Error creating current architecture: {e}")
    
    try:
        create_agent_pipeline()
        print("✓ Agent pipeline diagram created")
    except Exception as e:
        print(f"✗ Error creating agent pipeline: {e}")
    
    try:
        create_aws_architecture()
        print("✓ AWS architecture diagram created")
    except Exception as e:
        print(f"✗ Error creating AWS architecture: {e}")
    
    try:
        create_data_flow()
        print("✓ Data flow diagram created")
    except Exception as e:
        print(f"✗ Error creating data flow: {e}")
    
    print("\nAll diagrams generated in demo/diagrams/")
