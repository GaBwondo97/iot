class BaselineTracker:
    def __init__(self):
        self.history = {}
        self.std_floor = 0.5
