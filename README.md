# nyaya-ams
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
