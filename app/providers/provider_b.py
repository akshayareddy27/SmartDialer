from .base import TelecomProvider


class ProviderB(TelecomProvider):
    """
    Simulated unreliable telecom provider.

    Supports:
    - Timeouts
    - Duplicate events
    - Out-of-order event sequences
    """

    def __init__(
        self,
        fail=False,
        duplicate_events=True,
        out_of_order=False
    ):
        self.fail = fail
        self.duplicate_events = duplicate_events
        self.out_of_order = out_of_order

    def initiate_call(self, borrower_id: int, agent_id: int) -> dict:

        if self.fail:
            raise TimeoutError("Provider B timed out")

        events = [
            {
                "event_id": f"B-{borrower_id}-1",
                "borrower_id": borrower_id,
                "agent_id": agent_id,
                "status": "RINGING"
            },
            {
                "event_id": f"B-{borrower_id}-2",
                "borrower_id": borrower_id,
                "agent_id": agent_id,
                "status": "ANSWERED"
            }
        ]

        if self.out_of_order:
            events.reverse()

        if self.duplicate_events:
            events.append(dict(events[-1]))

        return {
            "provider": "B",
            "status": "RINGING",
            "events": events
        }