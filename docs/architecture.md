# Architecture notes

## Diagrams

Mermaid blocks: they render on GitHub, VS Code, Obsidian and any Markdown viewer with mermaid support.

### Topology

```mermaid
flowchart LR
    API([HTTP API]):::edge
    GET([GET endpoints]):::edge

    AC[(accounts.commands)]:::topic
    AE[(accounts.events)]:::topic
    OC[(orders.commands)]:::topic
    OE[(orders.events)]:::topic
    TE[(trades.events)]:::topic
    LE[(ledger.events)]:::topic

    LEDGER[ledger-worker]:::svc
    RISK[risk-worker]:::svc
    MATCH[matching-worker]:::svc
    PROJ[api projection]:::svc

    API -->|deposits, assets| AC --> LEDGER -->|balances| AE
    API -->|order.requested| OC --> RISK -->|accepted / rejected| OE
    OE --> MATCH -->|trade.executed| TE --> LEDGER -->|entries, positions| LE
    MATCH -->|filled / partially_filled| OE
    AE -.->|rebuilds replica| RISK
    TE -.->|replica settlement| RISK
    AE & OE & TE & LE --> PROJ --> GET

    classDef topic fill:#f7e6e1,stroke:#c8341a,color:#121721
    classDef svc fill:#f5f7f9,stroke:#121721,color:#121721
    classDef edge fill:none,stroke:#5c6874,stroke-dasharray:4 3,color:#121721
```

Topics are the only integration point: no service calls another service directly.

### Order lifecycle

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant A as API
    participant R as risk-worker
    participant M as matching-worker
    participant L as ledger-worker
    participant P as projection

    C->>A: POST /orders
    A->>A: mint order_id
    A-->>C: 202 Accepted
    A->>R: order.requested (orders.commands)
    R->>R: check replica, reserve cash or shares
    alt rejected
        R->>P: order.rejected
    else accepted
        R->>M: order.accepted (orders.events)
        M->>M: cross against the book
        M->>L: trade.executed (trades.events)
        M->>P: order.filled / order.partially_filled
        L->>L: release reservation, settle cash and position
        L->>P: ledger.entry_recorded, position.updated
        L->>R: accounts.events keep the replica in sync
    end
    C->>A: GET /accounts/{id}
    A-->>C: balances and positions from the projection
```

### Order status

```mermaid
stateDiagram-v2
    [*] --> pending: order.requested
    pending --> rejected: risk refused
    pending --> accepted: funds reserved
    accepted --> partially_filled: partial cross
    accepted --> filled: full cross
    partially_filled --> filled: remainder crossed
    accepted --> cancelled: cancel requested
    partially_filled --> cancelled: cancel requested
    rejected --> [*]
    filled --> [*]
    cancelled --> [*]
```

## Topics

| Topic | Key | Written by | Read by |
| --- | --- | --- | --- |
| `trading.accounts.commands` | `account_id` | api, seed | ledger-worker |
| `trading.accounts.events` | `account_id` | ledger-worker | risk-worker, api |
| `trading.orders.commands` | `account_id` / `symbol` | api, seed | risk-worker, matching-worker |
| `trading.orders.events` | `symbol` / `account_id` | risk-worker, matching-worker | matching-worker, risk-worker, api |
| `trading.trades.events` | `symbol` | matching-worker | ledger-worker, risk-worker, api |
| `trading.ledger.events` | `account_id` | ledger-worker | api |
| `trading.dead.letter` | source key | reserved | — |

## Event catalog

### Commands

| Type | Payload |
| --- | --- |
| `account.open_requested` | `account_id`, `owner`, `base_currency` |
| `account.deposit_requested` | `account_id`, `currency`, `amount` |
| `account.withdraw_requested` | `account_id`, `currency`, `amount` |
| `account.credit_asset_requested` | `account_id`, `symbol`, `quantity`, `price` |
| `order.requested` | `order_id`, `account_id`, `symbol`, `side`, `order_type`, `quantity`, `price`, `currency` |
| `order.cancel_requested` | `order_id`, `symbol` |

### Events

| Type | Payload |
| --- | --- |
| `account.opened` | `account_id`, `owner`, `base_currency` |
| `account.funds_deposited` / `account.funds_withdrawn` | `account_id`, `currency`, `amount`, `available`, `reserved` |
| `account.assets_credited` | `account_id`, `symbol`, `quantity`, `reserved`, `average_price`, `credited_quantity`, `price` |
| `account.command_rejected` | `command`, `reason`, `payload` |
| `order.accepted` / `order.rejected` | order snapshot (+ `reason` when rejected) |
| `order.partially_filled` / `order.filled` | order snapshot with `filled_quantity` |
| `order.cancelled` | `order_id`, `symbol` |
| `trade.executed` | `trade_id`, `symbol`, `price`, `quantity`, order ids, account ids, `taker_side` |
| `ledger.entry_recorded` | `account_id`, `trade_id`, `symbol`, `currency`, `amount`, `type` |
| `position.updated` | `account_id`, `symbol`, `quantity`, `reserved`, `average_price` |

## Envelope

Every message is JSON with the same envelope:

```json
{
  "event_id": "uuid",
  "type": "order.accepted",
  "key": "AAPL",
  "correlation_id": "uuid of the originating command",
  "occurred_at": "2026-09-14T12:00:00+00:00",
  "payload": {}
}
```

`correlation_id` is propagated from command to derived events, so a full flow can be traced
in Redpanda Console by filtering on it.

## Delivery semantics

- Producers: idempotent, `acks=all`.
- Consumers: manual commit after the handler succeeds — at-least-once, so handlers must
  tolerate reprocessing (the mock is not fully idempotent yet; see Next steps).
- Partitioning: account-keyed topics keep per-account ordering; symbol-keyed topics keep the
  book consistent per instrument, which is why the matching worker must own one symbol set.

## Money

`Decimal` everywhere, serialized as strings. Cash quantized to 2 decimals, quantities to 8.
Never floats.
