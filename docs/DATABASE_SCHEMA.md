# CityPulse AI — Finalized Database Schema Proposal

**Document Version:** 1.0  
**Role:** Database & Cloud Engineer (Person 4)  
**Status:** Aligned with Person 1 (Backend), Person 2 (Data/AI/ML), Person 3 (IoT)  

---

## 1. ERD & Entity Relationships

```text
               +-------------------+
               |      cities       |
               +-------------------+
               | id (PK)           |
               | name              |
               | country_code      |
               | latitude          |
               | longitude         |
               +---------+---------+
                         | 1
                         |
                         | N
        +----------------+----------------+
        |                                 |
+-------v-----------+            +--------v----------+
|   iot_devices     |            |   observations    |
+-------------------+            +-------------------+
| id (PK)           |            | id (PK)           |
| device_id (Unique)|            | city_id (FK)      |
| city_id (FK)      |            | indicator_id (FK) |
| indicator_id (FK) |            | source_type       |
| status            |            | source_name       |
| last_seen         |            | observed_at (UTC) |
+-------------------+            | ingested_at (UTC) |
                                 | record_id         |
                                 | value (DECIMAL)   |
                                 | raw_payload (JSON)|
                                 +---------+---------+
                                           | N
                                           | (Aggregated by AI Engine)
                                           | 1
                                 +---------v---------+
                                 |  risk_assessments |
                                 +-------------------+
                                 | id (PK)           |
                                 | city_id (FK)      |
                                 | status            |
                                 | risk_score (0-1)  |
                                 | severity          |
                                 | confidence (0-1)  |
                                 | assessed_at       |
                                 +----+---------+----+
                                      | 1       | 1
                                      | N       | N
                            +---------v---+   +-v-----------------+
                            |   alerts    |   |  recommendations  |
                            +-------------+   +-------------------+
                            | id (PK)     |   | id (PK)           |
                            | assessment  |   | assessment (FK)   |
                            | message     |   | text              |
                            | status      |   | action_required   |
                            +-------------+   +-------------------+
```

---

## 2. PostgreSQL DDL Schema (Supabase-Compatible)

