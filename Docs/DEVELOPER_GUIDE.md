# ICAP Developer Guide

## Table of Contents
- [Project Structure](#project-structure)
- [Development Setup](#development-setup)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Contributing](#contributing)
- [Code Style](#code-style)

## Project Structure

```
ColorAIStudio/
├── irm_api.py              # Main FastAPI application entry point
├── color_engine.py         # Color science calculations (Delta E, RAL, etc.)
├── vision_engine.py        # Vision AI operations (YOLO, ViT, etc.)
├── rag_system.py           # RAG system with Qdrant integration
├── agents_system.py        # Multi-agent orchestration
├── ai_color_analysis.py    # AI-driven color analysis (SPC, trends)
├── database.py             # Database connection and initialization
├── alerting_system.py      # Alert notifications (Slack, Email, SMS)
├── knowledge_graph.py      # Industrial knowledge graph
├── iot_connector.py        # MQTT connector for sensor data
├── opc_ua_connector.py     # OPC-UA connector for industrial controllers
├── routers/                # API route handlers
│   ├── color.py           # Color analysis endpoints
│   ├── vision.py          # Vision AI endpoints
│   ├── rag.py             # RAG endpoints
│   ├── agents.py          # Agent orchestration endpoints
│   └── ...
├── utils/                  # Utility modules
│   ├── cache_manager.py   # LRU cache implementation
│   ├── circuit_breaker.py # Circuit breaker pattern
│   ├── correlation_id.py  # Request correlation ID middleware
│   ├── tracing.py         # OpenTelemetry distributed tracing
│   ├── business_metrics.py # Custom business KPIs
│   └── ...
├── tests/                  # Test suite
│   ├── test_api.py        # Basic API tests
│   ├── test_color_engine.py # Color engine tests
│   ├── test_integration_color.py # Integration tests
│   ├── test_integration_rag.py    # RAG integration tests
│   ├── test_integration_iot.py    # IoT integration tests
│   └── test_e2e_workflows.py     # End-to-end workflow tests
├── Docs/                   # Documentation
├── AuditTrail/             # Database and audit logs
├── RAG/                    # Document storage for RAG indexing
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container definition
├── docker-compose.yml     # Multi-container orchestration
└── .env.example           # Environment variables template
```

## Development Setup

### Prerequisites
- Python 3.9+
- Docker and Docker Compose (for containerized deployment)
- Git

### Local Development

1. **Clone the repository**
```bash
git clone <repository-url>
cd ColorAIStudio
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**
```bash
python -c "import database; database.init_enterprise_db()"
```

## Running the Application

### Development Server
```bash
python irm_api.py
```

The API will be available at `http://localhost:8000`

### Using Docker Compose
```bash
docker-compose up -d
```

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## API Documentation

The ICAP API provides endpoints for:

### Color Analysis
- `POST /color/analyze` - Analyze color differences
- `POST /color/predict_trend` - Predict color trends
- `POST /color/recipe_formulation` - Calculate recipe recommendations

### Vision AI
- `POST /vision/analyze` - Detect defects in images
- `POST /vision/multi_view_fusion` - Multi-view defect detection
- `POST /vision/micro_defects` - Micro-defect analysis

### RAG System
- `POST /rag/query` - Query indexed documents
- `POST /rag/index` - Index new documents
- `GET /rag/stats` - Get RAG statistics

### Multi-Agent System
- `POST /agents/process` - Execute agent workflows
- `POST /agents/root_cause` - Root cause analysis

### IoT Connectors
- `POST /iot/mqtt/status` - MQTT connector status
- `POST /iot/opcua/status` - OPC-UA connector status

## Testing

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=. --cov-report=html
```

### Run specific test categories
```bash
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m e2e          # End-to-end tests only
```

### Run specific test file
```bash
pytest tests/test_color_engine.py
```

## Contributing

### Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Add docstrings to all functions and classes
- Write tests for new features

### Commit Messages
Use conventional commit format:
```
feat: add new feature
fix: fix bug in existing feature
docs: update documentation
test: add or update tests
refactor: code refactoring
```

### Pull Request Process
1. Create feature branch from `main`
2. Make changes and write tests
3. Ensure all tests pass
4. Update documentation
5. Submit pull request with description

## Code Style

### Python
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Import order: standard library, third-party, local
- Use f-strings for string formatting

### Example
```python
from typing import List, Dict, Optional
import numpy as np

def calculate_delta_e(lab1: List[float], lab2: List[float]) -> float:
    """
    Calculate Delta E between two LAB color values.
    
    Args:
        lab1: First LAB color [L, a, b]
        lab2: Second LAB color [L, a, b]
        
    Returns:
        Delta E value
    """
    # Implementation
    pass
```

## Environment Variables

Key environment variables (see `.env.example` for complete list):

```bash
# Database
ICAP_DATABASE_URL=sqlite:///AuditTrail/icap_enterprise.db

# Ollama LLM
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Qdrant Vector Database
QDRANT_URL=http://localhost:6333

# MQTT
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_TOPIC=factory/sensors/#

# OPC-UA
OPC_UA_SERVER_URL=opc.tcp://localhost:4840

# API Configuration
ICAP_ENVIRONMENT=development
ICAP_RATE_LIMIT=100
ICAP_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Tracing
ICAP_ENABLE_TRACING=false
```

## Troubleshooting

### Database Issues
```bash
# Reset database
rm AuditTrail/icap_enterprise.db
python -c "import database; database.init_enterprise_db()"
```

### Qdrant Connection
```bash
# Check Qdrant status
curl http://localhost:6333/health
```

### Ollama Connection
```bash
# Check Ollama status
curl http://localhost:11434/api/tags
```

## Performance Optimization

### Caching
- SPC calculations are cached for 30 minutes
- Delta E calculations are cached for 1 hour
- RAL lookups are cached for 2 hours

### Database
- Connection pooling enabled (max 5 connections)
- WAL mode for better concurrency
- Indexes on common query fields

### RAG
- Parallel embedding processing
- Batch processing for large documents
- Sparse + Dense hybrid search

## Security

### API Security
- Rate limiting enabled (100 req/min default)
- CORS configuration
- Input validation on all endpoints
- Correlation ID for request tracing

### Data Security
- No hardcoded credentials
- Environment variables for sensitive data
- SQL injection prevention (parameterized queries)
- Input sanitization

## Monitoring

### Metrics
- Prometheus metrics at `/metrics`
- Custom business metrics via `utils/business_metrics.py`
- Alert system with rate limiting

### Logging
- Structured logging with correlation IDs
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Log aggregation via WebSocket handler

### Tracing
- OpenTelemetry distributed tracing (optional)
- Jaeger exporter support
- Enable via `ICAP_ENABLE_TRACING=true`
