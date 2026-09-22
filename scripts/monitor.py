import argparse
import json
import signal
import sys
import time
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from confluent_kafka import Consumer

from trading.config import settings
from trading.events.topics import ALL_TOPICS
from trading.messaging.serialization import decode
from trading.monitor.render import CLEAR, HIDE_CURSOR, SHOW_CURSOR, frame
from trading.monitor.state import MonitorState

REFRESH = 0.25


def build_consumer(from_latest: bool) -> Consumer:
    return Consumer(
        {
            "bootstrap.servers": settings.bootstrap_servers,
            "group.id": f"monitor-{uuid4()}",
            "auto.offset.reset": "latest" if from_latest else "earliest",
            "enable.auto.commit": False,
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Live terminal view of the event flow")
    parser.add_argument("--from-latest", action="store_true", help="skip history, show only new events")
    args = parser.parse_args()

    state = MonitorState()
    consumer = build_consumer(args.from_latest)
    consumer.subscribe(ALL_TOPICS)

    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    print(CLEAR + HIDE_CURSOR, end="")
    drawn = 0.0
    try:
        while running:
            message = consumer.poll(0.1)
            if message is not None and not message.error():
                try:
                    state.apply(message.topic(), decode(message.value()))
                except (ValueError, KeyError, json.JSONDecodeError):
                    pass
            now = time.monotonic()
            if now - drawn >= REFRESH:
                print(frame(state, settings.bootstrap_servers), end="", flush=True)
                drawn = now
    finally:
        consumer.close()
        print(SHOW_CURSOR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
