#!/usr/bin/env python
"""
Test ORM cascade behavior for IoTDevice -> Observation relationship.
Verifies that deleting an IoTDevice does NOT delete its observations.
"""

import sys
from unittest.mock import MagicMock
from app.db.models import Base, IoTDevice, Observation
from sqlalchemy import inspect


def test_iot_device_observation_relationship():
    """Test that IoTDevice.observations relationship has no delete-orphan cascade."""
    mapper = inspect(IoTDevice)
    
    # Find the observations relationship
    obs_rel = None
    for rel in mapper.relationships:
        if rel.key == "observations":
            obs_rel = rel
            break
    
    assert obs_rel is not None, "IoTDevice.observations relationship not found"
    
    # Check cascade options
    cascade = obs_rel.cascade
    print(f"Cascade options: {cascade}")
    
    # Should NOT have delete-orphan
    assert "delete-orphan" not in cascade, f"delete-orphan found in cascade: {cascade}"
    assert "delete" not in cascade, f"delete found in cascade: {cascade}"
    
    # Should have save-update, merge (default)
    assert "save-update" in cascade
    assert "merge" in cascade
    
    print("✅ IoTDevice.observations: No delete-orphan cascade (correct)")
    return True


def test_observation_iot_device_relationship():
    """Test Observation.iot_device relationship configuration."""
    mapper = inspect(Observation)
    
    iot_rel = None
    for rel in mapper.relationships:
        if rel.key == "iot_device":
            iot_rel = rel
            break
    
    assert iot_rel is not None, "Observation.iot_device relationship not found"
    
    # Should have foreign_keys pointing to iot_device_id
    local_cols = list(iot_rel.local_columns)
    assert len(local_cols) == 1
    assert local_cols[0].name == "iot_device_id"
    
    # The foreign key should have ondelete="SET NULL"
    fk = list(local_cols[0].foreign_keys)[0]
    assert fk.ondelete == "SET NULL", f"Expected SET NULL, got {fk.ondelete}"
    
    print("✅ Observation.iot_device: FK has ON DELETE SET NULL (correct)")
    return True


def test_other_relationships_cascade():
    """Verify other relationships that should have cascade."""
    # City -> iot_devices: ON DELETE CASCADE in migration, so delete-orphan OK
    city_mapper = inspect(IoTDevice.__bases__[0].__subclasses__()[0])  # City
    # Actually let's just check directly
    from app.db.models import City
    city_mapper = inspect(City)
    
    iot_rel = None
    for rel in city_mapper.relationships:
        if rel.key == "iot_devices":
            iot_rel = rel
            break
    
    assert iot_rel is not None
    cascade = iot_rel.cascade
    print(f"City.iot_devices cascade: {cascade}")
    # Migration has ON DELETE CASCADE, so delete-orphan is appropriate
    assert "delete-orphan" in cascade
    print("✅ City.iot_devices: Has delete-orphan cascade (matches ON DELETE CASCADE)")
    
    # City -> observations: ON DELETE CASCADE
    obs_rel = None
    for rel in city_mapper.relationships:
        if rel.key == "observations":
            obs_rel = rel
            break
    assert obs_rel is not None
    cascade = obs_rel.cascade
    assert "delete-orphan" in cascade
    print("✅ City.observations: Has delete-orphan cascade (matches ON DELETE CASCADE)")
    
    # EnvironmentalIndicator -> observations: ON DELETE CASCADE
    from app.db.models import EnvironmentalIndicator
    ind_mapper = inspect(EnvironmentalIndicator)
    obs_rel = None
    for rel in ind_mapper.relationships:
        if rel.key == "observations":
            obs_rel = rel
            break
    assert obs_rel is not None
    cascade = obs_rel.cascade
    assert "delete-orphan" in cascade
    print("✅ EnvironmentalIndicator.observations: Has delete-orphan cascade (matches ON DELETE CASCADE)")
    
    # RiskAssessment -> alerts: ON DELETE CASCADE
    from app.db.models import RiskAssessment
    risk_mapper = inspect(RiskAssessment)
    alerts_rel = None
    for rel in risk_mapper.relationships:
        if rel.key == "alerts":
            alerts_rel = rel
            break
    assert alerts_rel is not None
    cascade = alerts_rel.cascade
    assert "delete-orphan" in cascade
    print("✅ RiskAssessment.alerts: Has delete-orphan cascade (matches ON DELETE CASCADE)")
    
    # RiskAssessment -> recommendations: ON DELETE CASCADE
    rec_rel = None
    for rel in risk_mapper.relationships:
        if rel.key == "recommendations":
            rec_rel = rel
            break
    assert rec_rel is not None
    cascade = rec_rel.cascade
    assert "delete-orphan" in cascade
    print("✅ RiskAssessment.recommendations: Has delete-orphan cascade (matches ON DELETE CASCADE)")
    
    return True


def test_all_models_import():
    """Verify all models still import."""
    from app.db.models import (
        Base, City, EnvironmentalIndicator, IoTDevice, 
        Observation, RiskAssessment, Alert, 
        Recommendation, IngestionRejectionLog
    )
    
    tables = list(Base.metadata.tables.keys())
    expected = {
        'cities', 'environmental_indicators', 'iot_devices', 'observations',
        'risk_assessments', 'alerts', 'recommendations', 'ingestion_rejection_logs'
    }
    assert set(tables) == expected, f"Tables mismatch: {set(tables)} != {expected}"
    print("✅ All 8 models import successfully")
    return True


def main():
    print("=" * 60)
    print("ORM CASCADE BEHAVIOR TESTS")
    print("=" * 60)
    
    try:
        test_all_models_import()
        print()
        test_iot_device_observation_relationship()
        print()
        test_observation_iot_device_relationship()
        print()
        test_other_relationships_cascade()
        print()
        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)