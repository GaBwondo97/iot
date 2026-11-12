#!/usr/bin/env python3
"""
CityPulse AI — Data Ingestion Runner

Fetches weather and/or air quality data for pilot cities
and inserts observations into the database.

Usage:
    python -m data_engineering.run_ingestion --weather
    python -m data_engineering.run_ingestion --air-quality
    python -m data_engineering.run_ingestion --both
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import List

# Add project root and backend to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

# Load environment variables from backend/.env
load_dotenv(BACKEND_DIR / ".env")

from data_engineering.pipeline import (
    run_weather_ingestion,
    run_air_quality_ingestion,
    run_combined_ingestion,
    IngestionResult,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)


def print_summary(title: str, results: List[IngestionResult]) -> None:
    """Print ingestion summary."""
    total_successful = sum(r.successful for r in results)
    total_skipped = sum(r.skipped for r in results)
    total_failed = sum(r.failed for r in results)
    
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)
    
    for r in results:
        status = "OK" if r.failed == 0 else ("UNAVAILABLE" if r.successful == 0 and r.failed == 0 else "ERROR")
        print(f"  {r.city_code:15} | {status} | "
              f"inserted: {r.successful:2d} | skipped: {r.skipped:2d} | failed: {r.failed:2d}")
        for err in r.errors:
            print(f"    └─ {err}")
    
    print("-" * 50)
    print(f"  TOTAL           | inserted: {total_successful:2d} | "
          f"skipped: {total_skipped:2d} | failed: {total_failed:2d}")
    print("=" * 50)


async def main() -> int:
    """Main entry point."""
    # Initialize database
    from app.db.session import init_db
    init_db()
    
    parser = argparse.ArgumentParser(description="CityPulse AI Data Ingestion")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--weather", action="store_true", help="Run weather ingestion only")
    group.add_argument("--air-quality", action="store_true", help="Run air quality ingestion only")
    group.add_argument("--both", action="store_true", help="Run both weather and air quality ingestion")
    
    args = parser.parse_args()
    
    try:
        if args.weather:
            log.info("Starting weather ingestion for pilot cities...")
            results = await run_weather_ingestion()
            print_summary("WEATHER INGESTION SUMMARY", results)
            total_failed = sum(r.failed for r in results)
            
        elif args.air_quality:
            log.info("Starting air quality ingestion for pilot cities...")
            results = await run_air_quality_ingestion()
            print_summary("AIR QUALITY INGESTION SUMMARY", results)
            total_failed = sum(r.failed for r in results)
            
        elif args.both:
            log.info("Starting combined weather and air quality ingestion...")
            weather_results, air_quality_results = await run_combined_ingestion()
            print_summary("WEATHER INGESTION SUMMARY", weather_results)
            print_summary("AIR QUALITY INGESTION SUMMARY", air_quality_results)
            total_failed = sum(r.failed for r in weather_results) + sum(r.failed for r in air_quality_results)
        
    except Exception as e:
        log.error(f"Ingestion failed: {e}")
        print(f"\nFATAL: {e}")
        return 1
    
    return 1 if total_failed > 0 else 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)