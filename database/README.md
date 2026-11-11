# CityPulse AI — Database

Database & Cloud Engineer (Person 4) deliverables.

## Overview
- **Database**: PostgreSQL 15+ (Supabase managed)
- **ORM**: SQLAlchemy 2.x (async)
- **Migration**: Alembic (SQL scripts)
- **Seed**: Idempotent SQL + Python runner

## Schema Tables
| Table | Purpose |
|---|---|
| `cities` | Reference data for pilot cities (kuala-lumpur, london, tokyo) |
| `environmental_indicators` | 16 metric definitions across weather, air_quality, traffic, population |
| `iot_devices` | Virtual sensor registry (device_id, city, status, last_seen) |
| `observations` | Unified observations table (public API + IoT simulation) |
| `risk_assessments` | AI engine assessment results (risk_score, severity, confidence) |
| `alerts` | Active alerts triggered by risk assessments |
| `recommendations` | Explainable recommendations generated from assessment drivers |
| `ingestion_rejection_logs` | Audit log for rejected records with reason codes |

## Data Flow
```
IoT Simulator (Paho-MQTT) → Mosquitto Broker → Backend Subscriber
                                                      ↓
                                          process_iot_message(topic, payload)
                                                      ↓
                                          Data Pipeline (Person 2)
                                          - Validation → Normalization → Deduplication
                                                      ↓
                                          observations table
                                                      ↓
                                          AI Engine → risk_assessments
                                                      ↓
                                          alerts + recommendations
```

## Setup
1. Create `.env` from `.env.example` and fill in credentials
2. Run migration: `database/migrations/001_initial_schema.sql`
3. Run seeds: `python database/scripts/run_seeds.py`

## Seed Data
- **Cities**: Kuala Lumpur, London, Tokyo
- **Indicators**: 16 metrics (4 weather, 4 air_quality, 4 traffic, 4 population)

## Indexes
- `idx_obs_city_time` — (city_id, observed_at DESC)
- `idx_obs_indicator_time` — (indicator_id, observed_at DESC)
- `idx_obs_source` — (source_type)
- `idx_risk_city_time` — (city_id, assessed_at DESC)

## Security
- Never commit real `.env` files
- Frontend uses `SUPABASE_ANON_KEY` only
- Backend uses `SUPABASE_SERVICE_ROLE_KEY` (never exposed to browser)
- Row Level Security (RLS) policies if Supabase Data API is exposed

## Documentation
- `docs/DATABASE_IMPLEMENTATION_PLAN.md` — Full architecture & team alignment
- `docs/DATABASE_SCHEMA.md` — DDL & Data Dictionary
- `docs/DEPLOYMENT_GUIDE.md` — Deployment & operations guide