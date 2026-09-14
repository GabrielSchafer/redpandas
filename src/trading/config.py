import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    bootstrap_servers: str
    topic_prefix: str
    api_host: str
    api_port: int
    default_partitions: int
    default_replication: int


def load_settings() -> Settings:
    return Settings(
        bootstrap_servers=os.getenv("REDPANDA_BROKERS", "localhost:19092"),
        topic_prefix=os.getenv("TOPIC_PREFIX", "trading"),
        api_host=os.getenv("API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("API_PORT", "8000")),
        default_partitions=int(os.getenv("TOPIC_PARTITIONS", "3")),
        default_replication=int(os.getenv("TOPIC_REPLICATION", "1")),
    )


settings = load_settings()
