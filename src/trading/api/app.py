import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..messaging.admin import ensure_topics
from .deps import stream
from .routes import accounts, market, orders

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_topics()
    stream.start()
    yield
    stream.stop()


app = FastAPI(title="Redpanda Trading Mock", version="0.1.0", lifespan=lifespan)
app.include_router(accounts.router)
app.include_router(orders.router)
app.include_router(market.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
