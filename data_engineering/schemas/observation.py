from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime

class Observation(BaseModel):
    sensor_id: str
    metric: str
    value: float
    unit: str
    timestamp: datetime
    city_id: str

class RejectRecord(BaseModel):
    raw_data: Any
    reason: str
