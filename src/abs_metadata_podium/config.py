import os
from dataclasses import dataclass


@dataclass
class Config:
    auth_token: str | None = None
    host: str = "0.0.0.0"
    port: int = 8000


def load_config_from_env() -> Config:
    return Config(
        auth_token=os.environ.get("ABS_METADATA_PODIUM_TOKEN") or None,
        host=os.environ.get("ABS_METADATA_PODIUM_HOST", "0.0.0.0"),
        port=int(os.environ.get("ABS_METADATA_PODIUM_PORT", "8000")),
    )
