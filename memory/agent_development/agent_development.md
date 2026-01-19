# CrewAI Agent Development Best Practices

This document provides standards and best practices for building AI agents using CrewAI framework.

## Agent Definition Principles

### The Role-Goal-Backstory Triad

Every agent must have three foundational attributes that shape its behavior:

1. **Role**: Defines the agent's function and expertise within the crew
   - Be specific: "Senior Data Researcher" not "Researcher"
   - Include domain expertise: "{topic} Bug Analysis Specialist"
   - Match organizational roles when possible

2. **Goal**: The individual objective guiding decision-making
   - Make it measurable and outcome-focused
   - Align with the agent's role capabilities
   - Example: "Extract technical details including steps to reproduce, platform info, and severity assessment"

3. **Backstory**: Provides context and personality
   - Enriches decision-making through context
   - Establishes expertise and experience level
   - Example: "You're a seasoned QA engineer with 10 years of experience triaging bug reports across mobile platforms"

### YAML Configuration (Recommended)

Use YAML for maintainability. Define agents in `config/agents.yaml`:

```yaml
feedback_classifier:
  role: "Senior Feedback Classification Specialist"
  goal: "Accurately categorize user feedback into Bug, Feature Request, Praise, Complaint, or Spam with high confidence scores"
  backstory: >
    You are an expert in natural language processing with years of experience
    analyzing customer feedback for SaaS products. You understand the nuances
    between a frustrated user reporting a bug versus requesting a feature.
    You never misclassify critical bugs as low-priority items.
```

### Code-Based Definition

For dynamic agent creation:

```python
from crewai import Agent

bug_analyst = Agent(
    role="Bug Analysis Specialist",
    goal="Extract technical details from bug reports including reproduction steps, platform info, and severity",
    backstory="You're a senior QA engineer who has triaged thousands of bug reports...",
    tools=[search_tool, file_read_tool],
    memory=True,
    verbose=True,
    max_iter=20,
    max_retry_limit=2
)
```

## Execution Control Parameters

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `max_iter` | 20 | Maximum reasoning iterations before stopping |
| `max_rpm` | None | Rate limit for API calls |
| `max_execution_time` | None | Timeout in seconds |
| `max_retry_limit` | 2 | Retries on error |
| `respect_context_window` | True | Auto-summarize to fit token limits |

### Guidelines:
- Set `max_iter` based on task complexity (simple: 10, complex: 25+)
- Always set `max_rpm` in production to prevent rate limiting
- Use `max_execution_time` for time-sensitive operations

## Tool Integration

### Creating Custom Tools

**Decorator Pattern (Simple Tools):**

```python
from crewai.tools import tool

@tool("Read CSV File")
def read_csv_tool(file_path: str) -> str:
    """Reads and parses a CSV file, returning structured data for analysis."""
    import pandas as pd
    df = pd.read_csv(file_path)
    return df.to_string()
```

**Class Pattern (Complex Tools):**

```python
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

class CSVWriterInput(BaseModel):
    file_path: str = Field(..., description="Path to output CSV file")
    data: str = Field(..., description="JSON string of data to write")

class CSVWriterTool(BaseTool):
    name: str = "Write CSV File"
    description: str = "Writes structured data to a CSV file for ticket logging"
    args_schema: Type[BaseModel] = CSVWriterInput

    def _run(self, file_path: str, data: str) -> str:
        import pandas as pd
        import json
        df = pd.DataFrame(json.loads(data))
        df.to_csv(file_path, index=False)
        return f"Successfully wrote {len(df)} rows to {file_path}"
```

### Tool Assignment Best Practices

- Assign only relevant tools to each agent
- Keep tools focused and single-purpose
- Write clear descriptions - agents select tools based on descriptions
- Implement caching for expensive operations

```python
agent = Agent(
    role="Ticket Creator",
    tools=[csv_writer_tool, template_tool],  # Only what's needed
    verbose=True
)
```

## Task Definition

### Core Task Attributes

```python
from crewai import Task

classification_task = Task(
    description="""
    Analyze the following user feedback and classify it into one category:
    - Bug: Technical issues, crashes, errors
    - Feature Request: New functionality suggestions
    - Praise: Positive feedback
    - Complaint: Non-technical dissatisfaction
    - Spam: Irrelevant or promotional content

    Feedback: {feedback_text}
    Source: {source_type}
    """,
    expected_output="""
    A JSON object with:
    - category: string (Bug|Feature Request|Praise|Complaint|Spam)
    - confidence: float (0.0-1.0)
    - reasoning: string explaining the classification
    """,
    agent=classifier_agent,
    output_json=ClassificationResult  # Pydantic model for validation
)
```

### Task Dependencies with Context

```python
analysis_task = Task(
    description="Analyze the classified bug report for technical details",
    expected_output="Structured bug analysis with reproduction steps",
    agent=bug_analyst,
    context=[classification_task]  # Receives output from classification
)
```

### Output Validation with Pydantic

