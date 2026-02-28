# Nyaya-Flow: Agentic Legal Aid Platform

Multi-agent AI system for generating legal aid documents for Indian citizens, with focus on Kerala jurisdiction. Now includes real-time audio transcription support.

## Features

- 🤖 **Multi-Agent Legal Aid**: Three specialized AI agents for legal document generation
- 🎤 **Real-Time Transcription**: Live audio transcription using Sarvam AI
- 📚 **RAG-Powered Research**: Search local legal documents and web resources
- 🔄 **Self-Correction Loop**: Automatic draft refinement based on expert feedback
- 🌐 **WebSocket Support**: Real-time communication for transcription
- 📝 **Human-in-the-Loop**: Review and approve at each workflow stage

## Architecture

### Legal Aid Agents

Three specialized AI agents working in collaboration:

1. **Researcher Agent** - Analyzes grievances and identifies applicable Indian laws (BNS, Consumer Protection Act, etc.)
2. **Drafter Agent** - Creates formal legal petitions following Indian legal format
3. **Expert Reviewer Agent** - Audits drafts for compliance and accuracy

**Self-Correction Loop:** Rejected drafts are automatically refined based on expert feedback (max 3 iterations).

### Transcription Service

Real-time audio transcription powered by Sarvam AI:
- WebSocket-based live transcription
- REST API polling fallback
- Automatic chunk deduplication
- Multi-client support

## Quick Start

```bash
# 1. Configure environment
cp .env.example .env
# Add your API keys to .env:
# - OPENAI_API_KEY (for legal agents)
# - GROQ_API_KEY (for RAG search)
# - SARVAM_API_KEY (for transcription)

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start server (with transcription support)
cd backend
uvicorn app.main:socket_app --reload --host 0.0.0.0 --port 8000

# 4. Access API
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - Health: http://localhost:8000/health
```

## API Usage

### Legal Aid Generation

```bash
curl -X POST "http://localhost:8000/api/v1/generate-legal-aid" \
  -H "Content-Type: application/json" \
  -d '{
    "grievance": "I purchased a defective mobile phone from a shop in Kochi. The seller refuses to provide a refund despite the warranty.",
    "rag_context": ""
  }'
```

### Audio Transcription

**WebSocket (Recommended):**
```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:8000', {
  path: '/socket.io'
});

socket.emit('audio_chunk', {
  audio: base64AudioData,
  timestamp: Date.now() / 1000,
  chunkName: 'chunk_001'
});

socket.on('transcription_result', (data) => {
  console.log('Transcription:', data.text);
});
```

**REST API (Polling Fallback):**
```bash
curl http://localhost:8000/api/v1/transcriptions
```

See [TRANSCRIPTION_API.md](backend/TRANSCRIPTION_API.md) for complete documentation.

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI + SocketIO application
│   ├── agents/              # Three AI agents
│   │   ├── researcher.py
│   │   ├── drafter.py
│   │   └── expert_reviewer.py
│   ├── services/
│   │   ├── orchestrator.py        # Multi-agent workflow
│   │   ├── transcription_service.py  # Audio transcription
│   │   └── transcription_state.py    # State management
│   ├── sockets/
│   │   └── transcription_handlers.py # WebSocket handlers
│   ├── config/
│   │   └── transcription_config.py   # Transcription settings
│   ├── api/v1/
│   │   └── endpoints.py     # REST API
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   └── tests/
├── src/                     # RAG components
├── docustore/              # Legal documents
├── TRANSCRIPTION_API.md    # Transcription API docs
└── TRANSCRIPTION_QUICKSTART.md  # Quick start guide
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
SARVAM_API_KEY=your_sarvam_api_key_here  # Required for transcription
HF_TOKEN=your_hf_token_here              # Optional
```

## Documentation

- [Transcription API Documentation](backend/TRANSCRIPTION_API.md) - Complete WebSocket and REST API reference
- [Transcription Quick Start](backend/TRANSCRIPTION_QUICKSTART.md) - Get started with audio transcription
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when server is running)
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
