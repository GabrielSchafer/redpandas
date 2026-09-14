import json
from decimal import Decimal
from typing import Any

from ..events.envelope import Event


def _default(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"unsupported type: {type(value)!r}")


def encode(event: Event) -> bytes:
    return json.dumps(event.to_dict(), default=_default).encode("utf-8")


def decode(raw: bytes) -> Event:
    return Event.from_dict(json.loads(raw.decode("utf-8")))
