#!/usr/bin/env python3
"""
CityPulse AI — Database Seed Runner
Runs all seed scripts in order: cities, indicators, iot_devices.
Idempotent: safe to re-run.
Usage: python database/scripts/run_seeds.py
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path for SQLAlchemy imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set. Copy .env.example to .env and fill in values.")
    sys.exit(1)

SEED_DIR = Path(__file__).resolve().parent.parent / "seeds"
SEED_FILES = [
    "seed_cities.sql",
    "seed_indicators.sql",
]

def run_seeds():
    engine = create_engine(DATABASE_URL)
    try:
        with engine.connect() as conn:
            # Enable UUID extension if not already present
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            conn.commit()

            for seed_file in SEED_FILES:
                seed_path = SEED_DIR / seed_file
                if not seed_path.exists():
                    print(f"SKIP: {seed_file} (not found)")
                    continue
                print(f"RUNNING: {seed_file}")
                sql = seed_path.read_text()
                conn.execute(text(sql))
                conn.commit()
                print(f"OK: {seed_file}")
            print("\nAll seeds completed successfully.")
    except OperationalError as e:
        print(f"ERROR: Cannot connect to database. {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_seeds()