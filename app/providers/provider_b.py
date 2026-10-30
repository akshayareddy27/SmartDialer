from .base import TelecomProvider

class ProviderB(TelecomProvider):
    """Mock provider that can simulate timeouts and duplicate events."""
    def __init__(self, fail: bool = False):
        self.fail = fail

    def initiate_call(self, borrower_id: int, agent_id: int) -> dict:
        if self.fail:
            raise TimeoutError("Provider B timed out")
        event = {"provider": "B", "status": "RINGING",
                 "borrower_id": borrower_id, "agent_id": agent_id}
        return {"event": event, "duplicate_event": dict(event)}
