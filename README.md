# CityPulse AI

**Turning Global Data into Intelligent Decisions.**

CityPulse AI is a global AI-powered urban monitoring and risk assessment decision-support system.

## 1. Project Context
CityPulse AI provides insights into environmental and urban conditions across global cities using a combination of public APIs, simulated IoT measurements, and AI-driven risk scoring.

**Pilot Cities:**
- Kuala Lumpur (Malaysia)
- London (UK)
- Tokyo (Japan)

## 2. Technology Stack
- **Backend:** FastAPI, Pydantic, SQLAlchemy 2.x
- **Frontend:** React, TypeScript, Vite
- **Database:** PostgreSQL (Supabase managed)
- **Deployment:** Render (Backend), Vercel (Frontend), Supabase (Database)

## 3. Project Structure
```text
citypulse-ai/
├── backend/           # FastAPI application
├── frontend/          # React web dashboard
├── data_engineering/  # Data ingestion and normalization
├── ai_engine/         # Anomaly detection and risk scoring
├── iot/               # IoT simulator and MQTT transport
├── database/          # Schemas, migrations, and seeds
├── docs/              # System documentation
└── tests/             # Integration tests
```

## 4. Getting Started

### Prerequisites
- Python 3.11+
- Node.js & npm
- PostgreSQL (Local or Supabase)

### Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 5. Development Status
- **Phase 1: Foundation (Current)** - Project structure, minimal backend/frontend established.
- **Phase 2: Architecture (Planned)** - System design and contract finalization.
- **Phase 3: Core Implementation (Planned)** - Data pipeline and AI scoring.

## 6. Existing Database Deliverables (Person 4)
- PostgreSQL schema, migrations, and seed scripts
- Independent test suite (run via `database/scripts/run_seeds.py`)
- Supabase integration guidance