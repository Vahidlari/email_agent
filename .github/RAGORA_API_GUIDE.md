# Ragora API Guide for Email Assistant Agent

This guide provides instructions for implementing an email assistant agent using the **Ragora** package library.

## Table of Contents
- [Overview](#overview)
- [Setup and Installation](#setup-and-installation)
- [Ragora API Reference](#ragora-api-reference)
- [Email Assistant Implementation](#email-assistant-implementation)
- [Usage Examples](#usage-examples)
- [Testing and Development](#testing-and-development)
- [Resources](#resources)

## Overview

**Ragora** is a Retrieval-Augmented Generation (RAG) framework that connects language models to real, reliable knowledge bases. It provides:

- Specialized document processing capabilities (including email handling)
- Flexible search modes
- Vector storage via Weaviate
- Performance optimization features
- Clean, composable interface

### Key Features for Email Assistant
- Native email document processing
- Vector-based email search and retrieval
- Knowledge base management
- Grounding pipelines for context-aware responses

## Setup and Installation

### Prerequisites
- Python 3.11 or higher
- Weaviate vector database instance

### Installation Steps

1. **Install Ragora Package**
   ```bash
   pip install ragora
   ```

2. **Install Additional Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Weaviate Database**
   
   Download and start the Weaviate server:
   ```bash
   wget https://github.com/Vahidlari/aiApps/releases/download/v1.0.0/database_server-1.0.0.tar.gz
   tar -xzf database_server-1.0.0.tar.gz
   cd database-server
   ./start.sh
   ```
   
   Or use Docker:
   ```bash
   docker run -d -p 8080:8080 semitechnologies/weaviate:1.22.0
   ```

4. **Environment Configuration**
   
   Create a `.env` file or set environment variables:
   ```bash
   WEAVIATE_URL=http://localhost:8080
   OPENAI_API_KEY=your_api_key_here
   ```

## Ragora API Reference

### Primary API Documentation
**Reference:** [Ragora API Reference](https://github.com/Vahidlari/aiApps/blob/v1.0.0/ragora/docs/api_reference.md)

For detailed API documentation, including:
- Core classes and methods
- Document processing functions
- Search and retrieval APIs
- Email-specific handling
- Configuration options

Refer to the official API reference document linked above.

### Key Ragora Components

#### 1. Knowledge Base Management
```python
from ragora import KnowledgeBase

# Initialize knowledge base
kb = KnowledgeBase(
    name="email_knowledge_base",
    weaviate_url="http://localhost:8080"
)
```

#### 2. Document Processing
```python
from ragora import DocumentProcessor

# Process email documents
processor = DocumentProcessor()
processed_emails = processor.process_emails(email_files)
```

#### 3. Search and Retrieval
```python
from ragora import SearchEngine

# Initialize search engine
search_engine = SearchEngine(knowledge_base=kb)

# Search emails
results = search_engine.search(
    query="meeting request from last week",
    search_mode="hybrid"  # semantic, keyword, or hybrid
)
```

#### 4. RAG Pipeline
```python
from ragora import RAGPipeline

# Create RAG pipeline
pipeline = RAGPipeline(
    knowledge_base=kb,
    model="gpt-4"
)

# Generate context-aware responses
response = pipeline.generate(
    query="What was discussed in the team meeting?",
    context=retrieved_emails
)
```

## Email Assistant Implementation

### Architecture

The email assistant agent should follow this structure:

```
email_agent/
├── emailprofilemanager/
│   ├── email_loader.py      # Load and parse emails
│   ├── email_processor.py   # Process with Ragora
│   ├── email_search.py      # Search functionality
│   └── assistant.py         # Main assistant agent
├── tests/
│   └── test_email_assistant.py
├── requirements.txt
└── .env
```

### Implementation Steps

#### Step 1: Email Loading Module
Create `emailprofilemanager/email_loader.py`:
- Load emails from various sources (files, API, IMAP)
- Parse email metadata (sender, subject, date, body)
- Extract attachments if needed

#### Step 2: Email Processing Module
Create `emailprofilemanager/email_processor.py`:
- Initialize Ragora Knowledge Base
- Process emails using Ragora DocumentProcessor
- Store processed emails in Weaviate
- Handle email-specific metadata

#### Step 3: Search Module
Create `emailprofilemanager/email_search.py`:
- Implement search functionality using Ragora SearchEngine
- Support multiple search modes (semantic, keyword, hybrid)
- Filter by date, sender, subject, etc.
- Rank and return relevant results

#### Step 4: Assistant Agent
Create `emailprofilemanager/assistant.py`:
- Integrate RAG pipeline for context-aware responses
- Handle user queries about emails
- Generate summaries and insights
- Provide email recommendations and actions

### Integration Example

```python
from emailprofilemanager.email_loader import EmailLoader
from emailprofilemanager.email_processor import EmailProcessor
from emailprofilemanager.email_search import EmailSearch
from emailprofilemanager.assistant import EmailAssistant

# Initialize components
loader = EmailLoader()
processor = EmailProcessor(kb_url="http://localhost:8080")
search_engine = EmailSearch(processor.knowledge_base)
assistant = EmailAssistant(search_engine)

# Load and process emails
emails = loader.load_from_directory("emails/")
processor.process_and_store(emails)

# Use assistant to answer queries
response = assistant.query("Show me emails about project deadlines")
print(response)
```

## Usage Examples

### Basic Email Search
```python
# Search for specific content
results = search_engine.search(
    query="quarterly review meeting",
    limit=10,
    filters={"date": "2024-01-01"}
)

for email in results:
    print(f"From: {email['sender']}")
    print(f"Subject: {email['subject']}")
    print(f"Date: {email['date']}")
    print(f"Relevance: {email['score']}")
```

### Generate Email Summary
```python
# Get summary of recent emails
summary = assistant.summarize_emails(
    start_date="2024-01-01",
    end_date="2024-01-31",
    topic="project updates"
)
print(summary)
```

### Find Similar Emails
```python
# Find similar emails to a reference
similar = assistant.find_similar(
    reference_email_id="123",
    top_k=5
)
```

### Answer Questions About Emails
```python
# Ask questions about email content
answer = assistant.ask(
    question="What action items were mentioned in yesterday's emails?",
    use_context=True
)
```

## Testing and Development

### Running Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=emailprofilemanager tests/

# Run specific test
pytest tests/test_email_assistant.py::test_search_functionality
```

### Test Structure
```python
# tests/test_email_assistant.py
def test_email_loading():
    """Test email loading functionality"""
    pass

def test_email_processing():
    """Test Ragora email processing"""
    pass

def test_search_functionality():
    """Test email search with Ragora"""
    pass

def test_assistant_query():
    """Test assistant query handling"""
    pass
```

### Development Environment
```bash
# Install in development mode
pip install -e .

# Install dev dependencies
pip install -r requirements-dev.txt

# Run linter
flake8 emailprofilemanager/

# Run formatter
black emailprofilemanager/
```

## Resources

### Official Documentation
- **Ragora API Reference:** https://github.com/Vahidlari/aiApps/blob/v1.0.0/ragora/docs/api_reference.md
- **PyPI Package:** https://pypi.org/project/ragora/
- **GitHub Repository:** https://github.com/Vahidlari/aiApps

### Additional Resources
- Weaviate Documentation: https://weaviate.io/developers/weaviate
- Python IMAP Library: https://docs.python.org/3/library/imaplib.html
- Email Format (RFC 5322): https://tools.ietf.org/html/rfc5322

### Examples and Tutorials
- Check the Ragora documentation for email usage examples
- Explore example implementations in the aiApps repository
- Review email processing patterns in the community

## Next Steps

1. **Review the API Reference:** Study the official Ragora API documentation to understand all available methods and options.

2. **Set Up Development Environment:** Install all dependencies and configure Weaviate.

3. **Implement Core Modules:** Start with email loading, then processing, search, and finally the assistant agent.

4. **Write Tests:** Create comprehensive tests for each module to ensure reliability.

5. **Iterate and Improve:** Refine the implementation based on test results and API insights.

## Support

For issues, questions, or contributions:
- Open an issue on the aiApps repository
- Check the Ragora documentation
- Review example implementations in the repository

---

**Last Updated:** Based on Ragora v1.0.0 API Reference
**Documentation Link:** https://github.com/Vahidlari/aiApps/blob/v1.0.0/ragora/docs/api_reference.md

