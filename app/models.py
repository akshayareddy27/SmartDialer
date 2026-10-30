from enum import Enum
from dataclasses import dataclass

class AgentState(str, Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    CONNECTED = "CONNECTED"
    WRAP_UP = "WRAP_UP"
    OFFLINE = "OFFLINE"

class CallState(str, Enum):
    QUEUED = "QUEUED"
    RESERVED = "RESERVED"
    INITIATED = "INITIATED"
    RINGING = "RINGING"
    ANSWERED = "ANSWERED"
    CONNECTED = "CONNECTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

@dataclass
class Agent:
    id: int
    state: AgentState = AgentState.AVAILABLE

@dataclass
class Borrower:
    id: int
    phone: str
    state: str = "QUEUED"
