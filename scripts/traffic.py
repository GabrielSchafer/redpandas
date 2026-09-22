import argparse
import random
import signal
import sys
import time
from collections import deque
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from trading.events.envelope import Event
from trading.events.topics import Topic
from trading.events.types import EventType
from trading.messaging.admin import ensure_topics
from trading.messaging.producer import EventProducer

NAMES = [
    ("alpha", "Ada"), ("beta", "Ben"), ("gamma", "Cleo"), ("delta", "Dara"),
    ("epsilon", "Eli"), ("zeta", "Zoe"), ("eta", "Hugo"), ("theta", "Tess"),
    ("iota", "Ivo"), ("kappa", "Kira"), ("lambda", "Luca"), ("mu", "Mira"),
]
CASH = "250000.00"
INVENTORY = "400"


def trader(index: int) -> tuple[str, str]:
    suffix, owner = NAMES[index % len(NAMES)]
    round_trip = index // len(NAMES)
    account_id = f"acc-{suffix}" if not round_trip else f"acc-{suffix}-{round_trip + 1}"
    return account_id, owner


def open_account(producer: EventProducer, account_id: str, owner: str, symbol: str, mid: float) -> None:
    producer.publish(
        Topic.ACCOUNT_COMMANDS,
        Event(EventType.ACCOUNT_OPEN_REQUESTED, account_id, {"account_id": account_id, "owner": owner, "base_currency": "USD"}),
    )
    producer.publish(
        Topic.ACCOUNT_COMMANDS,
        Event(EventType.DEPOSIT_REQUESTED, account_id, {"account_id": account_id, "currency": "USD", "amount": CASH}),
    )
    producer.publish(
        Topic.ACCOUNT_COMMANDS,
        Event(
            EventType.CREDIT_ASSET_REQUESTED,
            account_id,
            {"account_id": account_id, "symbol": symbol, "quantity": INVENTORY, "price": f"{mid:.2f}"},
        ),
    )


def bootstrap(producer: EventProducer, symbol: str, mid: float, count: int) -> list[str]:
    accounts = []
    for index in range(count):
        account_id, owner = trader(index)
        open_account(producer, account_id, owner, symbol, mid)
        accounts.append(account_id)
    producer.flush()
    return accounts


def build_order(symbol: str, mid: float, oversized: bool, accounts: list[str]) -> dict:
    side = random.choice(["buy", "sell"])
    offset = random.uniform(0.05, 0.30)
    aggressive = random.random() < 0.45
    if side == "buy":
        price = mid + offset if aggressive else mid - offset
    else:
        price = mid - offset if aggressive else mid + offset
    quantity = 9000 if oversized else random.randint(1, 12)
    return {
        "order_id": str(uuid4()),
        "account_id": random.choice(accounts),
        "symbol": symbol,
        "side": side,
        "order_type": "limit",
        "quantity": str(quantity),
        "price": f"{price:.2f}",
        "currency": "USD",
        "status": "pending",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Paced order flow for the demo")
    parser.add_argument("--symbol", default="AAPL")
    parser.add_argument("--interval", type=float, default=1.5, help="seconds between orders")
    parser.add_argument("--mid", type=float, default=190.0, help="starting reference price")
    parser.add_argument("--reject-rate", type=float, default=0.08, help="share of orders too large to pass risk")
    parser.add_argument("--cancel-rate", type=float, default=0.06, help="share of ticks that cancel a resting order")
    parser.add_argument("--accounts", type=int, default=5, help="traders funded on start")
    parser.add_argument("--join-every", type=int, default=0, help="open one more account every N orders, 0 disables")
    parser.add_argument("--orders", type=int, default=0, help="stop after N orders, 0 runs until ctrl-c")
    args = parser.parse_args()

    ensure_topics()
    producer = EventProducer(client_id="traffic")
    accounts = bootstrap(producer, args.symbol, args.mid, args.accounts)
    joined = len(accounts)
    print(f"{joined} accounts funded · one order every {args.interval}s · ctrl-c to stop")
    time.sleep(2)

    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    mid = args.mid
    resting: deque = deque(maxlen=40)
    sent = 0
    while running and (args.orders == 0 or sent < args.orders):
        mid = max(1.0, mid + random.uniform(-0.2, 0.2))
        payload = build_order(args.symbol, mid, random.random() < args.reject_rate, accounts)
        producer.publish(Topic.ORDER_COMMANDS, Event(EventType.ORDER_REQUESTED, payload["account_id"], payload))
        resting.append(payload["order_id"])
        sent += 1

        if args.join_every and sent % args.join_every == 0:
            account_id, owner = trader(joined)
            open_account(producer, account_id, owner, args.symbol, mid)
            accounts.append(account_id)
            joined += 1

        if resting and random.random() < args.cancel_rate:
            order_id = random.choice(resting)
            producer.publish(
                Topic.ORDER_COMMANDS,
                Event(EventType.ORDER_CANCEL_REQUESTED, args.symbol, {"order_id": order_id, "symbol": args.symbol}),
            )

        producer.flush(1.0)
        time.sleep(args.interval)

    producer.flush()
    print(f"\n{sent} orders published")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
