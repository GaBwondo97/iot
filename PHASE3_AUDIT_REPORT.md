# Phase 3 — Database Integration Audit Report

## 1. Files Inspected

| File | Status |
|------|--------|
| `backend/app/main.py` | ✅ Exists, working |
| `backend/app/core/config.py` | ✅ Exists, loads `.env` |
| `backend/app/db/session.py` | ✅ Exists, creates engine/session |
| `backend/app/api/routes/health.py` | ✅ Exists, simple router |
| `backend/requirements.txt` | ✅ Has sqlalchemy, asyncpg |
| `database/migrations/001_initial_schema.sql` | ✅ 8 canonical tables |
| `database/README.md` | ✅ Documents schema |
| `docs/DATABASE_SCHEMA.md` | ✅ Detailed DDL + ERD |
| `docs/DATABASE_IMPLEMENTATION_PLAN.md` | ✅ Full plan |
| `backend/.env` | ⚠️ Exists (secret, not read) |
| `.env.example` | ✅ Phase 1 vs future vars separated |

## 2. Existing Implementation Summary

### Backend Core (`main.py`)
- FastAPI app with title/version from config
- CORS middleware: 4 explicit dev origins, GET/OPTIONS, no credentials
- `GET /` → app metadata
- `GET /health` → `{"status": "healthy", "service": "citypulse-backend"}`
- Includes `health_router` at `/api/v1`

### Config (`config.py`)
- Loads `backend/.env` via `python-dotenv`
- `Settings` class with: `app_name`, `app_version`, `app_description`, `database_url`
- `database_url` defaults to empty string
- Single instance: `env_config = Settings()`

### Database Session (`session.py`)
- Creates async engine with `pool_pre_ping=True`
- `AsyncSessionLocal` sessionmaker with `expire_on_commit=False`
- `get_db()` async generator yielding session
- **CRITICAL**: Raises `RuntimeError` if `DATABASE_URL` missing — breaks startup

### Requirements
```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.2
pydantic-settings==2.1.0
sqlalchemy==2.0.23
asyncpg==0.29.0
python-dotenv==1.0.0
```
All compatible with Python 3.8.10.

### Database Schema (Canonical 8 Tables)
From `001_initial_schema.sql`:
1. **cities** — id, city_code, name, country_code, latitude, longitude, created_at, updated_at
2. **environmental_indicators** — id, indicator_code, category, name, unit, description, created_at
3. **iot_devices** — id, device_id, city_id(FK), category, status, last_seen, created_at
4. **observations** — id, city_id, indicator_id, iot_device_id(FK, nullable), source_type, source_name, record_id, observed_at, ingested_at, value(nullable), status, severity(nullable), confidence(nullable), raw_payload(JSONB), unique constraint
5. **risk_assessments** — id, city_id, indicator_id, observed_at, status, risk_score(nullable), severity(nullable), confidence(nullable), assessment_text, assessed_at, data_points_count, missing_indicators(JSONB)
6. **alerts** — id, city_id, risk_assessment_id(FK), severity, message, status, created_at
7. **recommendations** — id, city_id, risk_assessment_id(FK), recommendation_text, action_required, created_at
8. **ingestion_rejection_logs** — id, source_type, reason_code, details(JSONB), rejected_at

Indexes: `idx_obs_city_time`, `idx_obs_indicator_time`, `idx_obs_source`, `idx_risk_city_time`

## 3. Missing Components

| Component | Status |
|-----------|--------|
| SQLAlchemy 2.x declarative models (8 tables) | ❌ Missing |
| FastAPI lifespan (engine init/dispose) | ❌ Missing |
| Repository layer | ❌ Missing |
| Pydantic response schemas (API contract) | ❌ Missing |
| API endpoints for 8 tables | ❌ Missing |
| Database connection tests | ❌ Missing |
| Pagination/filtering utilities | ❌ Missing |

## 4. Compatibility Issues (Python 3.8.10)

| Issue | Severity | Fix |
|-------|----------|-----|
| `session.py` raises `RuntimeError` on missing `DATABASE_URL` | **HIGH** | Make DB optional for liveness; handle gracefully |
| No `lifespan` in FastAPI — engine never disposed | MEDIUM | Add lifespan context manager |
| `pydantic-settings==2.1.0` may need `pydantic>=2.0` — OK | LOW | Verify at runtime |
| `asyncpg==0.29.0` supports Python 3.8+ — OK | LOW | Verified |

## 5. Code That Must Be Preserved

- `main.py`: CORS, root, health, router include
- `config.py`: Settings class, env loading logic
- `session.py`: Engine/session factory pattern (but fix RuntimeError)
- `health.py`: Keep as-is
- All database migration/seed files
- All docs

## 6. Next Steps (Priority Order)

1. **Fix `session.py`** — Remove hard failure on missing `DATABASE_URL`; make engine lazy/optional
2. **Add FastAPI lifespan** — Initialize engine on startup, dispose on shutdown
3. **Create SQLAlchemy models** — `backend/app/db/models.py` matching migration exactly
4. **Create Pydantic schemas** — `backend/app/schemas/` for API responses
5. **Create repository base** — `backend/app/db/repository.py`
6. **Implement cities/indicators endpoints** — Per API contract
6. **Add connection test script** — Verify Supabase connectivity
7. **Run tests** — Verify all endpoints work with real DB