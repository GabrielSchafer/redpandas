import sys
import time
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from trading.events.envelope import Event
from trading.events.topics import Topic
from trading.events.types import EventType
from trading.messaging.admin import ensure_topics
from trading.messaging.producer import EventProducer

SYMBOL = "AAPL"
ACCOUNTS = [("acc-buyer", "Alice"), ("acc-seller", "Bob")]


def account_commands(producer: EventProducer) -> None:
    for account_id, owner in ACCOUNTS:
        payload = {"account_id": account_id, "owner": owner, "base_currency": "USD"}
        producer.publish(Topic.ACCOUNT_COMMANDS, Event(EventType.ACCOUNT_OPEN_REQUESTED, account_id, payload))
        deposit = {"account_id": account_id, "currency": "USD", "amount": "100000.00"}
        producer.publish(Topic.ACCOUNT_COMMANDS, Event(EventType.DEPOSIT_REQUESTED, account_id, deposit))
    assets = {"account_id": "acc-seller", "symbol": SYMBOL, "quantity": "50", "price": "185.00"}
    producer.publish(Topic.ACCOUNT_COMMANDS, Event(EventType.CREDIT_ASSET_REQUESTED, "acc-seller", assets))


def order_command(producer: EventProducer, account_id: str, side: str, price: str, qty: str) -> str:
    order_id = str(uuid4())
    payload = {
        "order_id": order_id,
        "account_id": account_id,
        "symbol": SYMBOL,
        "side": side,
        "order_type": "limit",
        "quantity": qty,
        "price": price,
        "currency": "USD",
        "status": "pending",
    }
    producer.publish(Topic.ORDER_COMMANDS, Event(EventType.ORDER_REQUESTED, account_id, payload))
    return order_id


def main() -> None:
    ensure_topics()
    producer = EventProducer(client_id="seed")
    account_commands(producer)
    producer.flush()
    time.sleep(2)

    sell_id = order_command(producer, "acc-seller", "sell", "190.00", "10")
    buy_id = order_command(producer, "acc-buyer", "buy", "190.00", "10")
    producer.flush()
    print(f"sell order: {sell_id}\nbuy order: {buy_id}")


if __name__ == "__main__":
    main()
