from fastapi import FastAPI
from pydantic import BaseModel
from .engine import SmartDialer
from .providers.provider_a import ProviderA
from .providers.provider_b import ProviderB

app = FastAPI(title="SmartDialer MVP", version="1.1.0")
dialer = SmartDialer()
class DialRequest(BaseModel): count: int = 1
class EventRequest(BaseModel): event_id: str; call_id: int; status: str
class RecoveryRequest(BaseModel): call_ids: list[int]

@app.get("/")
def home(): return {"project":"SmartDialer", "message":"API is running", "docs":"/docs"}
@app.get("/health")
def health(): return {"status":"ok"}
@app.get("/state")
def state(): return dialer.snapshot()
@app.get("/metrics")
def metrics(): return dialer.metrics()
@app.post("/dial/progressive")
def progressive(): return {"started":dialer.progressive_dial(), "state":dialer.snapshot()}
@app.post("/dial/predictive")
def predictive(): return {"started":dialer.predictive_pacing(), "state":dialer.snapshot()}
@app.post("/dial/request")
def dial_request(request: DialRequest):
    started = dialer.start_calls(request.count)
    return {"requested":request.count, "approved":len(started), "started":started, "state":dialer.snapshot()}
@app.post("/events")
def provider_event(event: EventRequest): return dialer.handle_event(event.event_id,event.call_id,event.status)
@app.post("/recovery/stale-reservations")
def recover(request: RecoveryRequest): return {"recovered_call_ids":dialer.recover_stale_reservations(request.call_ids)}
@app.post("/demo/provider-outage")
def provider_outage():
    global dialer
    dialer = SmartDialer(provider=ProviderB(fail=True))
    return {"message":"Provider B timeout simulation enabled; repeated failures open circuit"}
@app.post("/demo/reset")
def reset():
    global dialer
    dialer = SmartDialer()
    return {"message":"Simulation reset"}
@app.get("/simulation/scenarios")
def scenarios():
    results=[]
    for label, rate, talk in [("A",.20,120),("B",.50,90),("C",.70,180),("D",.10,240)]:
        sim=SmartDialer(agent_count=10,answer_rate=rate)
        started=sim.predictive_pacing()
        results.append({"scenario":label,"answer_rate":rate,"avg_talk_time_seconds":talk,
                        "calls_started":len(started),"metrics":sim.metrics()})
    return {"scenarios":results,"note":"Deterministic rule-based demonstration, not a statistically validated forecast."}
