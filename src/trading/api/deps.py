from ..messaging.producer import EventProducer
from .stream import ProjectionStream

producer = EventProducer(client_id="trading-api")
stream = ProjectionStream()


def get_producer() -> EventProducer:
    return producer


def get_projection():
    return stream.projection
