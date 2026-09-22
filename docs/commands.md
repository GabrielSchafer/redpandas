# Commands

Everything you need to run the mock, watch it and poke at it.

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt          # python 3.11 – 3.13, wheels only
```

The venv is needed only for the monitor, the traffic bots and the tests — the services
themselves run in containers.

## Stack

| Command | What it does |
| --- | --- |
| `make up` | Builds and starts broker, console, api and the three workers |
| `docker compose ps` | Should list 6 containers in `running` |
| `make logs` | Follows the logs of api and workers |
| `docker compose stop matching-worker` | Kills one service without touching the rest |
| `docker compose start matching-worker` | Brings it back; it resumes from its offset |
| `docker compose restart api` | Restarts a single service |
| `make down` | Stops everything and **deletes the log** (`-v`) |
| `docker compose stop` | Pauses without losing data |

First `make up` pulls images and builds the Python image — give it a couple of minutes.

## Watch it

| Command | What it does |
| --- | --- |
| `make monitor` | Terminal panel: topic counters, tape, shadow book, balances |
| `python scripts/monitor.py --from-latest` | Skips history when the log is already large |
| `make traffic` | Three bots, one order every 1.5s |
| `python scripts/traffic.py --interval 2.5` | Slower flow, easier to read on video |
| `python scripts/traffic.py --orders 20` | Stops after 20 orders |
| `python scripts/traffic.py --reject-rate 0.2` | More rejections, to show risk refusing orders |
| `python scripts/traffic.py --accounts 10` | Funds 10 traders on start instead of 5 |
| `python scripts/traffic.py --join-every 8` | Opens one more account every 8 orders, live |
| `make seed` | One-shot: two accounts and a single crossing pair |

## Poke at the API

```bash
curl localhost:8000/health

curl -X POST localhost:8000/accounts -H 'content-type: application/json' \
  -d '{"account_id":"acc-1","owner":"Alice"}'

curl -X POST localhost:8000/accounts/acc-1/deposits -H 'content-type: application/json' \
  -d '{"currency":"USD","amount":"10000"}'

curl -X POST localhost:8000/accounts/acc-1/assets -H 'content-type: application/json' \
  -d '{"symbol":"AAPL","quantity":"50","price":"190.00"}'

curl -X POST localhost:8000/orders -H 'content-type: application/json' \
  -d '{"account_id":"acc-1","symbol":"AAPL","side":"sell","order_type":"limit","quantity":"10","price":"190.00"}'

curl localhost:8000/accounts/acc-1
curl localhost:8000/market/trades
curl localhost:8000/market/prices
```

Writes answer `202`: the command is on the log and the projection catches up a moment later.
Interactive docs at `localhost:8000/docs`.

## Inspect the log

```bash
docker exec -it redpanda rpk topic list
docker exec -it redpanda rpk topic consume trading.orders.events -o start
docker exec -it redpanda rpk group list
docker exec -it redpanda rpk group describe risk-worker-group      # offsets and lag
docker exec -it redpanda rpk group seek risk-worker-group --to start
```

Redpanda Console: `localhost:8080`.

## Tests

```bash
make test                       # 11 unit tests, no broker needed
PYTHONPATH=src pytest -k matching   # a subset
```

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `Failed building wheel for confluent-kafka` | Python older than the pin supports — `pip install -r requirements-dev.txt` on 3.11–3.13 |
| Panel stays empty | Check `REDPANDA_BROKERS` (default `localhost:19092`) and that `make up` finished |
| Panel takes long to open | `python scripts/monitor.py --from-latest` |
| Workers restarting in a loop | Broker still booting; check `docker compose logs risk-worker` |
| `port is already allocated` | Free 8000, 8080 or 19092, or change the mapping in `docker-compose.yml` |
| Orders all rejected | The bots fund their own accounts on start; wait for `account.funds_deposited` in the tape |
