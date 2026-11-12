from pydantic import BaseModel, Field
from typing import List, Any
from data_engineering.schemas.observation import Observation, RejectRecord

class ProcessResult(BaseModel):
    accepted: List[Observation] = Field(default_factory=list)
    rejected: List[RejectRecord] = Field(default_factory=list)
    
    def add_rejection(self, raw_data: Any, reason: str):
        self.rejected.append(RejectRecord(raw_data=raw_data, reason=reason))
