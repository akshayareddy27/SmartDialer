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
