"""Small local throughput smoke test; run: python load_test.py"""
from time import perf_counter
from app.engine import SmartDialer

N=1000
start=perf_counter()
d=SmartDialer(agent_count=100)
for _ in range(N):
    d.progressive_dial()
elapsed=perf_counter()-start
print(f"{N} progressive dial requests in {elapsed:.4f}s ({N/elapsed:.1f} requests/sec)")
print("Final metrics:", d.metrics())
print("Note: in-memory single-process smoke test, not a production load benchmark.")
