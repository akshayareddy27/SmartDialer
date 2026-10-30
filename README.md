# SmartDialer — Progressive & Predictive Dialing MVP

A small Python/FastAPI prototype demonstrating safe outbound call allocation.

## Features
- Progressive dialing: starts at most one call per request.
- Predictive pacing: estimates a conservative number of calls from free agents and configured answer rate.
- Independent safety controller: caps requested calls at currently available agents.
- Agent and call lifecycle states.
- Two mock providers: Provider A (reliable) and Provider B (simulated timeout/duplicate-event behaviour).
- Idempotent provider event handling and protection against late events overwriting terminal call states.
- Automated tests.

## Run locally (Python 3.10+)
```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows cmd:
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs for interactive API documentation.

## Run tests
```bash
python -m pytest -q
```

## API demo
- `GET /state` — current agents, calls and queue.
- `POST /dial/progressive` — start one call.
- `POST /dial/predictive` — use rule-based pacing.
- `POST /events` — process provider event (JSON: `event_id`, `call_id`, `status`).
- `POST /demo/provider-outage` — switch to a failing mock provider.

## Architecture
Campaign/API → Pacing Engine → Safety Controller → Call Allocator → Provider interface → Mock provider.

The predictive engine only proposes a quantity. The safety controller applies the hard capacity limit before allocation.

## Important prototype limitations
This is an educational, single-process MVP. The Python lock protects concurrent reservations only inside one running process; it is not a distributed lock. State is in memory and is lost on restart. A production implementation would use transactional persistent storage, unique idempotency constraints, durable event inbox/outbox, leases/heartbeats, provider circuit breakers and multi-worker coordination.

## Design decisions
- Python + FastAPI keep the prototype small and easy to run.
- In-memory state keeps the time-boxed demonstration simple; SQLite/PostgreSQL is the next step for durable state.
- Rule-based pacing is explainable and deliberately conservative.
- Safety is separate from pacing and independently enforces the available-agent cap.

## Additional failure and demo endpoints
- `POST /recovery/stale-reservations` with `{"call_ids":[1]}` simulates lease-expiry recovery for stale in-flight calls.
- `POST /demo/provider-outage` switches to a timeout provider; repeated failures open a simple circuit breaker and stop new dialing.
- `GET /simulation/scenarios` returns deterministic A-D pacing examples.
- `GET /metrics` returns calls initiated, connected/answered, busy agents and utilization.
- `POST /demo/reset` resets the in-memory simulator.
- `python load_test.py` runs a small single-process throughput smoke test.

## Expanded test coverage
The tests cover progressive dialing, safety capacity, provider failure release, duplicate events, terminal-state protection, stale reservation recovery and stale event ordering.

## Limitations (important)
Crash recovery is demonstrated through an explicit stale-call recovery endpoint; it is not automatic durable lease recovery. The circuit breaker is a simple prototype. The load test is a local smoke test, not a production benchmark. State is in memory and the lock is process-local. Multi-worker production deployment requires durable database transactions, leases/heartbeats and shared idempotency storage.
