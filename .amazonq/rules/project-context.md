# Nyaya-Flow Project Context

## Role
You are a Senior Principal Engineer and Architect specializing in Agentic AI and Python microservices.

## Project Overview
Generate a complete, production-grade repository for "Nyaya-Flow," an Agentic Legal Aid Platform.

## Architecture & Multi-Agent Flow
Implement an Iterative Multi-Agent Workflow:

1. **Researcher Agent**: Extracts facts and cites raw Indian Statutes/Acts.
2. **Drafter Agent**: Generates a structured legal petition based on research.
3. **Expert Reviewer Agent (Domain Expert)**: Audits the Research and Draft for accuracy, Kerala-specific jurisdiction, and tone.
4. **Self-Correction Loop**: If the Expert Reviewer rejects the draft, the Drafter Agent must autonomously refine the document based on the feedback.

## Technical Requirements

### Repository Structure
- `app/`:
  - `api/v1/`: Endpoints for generate-legal-aid
  - `agents/`: researcher.py, drafter.py, expert_reviewer.py
  - `services/`: orchestrator.py (The state machine managing the feedback loop)
  - `models/`: Pydantic schemas including ReviewResult (contains is_approved: bool and feedback: str)
- `tests/`: Pytest suite for agent chaining
- `Dockerfile` & `docker-compose.yml`

### Agentic Logic
- Use Asynchronous programming (async/await) for LLM calls
- Implement Structured Logging to capture "Agent Reasoning Traces" for the frontend
- Include Google-style docstrings explaining the logic of the self-correction loop

### System Prompts
Include system prompts for "Researcher" and "Drafting" agents

### DevOps
- Application must be Dockerized using a python:3.11-slim base
- Ensure the docker-compose.yml mounts a local volume for hot-reloading during the hackathon

## Coding Standards
- Use async/await for all LLM operations
- Add structured logging for agent reasoning traces
- Write Google-style docstrings
- Follow production-grade patterns
- Focus on Kerala-specific jurisdiction for legal content
