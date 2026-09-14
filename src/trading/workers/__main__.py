import logging
import sys

from ..messaging.admin import ensure_topics
from .ledger_worker import LedgerWorker
from .matching_worker import MatchingWorker
from .risk_worker import RiskWorker

WORKERS = {"ledger": LedgerWorker, "matching": MatchingWorker, "risk": RiskWorker}


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    if len(sys.argv) != 2 or sys.argv[1] not in WORKERS:
        print(f"usage: python -m trading.workers <{'|'.join(WORKERS)}>", file=sys.stderr)
        return 1
    ensure_topics()
    WORKERS[sys.argv[1]]().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
