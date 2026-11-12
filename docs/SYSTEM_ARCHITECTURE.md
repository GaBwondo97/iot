# CityPulse AI — System Architecture

## Planned System Flow

### Data Ingestion Path
```
Public APIs / Open Datasets
    ↓
Data Engineering (Adapters, Validation, Normalization)
    ↓
AI/ML Engine (Risk Scoring, Anomaly Detection)
    ↓
PostgreSQL (Observations, Risk Assessments, Alerts)
    ↓
FastAPI (REST API)
    ↓
React Dashboard (Visualization, Alerts, Recommendations)
```

### Simulated IoT Path
```
Simulated IoT Sensors
    ↓
MQTT Broker (Mosquitto / EMQX Cloud)
    ↓
Backend Integration (MQTT Subscriber)
    ↓
Data Processing (Validation, Normalization, Deduplication)
    ↓
Database (Observations, Risk Assessments)
```

## Component Status

### Implemented (Phase 1)
- **Backend:** FastAPI application with `/` and `/health` endpoints
- **Frontend:** React + TypeScript + Vite dashboard shell
- **Database:** PostgreSQL schema, migrations, and seed scripts (Person 4 deliverable)
- **Documentation:** Project overview, deployment guide, database schema

### Planned (Future Phases)
- **Data Engineering:** Adapters for Open-Meteo, OpenAQ, and IoT payloads
- **AI/ML Engine:** Risk scoring, anomaly detection, and recommendation generation
- **IoT Simulator:** Weather, air quality, traffic, and population simulators
- **MQTT Transport:** Publisher, subscriber, and topic configuration
- **Frontend Dashboard:** City selection, monitoring overview, risk assessment display

## Architecture Principles
- **Modular:** Each component is independent and testable.
- **Single Source of Truth:** Shared Pydantic models for data contracts.
- **PostgreSQL-Only:** No MongoDB, Redis, or separate data warehouse for MVP.
- **Laptop-Development Friendly:** No complex infrastructure required.
- **Hackathon MVP:** Focus on core functionality over production-grade deployment.