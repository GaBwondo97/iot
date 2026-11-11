# CityPulse AI — Deployment Guide

## 1. Prerequisites
- Python 3.11+ (Hermes's venv on Windows)
- PostgreSQL-compatible database (Supabase preferred)
- `.env` file with credentials
- pip packages: SQLAlchemy, asyncpg, python-dotenv

## 2. Project Structure
```text
citypulse-ai/
├── docs/                     # Documentation
│   ├── DATABASE_IMPLEMENTATION_PLAN.md
│   ├── DATABASE_SCHEMA.md
│   └── DEPLOYMENT_GUIDE.md
├── database/                 # Persistence
│   ├── migrations/           # SQL migration scripts
│   │   └── 001_initial_schema.sql
│   ├── seeds/                # Idempotent seed scripts
│   │   ├── seed_cities.sql
│   │   └── seed_indicators.sql
│   ├── scripts/              # Python seed runner
│   │   └── run_seeds.py
│   └── README.md             # Database README (empty until seeded)
├── .env.example              # Environment placeholders
└── .gitignore                # Security protection
```

## 3. Environment Setup (.env)
Create `.env` from `.env.example`:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=public-anon-key  # For frontend
SUPABASE_SERVICE_ROLE_KEY=service-role-key  # For backend
DATABASE_URL=postgresql://postgres:your_password@your-host:5432/your_db  # For local development
```

## 4. Database Initialization
### 4.1 Run Seed Scripts (Recommended for new deployments)
```bash
python database/scripts/run_seeds.py
```

This runs the SQL files:
- `database/seeds/seed_cities.sql` (creates kuala-lumpur, london, tokyo)
- `database/seeds/seed_indicators.sql` (creates all 16 environmental indicators)

### 4.2 Apply SQL Migration (Alternative)
Execute `database/migrations/001_initial_schema.sql` directly:
```sql
-- Paste the content of 001_initial_schema.sql into psql or Supabase SQL editor
```

## 5. Verification
After running seeds/migration:
```sql
SELECT 'cities' as table_name, COUNT(*) as count FROM cities
UNION ALL
SELECT 'environmental_indicators', COUNT(*) FROM environmental_indicators
UNION ALL
SELECT 'observations', COUNT(*) FROM observations
UNION ALL
SELECT 'risk_assessments', COUNT(*) FROM risk_assessments;
```

Expected initial state:
```
table_name              count
------------------------
cities                  3
cities                  3
environmental_indicators 16
observations            0
risk_assessments        0
```

## 6. Security & Production
### 6. Security Considerations
- **Never commit real `.env` files** — protect them with `.gitignore`
- **Frontend should only use `SUPABASE_ANON_KEY`** — never expose `SERVICE_ROLE_KEY`
- **Least privilege**: Use Row Level Security (RLS) policies if Supabase Data API is exposed

### 6.2 Environment File Protection
Create `.gitignore` with:
```
.env
.env.example
.DS_Store
__pycache__/
*.pyc
```

## 7. Backup
- Enable point-in-time recovery on Supabase
- Run `pg_dump` for local databases:
```bash
pg_dump DATABASE_URL > backup_$(date +%F).sql
```

## 8. Future Migration Process
1. **Increment migration filename** (e.g., 002_add_alerts_table.sql)
2. **Execute migration on Supabase SQL editor** (admin only)
3. **Update seed scripts if needed**

## 9. Schema Validation Queries
Use these queries to verify data integrity:

### 9.1 Check for NULL 'value' fields (allowed)
```sql
SELECT COUNT(*) FROM observations WHERE value IS NULL;
```

### 9.2 Check for NULL 'risk_score' in analyzed assessments
```sql
SELECT COUNT(*) FROM risk_assessments WHERE status = 'analyzed' AND risk_score IS NULL;
```

### 9.3 Check for missing city references
```sql
SELECT COUNT(*) FROM observations o LEFT JOIN cities c ON o.city_id = c.id WHERE c.id IS NULL;
```

## 10. Maintenance
- **Monitoring**: Enable Supabase logs and metrics
- **Backups**: Schedule automated backups
- **RLS**: Define Row Level Security policies if using Supabase REST API directly
- **Indexes**: Use existing indexes; add only if query performance analysis shows need

## 11. Troubleshooting
- **Connection error**: Ensure `.env` DATABASE_URL or Supabase credentials are correct
- **Permission denied**: Verify the PostgreSQL user has rights to create tables
- **Seed failures**: Run migration before seed scripts if using raw SQL