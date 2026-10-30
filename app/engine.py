from math import ceil 
from threading import Lock
from .models import Agent, AgentState, Borrower, CallState
from .providers.provider_a import ProviderA
class SafetyController:
    """Independent component that enforces outbound dialing limits."""

    def decide(self, requested, available_agents, provider_open=False):
        requested = max(0, int(requested))

        if provider_open:
            return {
                "requested": requested,
                "approved": 0,
                "reason": "provider_circuit_open"
            }

        approved = min(requested, max(0, available_agents))

        return {
            "requested": requested,
            "approved": approved,
            "reason": "approved" if approved > 0 else "no_capacity"
        }
class SmartDialer:
    """Single-process prototype. Lock protects atomic in-process reservations."""
    def __init__(self, agent_count=3, answer_rate=0.4, provider=None):
        self.agents = {i: Agent(i) for i in range(1, agent_count + 1)}
        self.borrowers = [Borrower(i, f"+910000000{i:03d}") for i in range(1, 101)]
        self.calls, self.processed_events = [], set()
        self.lock = Lock()
        self.answer_rate = max(0.0, min(1.0, answer_rate))
        self.provider = provider or ProviderA()
        self.safety_log = []
        self.safety = SafetyController()
        self.provider_failures = 0
        self.provider_open = False

    def available_agents(self):
        return [a for a in self.agents.values() if a.state == AgentState.AVAILABLE]

    def safety_controller(self, requested):
        with self.lock:
            decision = self.safety.decide(
                requested=requested,
                available_agents=len(self.available_agents()),
                provider_open=self.provider_open
            )

            self.safety_log.append(decision.copy())
            return decision["approved"]

    def progressive_dial(self):
        return self.start_calls(1)

    def predictive_pacing(
        self,
        avg_talk_time_seconds=120,
        pacing_window_seconds=60
    ):
        free = len(self.available_agents())
        queued = sum(
            b.state == "QUEUED" for b in self.borrowers
        )

        if avg_talk_time_seconds <= 0 or pacing_window_seconds <= 0:
            return []

        requested = ceil(
            free
            * self.answer_rate
            * pacing_window_seconds
            / avg_talk_time_seconds
        )

        requested = min(queued, requested)

        return self.start_calls(requested)
    def start_calls(self, requested):
        started = []

        with self.lock:
            decision = self.safety.decide(
                requested=requested,
                available_agents=len(self.available_agents()),
                provider_open=self.provider_open
            )

            self.safety_log.append(decision.copy())
            approved = decision["approved"]

            if approved == 0:
                return []

            for agent in self.agents.values():
                if len(started) >= approved:
                    break

                if agent.state != AgentState.AVAILABLE:
                    continue

                borrower = next(
                    (b for b in self.borrowers if b.state == "QUEUED"),
                    None
                )

                if borrower is None:
                    break

                agent.state = AgentState.RESERVED
                borrower.state = "RESERVED"

                call = {
                    "id": len(self.calls) + 1,
                    "agent_id": agent.id,
                    "borrower_id": borrower.id,
                    "state": CallState.RESERVED.value
                }

                self.calls.append(call)
                started.append(call)

        for call in started:
            try:
                call["provider_result"] = self.provider.initiate_call(
                    call["borrower_id"], call["agent_id"]
                )

                call["state"] = CallState.RINGING.value
                self.borrowers[call["borrower_id"] - 1].state = "RINGING"
                self.provider_failures = 0

            except Exception as exc:
                call.update(
                    state=CallState.FAILED.value,
                    error=str(exc)
                )

                with self.lock:
                    self.borrowers[call["borrower_id"] - 1].state = "QUEUED"
                    self.agents[call["agent_id"]].state = AgentState.AVAILABLE

                    self.provider_failures += 1

                    if self.provider_failures >= 2:
                        self.provider_open = True

        return started
    def process_provider_events(self, call_id, provider_result=None):
        """Process provider events through the idempotent event handler."""

        with self.lock:
            call = next(
                (c for c in self.calls if c["id"] == call_id),
                None
            )

            if call is None:
                return []

            result = provider_result or call.get("provider_result", {})

        events = result.get("events", [])
        results = []

        for event in events:
            result = self.handle_event(
                event_id=event["event_id"],
                call_id=call_id,
                status=event["status"]
            )

            results.append(result)

        return results
    def recover_stale_reservations(self, stale_call_ids):
        """Demo recovery hook: release reservations for calls whose worker lease expired."""
        recovered = []
        with self.lock:
            for call in self.calls:
                if call["id"] in stale_call_ids and call["state"] in ("RESERVED", "INITIATED", "RINGING"):
                    call["state"] = CallState.CANCELLED.value
                    self.agents[call["agent_id"]].state = AgentState.AVAILABLE
                    self.borrowers[call["borrower_id"] - 1].state = "QUEUED"
                    recovered.append(call["id"])
        return recovered

    def handle_event(self, event_id, call_id, status):
        with self.lock:
            if event_id in self.processed_events:
                return {"accepted": False, "reason": "duplicate"}
            call = next((c for c in self.calls if c["id"] == call_id), None)
            if not call:
                return {"accepted": False, "reason": "unknown_call"}
            if call["state"] in ("COMPLETED", "FAILED", "CANCELLED"):
                return {"accepted": False, "reason": "terminal_state"}
            allowed = {"RINGING": "RINGING", "ANSWERED": "ANSWERED", "COMPLETED": "COMPLETED", "FAILED": "FAILED"}
            if status not in allowed:
                return {"accepted": False, "reason": "unsupported_status"}
            # Do not let a late RINGING event regress an answered call.
            if call["state"] == "ANSWERED" and status == "RINGING":
                self.processed_events.add(event_id)
                return {"accepted": False, "reason": "stale_event"}
            self.processed_events.add(event_id)
            call["state"] = allowed[status]
            agent, borrower = self.agents[call["agent_id"]], self.borrowers[call["borrower_id"] - 1]
            if status in ("COMPLETED", "FAILED"):
                agent.state, borrower.state = AgentState.AVAILABLE, status
            elif status == "ANSWERED":
                agent.state, borrower.state = AgentState.CONNECTED, "ANSWERED"
            return {"accepted": True, "state": call["state"]}

    def metrics(self):
        total = len(self.calls)
        connected = sum(c["state"] in ("ANSWERED", "CONNECTED", "COMPLETED") for c in self.calls)
        busy = sum(a.state != AgentState.AVAILABLE for a in self.agents.values())
        return {"calls_initiated": total, "calls_connected_or_answered": connected,
                "available_agents": len(self.available_agents()), "busy_agents": busy,
                "agent_utilization_pct": round(100 * busy / len(self.agents), 2) if self.agents else 0,
                "provider_circuit_open": self.provider_open}

    def snapshot(self):
        return {"agents": {str(k): v.state.value for k, v in self.agents.items()},
                "calls": self.calls, "queued_borrowers": sum(b.state == "QUEUED" for b in self.borrowers),
                "safety_decisions": self.safety_log, "metrics": self.metrics()}
