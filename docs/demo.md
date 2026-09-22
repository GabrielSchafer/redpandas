# Demo

Two terminals and a browser tab are enough to show the whole system working.

## Setup

```bash
make up        # broker, console, api and the three workers, all in Docker
make monitor   # terminal 1 — live view of every topic
make traffic   # terminal 2 — one order every 1.5s from three bots
```

`make up` builds the image on first run, so give it a minute before recording.
Redpanda Console is at `localhost:8080`, the API at `localhost:8000/docs`.

To start from a clean log: `make down && make up`.

## The panel

```
REDPANDA TRADING MOCK                          localhost:19092 · 14:32:07 UTC · 215 events
──────────────────────────────────────────────────────────────────────────────────────────
TOPICS                   msgs  last                TAPE      topic            event
accounts.events            12  account.assets…     14:32:07  trades.events    trade.executed
orders.commands            42  order.requested     14:32:06  orders.events    order.accepted
orders.events              80  order.accepted      14:32:06  orders.commands  order.requested
trades.events              31  trade.executed
ledger.events              62  position.updated

BOOK AAPL                 qty       price          ACCOUNTS         cash    reserved   AAPL
  ask                      12      191.20          acc-alpha  241,110.00    1,900.00    412
  ask                       8      190.90          acc-beta   258,760.00        0.00    388
  last traded                      190.75          acc-gamma  249,980.00      570.00    400
  bid                       5      190.40
  bid                       9      190.10
```

| Pane | Built from | Shows |
| --- | --- | --- |
| Topics | every topic | How many messages each one holds and the last type that landed |
| Tape | every topic | The raw event stream, newest first — green for fills, red for rejections |
| Book | `orders.events` | A shadow order book, replayed with the same matching engine the worker runs |
| Accounts | `accounts.events` + `ledger.events` | Cash, reserved cash and position per account |

The monitor is read-only and owns a throwaway consumer group, so it never disturbs the workers.

## Five-minute script

| Time | Show | Say |
| --- | --- | --- |
| 0:00 | `README.md` diagram | A trading bank where services never call each other — they react to a log |
| 0:30 | `make up`, `docker compose ps` | One broker, one API, three workers, each an independent consumer group |
| 1:00 | `make monitor` on an empty log | Nothing happened yet: the panel is the log, folded |
| 1:20 | `make traffic` | Bots place orders; watch the counters move topic by topic |
| 2:00 | Tape pane | One order crossing four topics: requested → accepted → executed → entry recorded |
| 2:40 | Book and accounts panes | Reserved cash rising on resting orders, position moving only after a trade |
| 3:10 | A red line in the tape | Risk rejecting an oversized order before it ever reaches the book |
| 3:30 | Console → Topics → a message | The envelope: type, key, `correlation_id`, payload |
| 4:00 | Console → filter by `correlation_id` | The same order's life across every topic |
| 4:20 | Console → Consumer Groups | Three groups reading the same topics at their own offsets, with lag |
| 4:40 | `docker compose stop matching-worker`, then tape | Orders keep being accepted and pile up — no trades until it comes back |
| 5:00 | Close | The log is the source of truth; every service is a fold over it |

## Recording tips

- Terminal at 120×40 or wider, large font: the panel adapts up to 130 columns.
- Dark theme: the colours are tuned for it (orange accent, green fills, red rejections).
- `--interval 2.5` on `make traffic` slows the flow down if 1.5s reads too fast on video.
- `python scripts/monitor.py --from-latest` skips history when the log already has thousands of events.
