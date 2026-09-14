import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from trading.events.topics import ALL_TOPICS
from trading.messaging.admin import ensure_topics


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    ensure_topics()
    print("\n".join(ALL_TOPICS))


if __name__ == "__main__":
    main()
