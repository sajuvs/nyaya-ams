j# Docker Setup Guide

## Quick Start

### 1. Setup Environment Variables
```bash
cp .env.example .env
# Edit .env and add your API keys
```

### 2. Run Full Stack (Backend + Frontend)
```bash
docker-compose -f docker-compose.full.yml up --build
```

### 3. Access Services
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 4. Stop Services
```bash
docker-compose -f docker-compose.full.yml down
```

## Backend Only

```bash
docker-compose up --build
```

## Development Mode

Both services run with hot-reload enabled:
- Backend: Changes to Python files auto-reload
- Frontend: Changes to React files auto-reload

## Logs

View logs:
```bash
# All services
docker-compose -f docker-compose.full.yml logs -f

# Backend only
docker-compose -f docker-compose.full.yml logs -f backend

# Frontend only
docker-compose -f docker-compose.full.yml logs -f frontend
```

## Troubleshooting

### Port conflicts
If ports 3000 or 8000 are in use, edit `docker-compose.full.yml`:
```yaml
ports:
  - "3001:3000"  # Change host port
```

### Rebuild containers
```bash
docker-compose -f docker-compose.full.yml up --build --force-recreate
```

### Clear volumes
```bash
docker-compose -f docker-compose.full.yml down -v
```
