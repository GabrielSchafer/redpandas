from fastapi import APIRouter, Depends

from ..deps import get_projection

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/trades")
def recent_trades(symbol: str | None = None, limit: int = 20, projection=Depends(get_projection)) -> list[dict]:
    trades = list(projection.trades)
    if symbol:
        trades = [trade for trade in trades if trade["symbol"] == symbol]
    return trades[:limit]


@router.get("/prices")
def last_prices(projection=Depends(get_projection)) -> dict[str, str]:
    return projection.last_price
