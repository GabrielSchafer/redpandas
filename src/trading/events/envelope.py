from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Event:
    type: str
    key: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: str | None = None
    occurred_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "type": self.type,
            "key": self.key,
            "correlation_id": self.correlation_id,
            "occurred_at": self.occurred_at,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        return cls(
            type=data["type"],
            key=data["key"],
            payload=data.get("payload", {}),
            event_id=data.get("event_id", str(uuid4())),
            correlation_id=data.get("correlation_id"),
            occurred_at=data.get("occurred_at", _now()),
        )
