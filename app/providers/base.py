from abc import ABC, abstractmethod

class TelecomProvider(ABC):
    @abstractmethod
    def initiate_call(self, borrower_id: int, agent_id: int) -> dict:
        raise NotImplementedError
