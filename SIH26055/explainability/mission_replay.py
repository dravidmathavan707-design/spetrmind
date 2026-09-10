"""Read-only replay of recorded cognitive scanning decisions and observations."""


class MissionReplay:
    def __init__(self, decisions=None, observations=None):
        self._events = []
        if decisions is not None or observations is not None:
            self.load(decisions or [], observations or [])

    def load(self, decisions, observations):
        """Load aligned decision/observation records in chronological order."""
        if len(decisions) != len(observations):
            raise ValueError("decisions and observations must have equal length")
        self._events = []
        for decision, observation in zip(decisions, observations):
            if not isinstance(decision, dict) or not isinstance(observation, dict):
                raise ValueError("each decision and observation must be a dictionary")
            if "time" not in decision or "band" not in decision:
                raise ValueError("each decision must contain time and band")
            if "time" not in observation or "band" not in observation:
                raise ValueError("each observation must contain time and band")
            if decision["time"] != observation["time"] or decision["band"] != observation["band"]:
                raise ValueError("decision and observation time/band must align")
            self._events.append({
                "time": decision["time"],
                "decision": dict(decision),
                "observation": dict(observation),
            })

    def replay(self):
        """Return copied events in recorded chronological order."""
        return [
            {
                "time": event["time"],
                "decision": dict(event["decision"]),
                "observation": dict(event["observation"]),
            }
            for event in self._events
        ]

    def event(self, index):
        if not isinstance(index, int) or not 0 <= index < len(self._events):
            raise IndexError("replay event index out of range")
        event = self._events[index]
        return {
            "time": event["time"],
            "decision": dict(event["decision"]),
            "observation": dict(event["observation"]),
        }

    def __len__(self):
        return len(self._events)

    def reset(self):
        self._events = []