```sql
-- CityPulse AI Initial Migration Schema
-- Compatible with PostgreSQL 15+ / Supabase

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Cities Reference Table
CREATE TABLE IF NOT EXISTS cities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    city_code VARCHAR(50) UNIQUE NOT NULL, -- e.g. KUALA_LUMPUR, LONDON, TOKYO
    name VARCHAR(100) NOT NULL,
    country_code VARCHAR(10) NOT NULL,
    latitude DECIMAL(9, 6) NOT NULL,
    longitude DECIMAL(9, 6) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 2. Environmental Indicators Reference Table
CREATE TABLE IF NOT EXISTS environmental_indicators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    indicator_code VARCHAR(50) UNIQUE NOT NULL, -- e.g. temperature, pm25, vehicle_count
    category VARCHAR(50) NOT NULL, -- weather, air_quality, traffic, population
    name VARCHAR(100) NOT NULL,
    unit VARCHAR(30) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 3. IoT Devices Reference Table
CREATE TABLE IF NOT EXISTS iot_devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id VARCHAR(100) UNIQUE NOT NULL, -- e.g. WEATHER_SIM_KL_01
    city_id UUID REFERENCES cities(id) ON DELETE CASCADE NOT NULL,
    category VARCHAR(50) NOT NULL,
    status VARCHAR(30) DEFAULT 'online' NOT NULL, -- online, offline, degraded
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 4. Unified Observations Table (Public API + IoT)
CREATE TABLE IF NOT EXISTS observations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    city_id UUID REFERENCES cities(id) ON DELETE CASCADE NOT NULL,
    indicator_id UUID REFERENCES environmental_indicators(id) ON DELETE CASCADE NOT NULL,
    iot_device_id UUID REFERENCES iot_devices(id) ON DELETE SET NULL, -- NULL for public API
    source_type VARCHAR(50) NOT NULL, -- 'simulation', 'public_api'
    source_name VARCHAR(100) NOT NULL, -- 'Paho-MQTT', 'Open-Meteo', 'OpenAQ'
    record_id VARCHAR(100), -- Unique record ID from source for deduplication
    observed_at TIMESTAMPTZ NOT NULL, -- Event timestamp in UTC
    ingested_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    value DECIMAL(12, 4), -- NULL allowed if reading failed/missing (never zero!)
    status VARCHAR(30) DEFAULT 'active' NOT NULL, -- active, rejected, duplicate
    raw_payload JSONB, -- Full JSON message for audit/debugging
    CONSTRAINT uq_observation_record UNIQUE (city_id, indicator_id, observed_at, source_type)
);

-- Indexes for high-frequency queries
CREATE INDEX idx_obs_city_time ON observations (city_id, observed_at DESC);
CREATE INDEX idx_obs_indicator_time ON observations (indicator_id, observed_at DESC);
CREATE INDEX idx_obs_source ON observations (source_type);

-- 5. Risk Assessments Table
CREATE TABLE IF NOT EXISTS risk_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    city_id UUID REFERENCES cities(id) ON DELETE CASCADE NOT NULL,
    status VARCHAR(30) NOT NULL, -- 'analyzed', 'partial', 'insufficient_data'
    risk_score DECIMAL(3, 2), -- 0.00 to 1.00 (NULL if insufficient_data)
    severity VARCHAR(30), -- 'low', 'moderate', 'high', 'critical' (NULL if insufficient_data)
    confidence DECIMAL(3, 2), -- 0.00 to 1.00 (NULL if insufficient_data)
    assessed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    data_points_count INT NOT NULL DEFAULT 0,
    missing_indicators JSONB -- List of missing metrics if status is 'partial' or 'insufficient_data'
);

CREATE INDEX idx_risk_city_time ON risk_assessments (city_id, assessed_at DESC);

-- 6. Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    city_id UUID REFERENCES cities(id) ON DELETE CASCADE NOT NULL,
    assessment_id UUID REFERENCES risk_assessments(id) ON DELETE CASCADE NOT NULL,
    severity VARCHAR(30) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(30) DEFAULT 'active' NOT NULL, -- active, acknowledged, resolved
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 7. Recommendations Table
CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    city_id UUID REFERENCES cities(id) ON DELETE CASCADE NOT NULL,
    assessment_id UUID REFERENCES risk_assessments(id) ON DELETE CASCADE NOT NULL,
    recommendation_text TEXT NOT NULL,
    action_required BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 8. Ingestion Audit / Rejection Log Table
CREATE TABLE IF NOT EXISTS ingestion_rejection_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type VARCHAR(50) NOT NULL,
    reason_code VARCHAR(100) NOT NULL, -- e.g. INVALID_TIMESTAMP, MISSING_REQUIRED_FIELD, RANGE_OUT_OF_BOUNDS
    details JSONB,
    rejected_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

---

## 3. Data Dictionary

| Table | Column | Type | Constraints | Description |
|---|---|---|---|---|
| **cities** | id | UUID | PK, DEFAULT uuid_generate_v4() | Unique city ID |
| | city_code | VARCHAR(50) | UNIQUE, NOT NULL | Code identifier (e.g. KUALA_LUMPUR) |
| | name | VARCHAR(100) | NOT NULL | Display name |
| | country_code | VARCHAR(10) | NOT NULL | ISO country code (e.g. MY, GB, JP) |
| | latitude | DECIMAL(9,6) | NOT NULL | WGS84 Latitude |
| | longitude | DECIMAL(9,6) | NOT NULL | WGS84 Longitude |
| **environmental_indicators** | id | UUID | PK | Unique indicator ID |
| | indicator_code | VARCHAR(50) | UNIQUE, NOT NULL | Code (temperature, pm25, aqi, vehicle_count) |
| | category | VARCHAR(50) | NOT NULL | Category: weather, air_quality, traffic, population |
| | unit | VARCHAR(30) | NOT NULL | Unit: °C, µg/m³, count, people/km² |
| **observations** | id | UUID | PK | Unique observation ID |
| | city_id | UUID | FK → cities.id | City target |
| | indicator_id | UUID | FK → environmental_indicators.id | Metric measured |
| | source_type | VARCHAR(50) | NOT NULL | `simulation` or `public_api` |
| | observed_at | TIMESTAMPTZ | NOT NULL | Measurement timestamp (UTC) |
| | value | DECIMAL(12,4) | NULLABLE | Measurement value (NULL = missing/failed) |
| **risk_assessments** | id | UUID | PK | Unique assessment ID |
| | city_id | UUID | FK → cities.id | Assessed city |
| | status | VARCHAR(30) | NOT NULL | `analyzed`, `partial`, `insufficient_data` |
| | risk_score | DECIMAL(3,2) | NULLABLE | Calculated score 0.00-1.00 (NULL if insufficient data) |
| | severity | VARCHAR(30) | NULLABLE | `low`, `moderate`, `high`, `critical` |
| | confidence | DECIMAL(3,2) | NULLABLE | Calculated confidence 0.00-1.00 |