```python
from pydantic import BaseModel, Field
from typing import Optional

class TicketOutput(BaseModel):
    ticket_id: str = Field(..., description="Unique ticket identifier")
    title: str = Field(..., description="Concise ticket title")
    category: str = Field(..., description="Bug|Feature Request|Praise|Complaint")
    priority: str = Field(..., description="Critical|High|Medium|Low")
    description: str = Field(..., description="Detailed ticket description")
    source_id: str = Field(..., description="Original feedback ID")
    technical_details: Optional[str] = Field(None, description="For bugs only")

task = Task(
    description="Create a structured ticket...",
    expected_output="Validated ticket object",
    output_pydantic=TicketOutput
)
```

## Crew Orchestration

### Process Types

**Sequential (Default):** Tasks execute one after another
```python
crew = Crew(
    agents=[reader, classifier, analyst, creator],
    tasks=[read_task, classify_task, analyze_task, create_task],
    process=Process.sequential,
    verbose=True
)
```

**Hierarchical:** Manager agent coordinates delegation
```python
crew = Crew(
    agents=[classifier, bug_analyst, feature_extractor, creator],
    tasks=[process_feedback_task],
    process=Process.hierarchical,
    manager_llm=ChatOpenAI(model="gpt-4"),
    verbose=True
)
```

### Memory Configuration

Enable memory for context retention across interactions:

```python
crew = Crew(
    agents=[...],
    tasks=[...],
    memory=True,  # Enables short-term, long-term, and entity memory
    cache=True,   # Caches tool results (default: True)
    verbose=True
)
```

### Execution Methods

```python
# Standard synchronous execution
result = crew.kickoff(inputs={"feedback_file": "reviews.csv"})

# Process multiple inputs
results = crew.kickoff_for_each(
    inputs=[
        {"feedback_file": "reviews.csv"},
        {"feedback_file": "emails.csv"}
    ]
)

# Async execution
result = await crew.akickoff(inputs={...})
```

## Error Handling Patterns

### Agent-Level Resilience

```python
agent = Agent(
    role="Data Processor",
    max_retry_limit=3,          # Retry failed operations
    max_iter=25,                # Allow more iterations for complex tasks
    respect_context_window=True # Auto-handle token limits
)
```

### Tool-Level Error Handling

```python
@tool("Safe CSV Reader")
def safe_csv_reader(file_path: str) -> str:
    """Safely reads CSV files with error handling."""
    try:
        import pandas as pd
        df = pd.read_csv(file_path)
        return df.to_json(orient='records')
    except FileNotFoundError:
        return "ERROR: File not found. Please verify the file path."
    except pd.errors.EmptyDataError:
        return "ERROR: CSV file is empty."
    except Exception as e:
        return f"ERROR: Failed to read CSV - {str(e)}"
```

### Guardrails for Output Validation

```python
from crewai import Task

task = Task(
    description="Classify the feedback",
    expected_output="Classification result",
    guardrails=[
        lambda output: output.category in ["Bug", "Feature Request", "Praise", "Complaint", "Spam"],
        lambda output: 0.0 <= output.confidence <= 1.0
    ]
)
```

## Project Structure

Recommended directory layout:

```
project/
├── config/
│   ├── agents.yaml      # Agent definitions
│   └── tasks.yaml       # Task definitions
├── src/
│   ├── crew.py          # Crew orchestration
│   ├── agents/          # Custom agent logic
│   ├── tools/           # Custom tools
│   └── models/          # Pydantic output models
├── data/
│   ├── input/           # Input CSV files
│   └── output/          # Generated tickets, logs
├── tests/
│   └── test_agents.py   # Agent unit tests
├── app.py               # Streamlit UI
└── main.py              # Entry point
```

## Testing Agents

```python
import pytest
from src.crew import FeedbackCrew

def test_bug_classification():
    crew = FeedbackCrew()
    result = crew.kickoff(inputs={
        "feedback_text": "App crashes when I try to login on iOS 17",
        "source_type": "app_store_review"
    })
    assert result.category == "Bug"
    assert result.confidence > 0.8

def test_feature_request_classification():
    crew = FeedbackCrew()
    result = crew.kickoff(inputs={
        "feedback_text": "Would love to see dark mode added",
        "source_type": "app_store_review"
    })
    assert result.category == "Feature Request"
```

## Performance Optimization

1. **Enable Caching:** Reduces redundant API calls
   ```python
   crew = Crew(..., cache=True)
   ```

2. **Set Rate Limits:** Prevent API throttling
   ```python
   agent = Agent(..., max_rpm=10)
   ```

3. **Use Async for I/O:** Non-blocking operations
   ```python
   @tool("Async Fetch")
   async def fetch_data(url: str) -> str:
       async with aiohttp.ClientSession() as session:
           async with session.get(url) as response:
               return await response.text()
   ```

4. **Batch Processing:** Process multiple items efficiently
   ```python
   results = crew.kickoff_for_each(inputs=batch_inputs)
   ```

## References

- [CrewAI Documentation](https://docs.crewai.com/)
- [CrewAI GitHub Repository](https://github.com/crewAIInc/crewAI)
- [CrewAI Tools Reference](https://docs.crewai.com/concepts/tools)
