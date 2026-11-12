#!/usr/bin/env python3
"""
CityPulse AI — Risk Scoring CLI Runner

Generates risk assessments for pilot cities using the MVP rule-based engine.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path (backend/ must be in path for 'app' imports)
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.session import init_db, close_db, AsyncSessionLocal
from ai_engine.risk_engine import run_risk_scoring


async def main():
    """Run risk scoring for all pilot cities."""
    print("Initializing database...")
    init_db()

    try:
        async with AsyncSessionLocal() as session:
            print("Running risk scoring engine...")
            results = await run_risk_scoring(session)
    finally:
        await close_db()

    print("\n" + "=" * 60)
    print("RISK SCORING RESULTS")
    print("=" * 60)

    for city_code, result in results.items():
        print(f"\n{city_code.upper()}:")
        if result["status"] == "success":
            print(f"  Assessments created: {result['assessments_count']}")
            for detail in result["details"]:
                score = detail["risk_score"] or "NULL"
                severity = detail["severity"] or "NULL"
                print(f"  - Indicator {detail['indicator']}: score={score}, severity={severity}, status={detail['status']}")
        else:
            print(f"  ERROR: {result['error']}")

    print("\n" + "=" * 60)
    print("Note: Thresholds are PRELIMINARY HEURISTICS — NOT scientifically validated.")


if __name__ == "__main__":
    asyncio.run(main())