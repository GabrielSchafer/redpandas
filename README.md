# Redpanda Trading Mock

Event-driven mock of a trading backend built on **Redpanda** (Kafka API) and **Python**.
The goal is to exercise event-driven patterns — commands, events, stream-built state, projections —
using a trading bank as the domain: accounts, cash, positions, orders, matching and settlement.

## Stack

| Piece | Choice |
| --- | --- |
| Broker | Redpanda (single node, `docker compose`) |
| Client | `confluent-kafka` 2.15 (librdkafka) |
| API | FastAPI + Uvicorn |
| State | In-memory, built from the log on first run |
| Tests | pytest (pure unit, no broker needed) |

## Architecture

```
HTTP (FastAPI)
  |  publishes commands
  v
trading.accounts.commands ---> [ledger-worker] ---> trading.accounts.events
trading.orders.commands   ---> [risk-worker]   ---> trading.orders.events
trading.orders.events     ---> [matching-worker] -> trading.trades.events
trading.trades.events     ---> [ledger-worker] ---> trading.ledger.events
                                      |
                       [api projection thread] -> read models (GET endpoints)
```

Each worker is an independent consumer group with its own in-memory state. On its first run a
group has no committed offsets, so it reads its topics from the earliest one and builds state from
the whole history. No database: the log is the source of truth.

Offsets are committed after each handled message, so a **restart resumes where the group stopped**
— with an empty in-memory state. Until a snapshot mechanism exists, rebuilding means rewinding the
group explicitly:

```bash
docker exec -it redpanda rpk group seek risk-worker-group --to start
```

| Service | Consumes | Produces | Responsibility |
| --- | --- | --- | --- |
| `ledger-worker` | accounts.commands, trades.events | accounts.events, ledger.events | Authoritative cash/positions, settlement, double-sided entries |
| `risk-worker` | orders.commands, accounts.events, trades.events, orders.events | orders.events | Validates order, reserves funds/assets, accepts or rejects |
| `matching-worker` | orders.events, orders.commands | trades.events, orders.events | Price-time priority order book, fills, cancels |
| `api` | accounts/orders/trades/ledger events | commands | REST surface + read-model projection |

## Event flow (happy path)

1. `POST /orders` publishes `order.requested` to `trading.orders.commands`.
2. `risk-worker` checks the account replica, reserves cash (buy) or shares (sell), emits `order.accepted`.
3. `matching-worker` runs it against the book, emits `trade.executed` plus `order.filled` / `order.partially_filled`.
4. `ledger-worker` settles the trade and emits `ledger.entry_recorded` and `position.updated`.
5. The API projection consumes every event topic and serves `GET /accounts/{id}`, `/orders/{id}`, `/market/trades`.

Diagrams, full event catalog and a trigger-to-reaction table: [docs/architecture.md](docs/architecture.md).

## Layout

```
src/trading/
  config.py           env-driven settings
  domain/             enums, money helpers, Account, Order, Trade
  events/             envelope, topics, event types, payload mappers
  messaging/          producer, consumer, router, serialization, topic admin
  services/           ledger, settlement, risk, order book, matching engine
  store/              read-model projections
  workers/            ledger, risk and matching workers (+ CLI runner)
  monitor/            state and renderer for the terminal dashboard
  api/                FastAPI app, routes, projection stream
scripts/              topic bootstrap, seed, terminal monitor, traffic bots
tests/                unit tests for matching, ledger and projections
```

## Running

Everything in Docker — broker, console, API and the three workers:

```bash
make up        # http://localhost:8080 console · http://localhost:8000/docs api
```

Watch it run, two terminals:

```bash
make monitor   # live terminal view of every topic, book and balance
make traffic   # three bots, one order every 1.5s
```

The panel and a five-minute walkthrough are described in [docs/demo.md](docs/demo.md);
`docs/roteiro-estudo.md` is a thirty-minute guide to studying and presenting the project.

For development without containers, run the broker only and start each process yourself:

Python 3.11 to 3.13 — the client ships wheels for all three, so nothing is compiled locally.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env

make broker    # only redpanda + console
make topics
make worker-ledger
make worker-risk
make worker-matching
make api
make seed      # 2 accounts, deposits, seller inventory, crossing orders
make test
```

## API

| Method | Path | Effect |
| --- | --- | --- |
| POST | `/accounts` | `account.open_requested` |
| POST | `/accounts/{id}/deposits` | `account.deposit_requested` |
| POST | `/accounts/{id}/withdrawals` | `account.withdraw_requested` |
| POST | `/accounts/{id}/assets` | `account.credit_asset_requested` (seed inventory) |
| GET | `/accounts/{id}` | balances and positions from the projection |
| POST | `/orders` | `order.requested` |
| DELETE | `/orders/{id}?symbol=` | `order.cancel_requested` |
| GET | `/orders/{id}` | order status from the projection |
| GET | `/market/trades` | recent trades |
| GET | `/market/prices` | last traded price per symbol |

Write endpoints return `202 Accepted`: the command is published, the result shows up in the
projection once the workers process it.

Example:

```bash
curl -X POST localhost:8000/accounts -H 'content-type: application/json' \
  -d '{"account_id":"acc-1","owner":"Alice"}'

curl -X POST localhost:8000/accounts/acc-1/deposits -H 'content-type: application/json' \
  -d '{"currency":"USD","amount":"10000"}'

curl -X POST localhost:8000/orders -H 'content-type: application/json' \
  -d '{"account_id":"acc-1","symbol":"AAPL","side":"buy","order_type":"limit","quantity":"10","price":"190"}'
```

## Configuration

| Variable | Default | Meaning |
| --- | --- | --- |
| `REDPANDA_BROKERS` | `localhost:19092` | Broker list |
| `TOPIC_PREFIX` | `trading` | Topic namespace |
| `TOPIC_PARTITIONS` | `3` | Partitions per topic |
| `TOPIC_REPLICATION` | `1` | Replication factor (single node) |
| `API_HOST` / `API_PORT` | `0.0.0.0` / `8000` | API bind |

## Mock scope

Deliberately simplified — the focus is the streaming architecture, not exchange realism.

- State is in-memory and lost on restart. The group resumes from its committed offsets instead of
  replaying, so a restarted worker is out of sync until its offsets are rewound (see above). The
  fix is snapshots, listed below.
- Ordering is guaranteed per partition (key = account or symbol), not across topics.
- Fill events are emitted for the taker; makers are updated from `trade.executed`.
- No fees, no auth, no persistence, no schema registry yet.

## Next steps

- Compacted snapshot topics, so a worker restores state on restart instead of replaying history.
- Schema Registry with Avro/Protobuf instead of plain JSON.
- Dead-letter handling on `trading.dead.letter`.
- Market data topic with order book snapshots.
