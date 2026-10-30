# Architecture Decision Record

## 1. Architecture
The SmartDialer uses a modular Python and FastAPI architecture.

The main flow is:
Campaign API -> Pacing Engine -> Safety Controller -> Call Allocator -> Telecom Provider.

## 2. Technology Decisions

- Python: Simple and readable implementation.
- FastAPI: REST API interface.
- Threading Lock: Atomic reservation within a single process.
- Mock Providers: Simulate telecom provider behaviour.
- Pytest: Automated testing.

## 3. Pacing Strategy

The prototype uses rule-based predictive pacing based on available agents and estimated answer rate. Progressive mode starts one call per request.

## 4. Safety Strategy

The system applies a hard limit based on available agents before allocating calls. Predictive pacing cannot directly initiate provider calls.

## 5. Failure Handling

The prototype demonstrates provider timeouts, failed call cleanup, duplicate event rejection, stale event protection and manual stale-reservation recovery.

## 6. Current Limitations

State is stored in memory. Locks operate within one process only. Crash recovery is simulated rather than automatically recovered from durable storage.

## 7. Production Improvements

A production version would use transactional database reservations, distributed coordination, durable event processing, worker leases, provider health monitoring and automatic recovery.
