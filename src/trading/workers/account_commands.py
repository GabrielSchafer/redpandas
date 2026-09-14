from decimal import Decimal

from ..events.envelope import Event
from ..events.topics import Topic
from ..events.types import EventType
from ..services.ledger import LedgerError


class AccountCommandsMixin:
    """Handlers for the account command topic, used by the ledger worker."""

    def open_account(self, event: Event) -> None:
        payload = event.payload
        try:
            account = self.ledger.open_account(payload["account_id"], payload["owner"], payload.get("base_currency"))
        except LedgerError as error:
            return self.reject(event, str(error))
        self.emit(
            Topic.ACCOUNT_EVENTS,
            EventType.ACCOUNT_OPENED,
            account.account_id,
            {"account_id": account.account_id, "owner": account.owner, "base_currency": account.base_currency},
            event,
        )

    def deposit(self, event: Event) -> None:
        self._move_funds(event, EventType.FUNDS_DEPOSITED, self.ledger.deposit)

    def withdraw(self, event: Event) -> None:
        self._move_funds(event, EventType.FUNDS_WITHDRAWN, self.ledger.withdraw)

    def credit_assets(self, event: Event) -> None:
        payload = event.payload
        try:
            self.ledger.credit_asset(
                payload["account_id"], payload["symbol"], Decimal(payload["quantity"]), Decimal(payload["price"])
            )
        except LedgerError as error:
            return self.reject(event, str(error))
        position = self.ledger.get(payload["account_id"]).position(payload["symbol"])
        self.emit(
            Topic.ACCOUNT_EVENTS,
            EventType.ASSETS_CREDITED,
            payload["account_id"],
            {
                "account_id": payload["account_id"],
                "symbol": payload["symbol"],
                "quantity": str(position.quantity),
                "reserved": str(position.reserved),
                "average_price": str(position.average_price),
                "credited_quantity": payload["quantity"],
                "price": payload["price"],
            },
            event,
        )

    def reject(self, event: Event, reason: str) -> None:
        self.emit(
            Topic.ACCOUNT_EVENTS,
            EventType.ACCOUNT_COMMAND_REJECTED,
            event.key,
            {"command": event.type, "reason": reason, "payload": event.payload},
            event,
        )

    def _move_funds(self, event: Event, event_type: str, operation) -> None:
        payload = event.payload
        try:
            balance = operation(payload["account_id"], payload["currency"], Decimal(payload["amount"]))
        except LedgerError as error:
            return self.reject(event, str(error))
        self.emit(
            Topic.ACCOUNT_EVENTS,
            event_type,
            payload["account_id"],
            {
                "account_id": payload["account_id"],
                "currency": balance.currency,
                "amount": payload["amount"],
                "available": str(balance.available),
                "reserved": str(balance.reserved),
            },
            event,
        )
