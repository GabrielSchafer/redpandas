import logging

from confluent_kafka.admin import AdminClient, NewTopic

from ..config import settings
from ..events.topics import ALL_TOPICS

logger = logging.getLogger(__name__)


def ensure_topics(topics: list[str] | None = None) -> None:
    admin = AdminClient({"bootstrap.servers": settings.bootstrap_servers})
    existing = set(admin.list_topics(timeout=10).topics)
    wanted = topics or ALL_TOPICS
    missing = [
        NewTopic(name, settings.default_partitions, settings.default_replication)
        for name in wanted
        if name not in existing
    ]
    if not missing:
        return
    for name, future in admin.create_topics(missing).items():
        future.result()
        logger.info("topic created: %s", name)
