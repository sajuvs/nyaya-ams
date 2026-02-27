# Nyaya-Flow: Agentic Legal Aid Platform

Multi-agent AI system for generating legal aid documents for Indian citizens, with focus on Kerala jurisdiction.

## Architecture

Three specialized AI agents working in collaboration:

1. **Researcher Agent** - Analyzes grievances and identifies applicable Indian laws (BNS, Consumer Protection Act, etc.)
2. **Drafter Agent** - Creates formal legal petitions following Indian legal format
3. **Expert Reviewer Agent** - Audits drafts for compliance and accuracy

**Self-Correction Loop:** Rejected drafts are automatically refined based on expert feedback (max 3 iterations).

## Quick Start

```bash
# 1. Configure environment
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# 2. Start with Docker
docker-compose up --build

# 3. Access API
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - Health: http://localhost:8000/api/v1/health
```

## API Usage

```bash
curl -X POST "http://localhost:8000/api/v1/generate-legal-aid" \
  -H "Content-Type: application/json" \
  -d '{
    "grievance": "I purchased a defective mobile phone from a shop in Kochi. The seller refuses to provide a refund despite the warranty.",
    "rag_context": ""
  }'
```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── agents/              # Three AI agents
│   │   ├── researcher.py
│   │   ├── drafter.py
│   │   └── expert_reviewer.py
│   ├── services/
│   │   └── orchestrator.py  # Multi-agent workflow
│   ├── api/v1/
│   │   └── endpoints.py     # REST API
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   └── tests/
│       └── test_orchestrator.py
├── src/                     # RAG components
└── docustore/              # Legal documents
```

## Testing

```bash
# Quick test (no API calls)
cd backend
python test_imports.py

# Full agent test (requires OPENAI_API_KEY)
python test_agents.py

# Unit tests
pytest app/tests/ -v

# Run example
python example_usage.py
```

See [TESTING.md](TESTING.md) for detailed testing guide.

## Response Structure

The API returns complete agent traces for visualization:

```json
{
  "final_document": "To: The District Consumer Forum...",
  "research_findings": {
    "legal_provisions": ["Consumer Protection Act 2019, Section 35"],
    "merits_score": 8
  },
  "agent_traces": [
    {
      "agent": "researcher",
      "action": "analyzing_grievance",
      "details": "Scanning legal provisions...",
      "timestamp": "2026-02-27T10:00:00"
    }
  ],
  "iterations": 1,
  "status": "approved"
}
```

## Technology Stack

- FastAPI + Uvicorn
- OpenAI GPT-4.1 (for multi-agent system)
- Groq LLM (for RAG search)
- LangChain for orchestration
- FAISS for vector store
- Docker for deployment

## Environment Variables

```bash
OPENAI_API_KEY=your_openai_api_key_here  # Required for agents
GROQ_API_KEY=your_groq_api_key_here      # Required for RAG
HF_TOKEN=your_hf_token_here              # Optional
```
Nyaya-Ams - Agentic Legal Aid Platform

## Overview
Nyaya-Flow is an Agentic Legal Aid Platform that uses RAG (Retrieval-Augmented Generation) to provide legal assistance based on Indian statutes and Kerala-specific jurisdiction.

## Prerequisites
- Python 3.11+
- Docker & Docker Compose (optional)
- Git

## Local Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd nyaya-ams
```

### 2. Setup Environment Variables
```bash
cp .env.example .env
# Edit .env and add your API keys:
# GROQ_API_KEY=your_groq_api_key
# HF_TOKEN=your_huggingface_token
```

### 3. Install Dependencies

**Using uv (recommended):**
```bash
uv sync
```

**Using pip:**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Add PDF Documents
Place your legal PDF documents in:
```
backend/docustore/pdf/
```

### 5. Build Vector Store (First Time Only)
Uncomment the build line in `backend/app.py`:
```python
store.build_from_documents(docs)  # Uncomment this line
```

Then run:
```bash
cd backend
python app.py
```

After first run, comment it back to use the cached embeddings.

### 6. Run Application
```bash
cd backend
python app.py
```

## Docker Setup

### 1. Setup Environment
```bash
cp .env.example .env
# Add your API keys to .env
```

### 2. Build and Run
```bash
docker-compose up --build
```

### 3. Stop
```bash
docker-compose down
```

## Project Structure
```
nyaya-ams/
├── backend/
│   ├── src/
│   │   ├── data_loader.py    # Document loading
│   │   ├── embedding.py      # Text chunking & embeddings
│   │   ├── vectorstore.py    # FAISS vector store
│   │   └── search.py         # RAG search & summarization
│   ├── tests/                # Test suite
│   ├── docustore/pdf/        # PDF documents
│   ├── data/faiss_store/     # Vector embeddings (generated)
│   └── app.py                # Main application
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Running Tests
```bash
cd backend
pytest tests/ -v
```

## API Keys
- **GROQ_API_KEY**: Get from https://console.groq.com/keys
- **HF_TOKEN**: Get from https://huggingface.co/settings/tokens

## Backup
Create a backup:
```bash
./backup.sh
```
Backup saved to `../backups/` 
