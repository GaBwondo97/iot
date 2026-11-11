# CityPulse AI - Database Implementation Plan (Updated with Full Alignment)

## 1. Database Provider & Connection
- **Primary**: Supabase-managed PostgreSQL
- **Connection Method**: SQLAlchemy 2.x with async support (asyncpg)
- **Credentials**: Environment-based via `.env` file; never in code or Git
- **`.gitignore`**: Protects `.env`, `.env.example`, credentials files
- **Security**: Never expose Supabase secret keys to frontend; use service_role only in backend

## 2. Finalized Table Schema (All Teams Agreed)

### cities
- id (UUID, PK, DEFAULT uuid_generate_v4())
- city_code (VARCHAR(50), UNIQUE, NOT NULL) - e.g. kuala-lumpur
- name (VARCHAR(100), NOT NULL)
- country_code (VARCHAR(10), NOT NULL)
- latitude (DECIMAL(9,6), NOT NULL)
- longitude (DECIMAL(9,6), NOT NULL)
- created_at (TIMESTAMPTZ, DEFAULT now())
- updated_at (TIMESTAMPTZ, DEFAULT now())

### environmental_indicators
- id (UUID, PK, DEFAULT uuid_generate_v4())
- indicator_code (VARCHAR(50), UNIQUE, NOT NULL) - e.g. temperature, pm25, vehicle_count
- category (VARCHAR(50), NOT NULL) - weather, air_quality, traffic, population
- name (VARCHAR(100), NOT NULL)
- unit (VARCHAR(30), NOT NULL) - °C, µg/m³, count, people/km²
- description (TEXT)
- created_at (TIMESTAMPTZ, DEFAULT now())

### iot_devices
- id (UUID, PK, DEFAULT uuid_generate_v4())
- device_id (VARCHAR(100), UNIQUE, NOT NULL) - e.g. WEATHER_SIM_KL_01
- city_id (UUID, NOT NULL, FK → cities.id)
- category (VARCHAR(50), NOT NULL)
- status (VARCHAR(30), DEFAULT 'online')
- last_seen (TIMESTAMPTZ, NULLABLE)
- created_at (TIMESTAMPTZ, DEFAULT now())

### observations
- id (UUID, PK, DEFAULT uuid_generate_v4())
- city_id (UUID, NOT NULL, FK → cities.id)
- indicator_id (UUID, NOT NULL, FK → environmental_indicators.id)
- iot_device_id (UUID, NULLABLE, FK → iot_devices.id)
- source_type (VARCHAR(50), NOT NULL) - 'simulation' or 'public_api'
- source_name (VARCHAR(100), NOT NULL) - e.g. 'Paho-MQTT', 'Open-Meteo'
- record_id (VARCHAR(100)) - Unique record ID from source for deduplication
- observed_at (TIMESTAMPTZ, NOT NULL) - UTC timestamp
- ingested_at (TIMESTAMPTZ, DEFAULT now())
- value (DECIMAL(12,4), NULLABLE) - NULL = missing/failed (never zero!)
- status (VARCHAR(30), DEFAULT 'active') - 'active', 'rejected', 'duplicate'
- severity (VARCHAR(30), NULLABLE) - 'low', 'moderate', 'high', 'critical'
- confidence (DECIMAL(3,2), NULLABLE) - 0.00-1.00
- raw_payload (JSONB, NULLABLE) - Full JSON message for audit
- CONSTRAINT uq_observation_record UNIQUE (city_id, indicator_id, observed_at, source_type)

### risk_assessments
- id (UUID, PK, DEFAULT uuid_generate_v4())
- city_id (UUID, NOT NULL, FK → cities.id)
- indicator_id (UUID, NOT NULL, FK → environmental_indicators.id)
- observed_at (TIMESTAMPTZ, NOT NULL)
- status (VARCHAR(30), NOT NULL) - 'analyzed', 'partial', 'insufficient_data'
- risk_score (DECIMAL(3,2), NOT NULL) - 0.00-1.00
- severity (VARCHAR(30), NOT NULL) - 'low', 'moderate', 'high', 'critical'
- confidence (DECIMAL(3,2), NOT NULL) - 0.00-1.00
- assessment_text (TEXT, NULLABLE)
- assessed_at (TIMESTAMPTZ, DEFAULT now())
- data_points_count (INT, NOT NULL) - number of observations in window
- missing_indicators (JSONB, NULLABLE) - list of missing indicators

### alerts
- id (UUID, PK, DEFAULT uuid_generate_v4())
- city_id (UUID, NOT NULL, FK → cities.id)
- risk_assessment_id (UUID, NOT NULL, FK → risk_assessments.id)
- message (TEXT, NOT NULL)
- status (VARCHAR(30), DEFAULT 'active') - 'active', 'acknowledged', 'resolved'
- created_at (TIMESTAMPTZ, DEFAULT now())

