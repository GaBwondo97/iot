from data_engineering.schemas.observation import Observation

class Deduplicator:
    def __init__(self):
        self.seen_signatures = set()
        
    def is_unique(self, obs: Observation) -> bool:
        sig = f"{obs.sensor_id}_{obs.timestamp.isoformat()}_{obs.metric}"
        if sig in self.seen_signatures:
            return False
        self.seen_signatures.add(sig)
        return True
