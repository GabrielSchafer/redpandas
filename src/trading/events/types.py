class EventType:
    ACCOUNT_OPEN_REQUESTED = "account.open_requested"
    DEPOSIT_REQUESTED = "account.deposit_requested"
    WITHDRAW_REQUESTED = "account.withdraw_requested"
    CREDIT_ASSET_REQUESTED = "account.credit_asset_requested"

    ACCOUNT_OPENED = "account.opened"
    FUNDS_DEPOSITED = "account.funds_deposited"
    FUNDS_WITHDRAWN = "account.funds_withdrawn"
    ASSETS_CREDITED = "account.assets_credited"
    ACCOUNT_COMMAND_REJECTED = "account.command_rejected"

    ORDER_REQUESTED = "order.requested"
    ORDER_CANCEL_REQUESTED = "order.cancel_requested"
    ORDER_ACCEPTED = "order.accepted"
    ORDER_REJECTED = "order.rejected"
    ORDER_CANCELLED = "order.cancelled"
    ORDER_PARTIALLY_FILLED = "order.partially_filled"
    ORDER_FILLED = "order.filled"

    TRADE_EXECUTED = "trade.executed"
    LEDGER_ENTRY_RECORDED = "ledger.entry_recorded"
    POSITION_UPDATED = "position.updated"
