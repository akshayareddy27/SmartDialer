from app.engine import SmartDialer
from app.models import AgentState
from app.providers.provider_b import ProviderB

def test_progressive_starts_one(): assert len(SmartDialer(agent_count=5).progressive_dial()) == 1

def test_safety_caps_at_available_agents():
 d=SmartDialer(agent_count=2); calls=d.start_calls(100); assert len(calls)==2; assert d.start_calls(100)==[]

def test_provider_failure_releases_agent():
 d=SmartDialer(agent_count=1,provider=ProviderB(fail=True)); call=d.progressive_dial()[0]
 assert call['state']=='FAILED' and d.agents[1].state==AgentState.AVAILABLE

def test_duplicate_event_ignored():
 d=SmartDialer(agent_count=1); c=d.progressive_dial()[0]
 assert d.handle_event('e1',c['id'],'ANSWERED')['accepted']
 assert not d.handle_event('e1',c['id'],'COMPLETED')['accepted']

def test_terminal_call_not_reopened():
 d=SmartDialer(agent_count=1); c=d.progressive_dial()[0]
 d.handle_event('e1',c['id'],'COMPLETED')
 assert not d.handle_event('e2',c['id'],'ANSWERED')['accepted']

def test_stale_reservation_recovery():
 d=SmartDialer(agent_count=1); c=d.progressive_dial()[0]
 assert d.recover_stale_reservations([c['id']])==[c['id']]
 assert d.agents[1].state==AgentState.AVAILABLE

def test_late_ringing_does_not_regress_answered():
 d=SmartDialer(agent_count=1); c=d.progressive_dial()[0]
 d.handle_event('e1',c['id'],'ANSWERED')
 assert not d.handle_event('e2',c['id'],'RINGING')['accepted']
def test_safety_controller_rejects_when_provider_open():
    d = SmartDialer(agent_count=3)
    d.provider_open = True

    assert d.safety_controller(3) == 0


def test_safety_controller_never_exceeds_available_agents():
    d = SmartDialer(agent_count=2)

    approved = d.safety_controller(100)

    assert approved == 2


def test_concurrent_workers_cannot_reserve_same_agent():
    from concurrent.futures import ThreadPoolExecutor

    d = SmartDialer(agent_count=1)

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(
            executor.map(lambda _: d.start_calls(1), range(10))
        )

    total_started = sum(len(result) for result in results)

    assert total_started == 1
    assert len(d.calls) == 1
def test_provider_b_duplicate_events_are_ignored():
    d = SmartDialer(
        agent_count=1,
        provider=ProviderB(duplicate_events=True)
    )

    call = d.progressive_dial()[0]

    results = d.process_provider_events(call["id"])

    assert results[0]["accepted"] is True
    assert results[-1]["accepted"] is False
    assert results[-1]["reason"] == "duplicate"


def test_provider_b_out_of_order_events_do_not_regress_state():
    d = SmartDialer(
        agent_count=1,
        provider=ProviderB(
            duplicate_events=False,
            out_of_order=True
        )
    )

    call = d.progressive_dial()[0]

    results = d.process_provider_events(call["id"])

    assert any(r.get("reason") == "stale_event" for r in results)
    assert call["state"] == "ANSWERED"
    assert d.agents[call["agent_id"]].state == AgentState.CONNECTED