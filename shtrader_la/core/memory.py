"""Conversation memory.

`MemoryStore` is the interface the orchestrator depends on. Only an in-process
implementation exists: no database, no network, nothing that breaks offline use.
A persistent store can be added later without touching the agent.
"""

from __future__ import annotations

import abc
from collections import defaultdict, deque
from typing import Any, Deque, Dict, List

from ..llm.base import Message

DEFAULT_MAX_TURNS = 8


class MemoryStore(abc.ABC):
    @abc.abstractmethod
    def append(self, session_id: str, role: str, content: str) -> None: ...

    @abc.abstractmethod
    def history(self, session_id: str) -> List[Message]: ...

    @abc.abstractmethod
    def facts(self, session_id: str) -> Dict[str, Any]: ...

    @abc.abstractmethod
    def remember(self, session_id: str, **facts: Any) -> None: ...

    @abc.abstractmethod
    def clear(self, session_id: str) -> None: ...


class SessionMemory(MemoryStore):
    """Bounded in-memory transcript plus a small sticky fact store.

    Facts let a trader say "my balance is $1,000" once and have later messages
    ("size a BTC long for me") resolve deterministically.
    """

    def __init__(self, max_turns: int = DEFAULT_MAX_TURNS) -> None:
        self.max_turns = max_turns
        self._turns: Dict[str, Deque[Message]] = defaultdict(lambda: deque(maxlen=max_turns * 2))
        self._facts: Dict[str, Dict[str, Any]] = defaultdict(dict)

    def append(self, session_id: str, role: str, content: str) -> None:
        self._turns[session_id].append(Message(role=role, content=content))

    def history(self, session_id: str) -> List[Message]:
        return list(self._turns.get(session_id, []))

    def facts(self, session_id: str) -> Dict[str, Any]:
        return dict(self._facts.get(session_id, {}))

    def remember(self, session_id: str, **facts: Any) -> None:
        clean = {k: v for k, v in facts.items() if v is not None}
        if clean:
            self._facts[session_id].update(clean)

    def clear(self, session_id: str) -> None:
        self._turns.pop(session_id, None)
        self._facts.pop(session_id, None)

    def sessions(self) -> List[str]:
        return sorted(set(self._turns) | set(self._facts))
