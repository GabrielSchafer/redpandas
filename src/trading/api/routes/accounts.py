from fastapi import APIRouter, Depends, HTTPException

from ...events.envelope import Event
from ...events.topics import Topic
from ...events.types import EventType
from ..deps import get_producer, get_projection
from ..schemas import AccountRequest, AssetRequest, CommandAccepted, FundsRequest

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("", response_model=CommandAccepted, status_code=202)
def open_account(body: AccountRequest, producer=Depends(get_producer)) -> CommandAccepted:
    event = Event(type=EventType.ACCOUNT_OPEN_REQUESTED, key=body.account_id, payload=body.model_dump())
    producer.publish(Topic.ACCOUNT_COMMANDS, event)
    return CommandAccepted(event_type=event.type, reference=body.account_id)


@router.post("/{account_id}/deposits", response_model=CommandAccepted, status_code=202)
def deposit(account_id: str, body: FundsRequest, producer=Depends(get_producer)) -> CommandAccepted:
    return _funds_command(EventType.DEPOSIT_REQUESTED, account_id, body, producer)


@router.post("/{account_id}/withdrawals", response_model=CommandAccepted, status_code=202)
def withdraw(account_id: str, body: FundsRequest, producer=Depends(get_producer)) -> CommandAccepted:
    return _funds_command(EventType.WITHDRAW_REQUESTED, account_id, body, producer)


@router.post("/{account_id}/assets", response_model=CommandAccepted, status_code=202)
def credit_assets(account_id: str, body: AssetRequest, producer=Depends(get_producer)) -> CommandAccepted:
    payload = {
        "account_id": account_id,
        "symbol": body.symbol,
        "quantity": str(body.quantity),
        "price": str(body.price),
    }
    event = Event(type=EventType.CREDIT_ASSET_REQUESTED, key=account_id, payload=payload)
    producer.publish(Topic.ACCOUNT_COMMANDS, event)
    return CommandAccepted(event_type=event.type, reference=account_id)


@router.get("/{account_id}")
def read_account(account_id: str, projection=Depends(get_projection)) -> dict:
    account = projection.accounts.get(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="account not projected yet")
    return {"account_id": account_id, **account}


def _funds_command(event_type: str, account_id: str, body: FundsRequest, producer) -> CommandAccepted:
    payload = {"account_id": account_id, "currency": body.currency, "amount": str(body.amount)}
    event = Event(type=event_type, key=account_id, payload=payload)
    producer.publish(Topic.ACCOUNT_COMMANDS, event)
    return CommandAccepted(event_type=event_type, reference=account_id)