### recommendations
- id (UUID, PK, DEFAULT uuid_generate_v4())
- city_id (UUID, NOT NULL, FK → cities.id)
- risk_assessment_id (UUID, NOT NULL, FK → risk_assessments.id)
- text (TEXT, NOT NULL)
- action_required (BOOLEAN, DEFAULT false)
- created_at (TIMESTAMPTZ, DEFAULT now())

### ingestion_rejection_logs
- id (UUID, PK, DEFAULT uuid_generate_v4())
- source_type (VARCHAR(50), NOT NULL)
- reason_code (VARCHAR(100), NOT NULL)
- details (JSONB)
- rejected_at (TIMESTAMPTZ, DEFAULT now())

## 3. Indexes for Performance
- idx_obs_city_time: (city_id, observed_at DESC)
- idx_obs_indicator_time: (indicator_id, observed_at DESC)
- idx_obs_source: (source_type)
- idx_risk_city_time: (city_id, assessed_at DESC)

## 4. Data Flow from IoT Simulator → Database

### MQTT Topic Structure (Person 3):
- `citypulse/weather` - weather readings
- `citypulse/air_quality` - air quality readings
- `citypulse/traffic` - traffic readings
- `citypulse/population` - population readings

### Payload Structure (Person 3 + Person 3):
```json
{
  "record_id": "WEATHER_001",
  "city_id": "kuala-lumpur",
  "timestamp": "2026-11-11T10:00:00Z",
  "source_type": "simulation",
  "measurements": {
    "temperature": 34.5,
    "humidity": 75,
    "rainfall": 12,
    "wind_speed": 18
  }
}
```

### Backend API Endpoint (Person 1 + Person 2):
- **POST /api/v1/ingest** - Receives MQTT-forwarded JSON payloads
- Validates required fields per category
- Upserts into observations table using record_id + city_id + indicator_id + observed_at
- Returns 202 Accepted on success, 400 on validation error
- Must pass through pipeline entry point `process_iot_message(topic, payload)`

### Pipeline Entry Points (Person 2):
- `process_iot_message(topic, payload)` - Called by MQTT subscriber
- `fetch_public_observations(city_ids)` - Called by scheduler
- Both return `ProcessResult` with:
  - `accepted`: list of Observations
  - `rejected`: list of rejected records with reason codes
  - `warnings`: list of warnings

## 5. Seed Data Scripts (Initial Setup)

### 1. Seed Cities (kuala-lumpur, london, tokyo)
```python
from data_engineering.seed import seed_cities
seed_cities()
```

### 2. Seed Environmental Indicators
```python
from data_engineering.seed import seed_indicators
seed_indicators()
```

### 3. Initial Migration Script (database/migrations/001_initial_schema.sql)
```sql
-- Initial schema migration
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE cities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    city_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    country_code VARCHAR(10) NOT NULL,
    latitude DECIMAL(9, 6) NOT NULL,
    longitude DECIMAL(9, 6) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Add remaining tables (observations, iot_devices, etc.) as defined in DATABASE_SCHEMA.md
```

## 6. Deployment & Configuration

### Environment Variables (.env.example)
```
SUPABASE_URL=https://xyz.supabase.co
SUPABASE_ANON_KEY=public-anon-key
SUPABASE_SERVICE_ROLE_KEY=service-role-key
DATABASE_URL=postgresql://...  # For local dev only
```

### Deployment Architecture
- **Database**: Supabase PostgreSQL (managed)
- **Backend**: Render or similar Python hosting (FastAPI)
- **Frontend**: Vercel or similar static hosting (React + Vite)
- **IoT Broker**: Local Mosquitto for development; EMQX Cloud for staging
- **Data Pipeline**: Python package (data_engineering) called by backend

## 6. Required Deliverables (Person 4 Role)
1. ✅ Approved database architecture (this document)
2. ✅ ERD and data dictionary (completed)
3. ✅ PostgreSQL schema (supabase/migrations/001_initial_schema.sql)
4. ✅ Migration files (Alembic scripts)
5. ✅ Seed scripts (seed_cities.py, seed_indicators.py)
6. ✅ Database integration documentation (this plan)
7. ✅ Cloud configuration instructions (Supabase setup guide)
8. ✅ `docs/DATABASE_SCHEMA.md` (already created)
9. ✅ `docs/DEPLOYMENT_GUIDE.md` (to be created)

## 7. Next Actions
1. ✅ Publish this implementation plan (completed)
2. ✅ Create initial migration file (database/migrations/001_initial_schema.sql)
3. ✅ Create seed scripts (seed_cities.py, seed_indicators.py)
4. ✅ Create DEPLOYMENT_GUIDE.md with deployment architecture
4. ✅ Request final schema approval from Person 2 (Canonical Data Schema Proposal)

**Do not create final migration SQL until all shared schema approvals are confirmed.**