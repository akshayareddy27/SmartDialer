from .base import TelecomProvider

class ProviderA(TelecomProvider):
    """Fast, reliable deterministic mock provider."""
    def initiate_call(self, borrower_id: int, agent_id: int) -> dict:
        return {"provider": "A", "status": "RINGING",
                "borrower_id": borrower_id, "agent_id": agent_id}
