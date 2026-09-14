from ..config import settings


def _topic(name: str) -> str:
    return f"{settings.topic_prefix}.{name}"


class Topic:
    ACCOUNT_COMMANDS = _topic("accounts.commands")
    ACCOUNT_EVENTS = _topic("accounts.events")
    ORDER_COMMANDS = _topic("orders.commands")
    ORDER_EVENTS = _topic("orders.events")
    TRADE_EVENTS = _topic("trades.events")
    LEDGER_EVENTS = _topic("ledger.events")
    DEAD_LETTER = _topic("dead.letter")


ALL_TOPICS = [
    Topic.ACCOUNT_COMMANDS,
    Topic.ACCOUNT_EVENTS,
    Topic.ORDER_COMMANDS,
    Topic.ORDER_EVENTS,
    Topic.TRADE_EVENTS,
    Topic.LEDGER_EVENTS,
    Topic.DEAD_LETTER,
]
