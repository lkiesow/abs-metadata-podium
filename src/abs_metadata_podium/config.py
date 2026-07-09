import os
from dataclasses import dataclass


@dataclass
class Config:
    auth_token: str | None = None
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False


def _parse_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in ("1", "true", "yes", "on")


def load_config_from_env() -> Config:
    return Config(
        auth_token=os.environ.get("ABS_METADATA_PODIUM_TOKEN") or None,
        host=os.environ.get("ABS_METADATA_PODIUM_HOST", "0.0.0.0"),
        port=int(os.environ.get("ABS_METADATA_PODIUM_PORT", "8000")),
        debug=_parse_bool(os.environ.get("ABS_METADATA_PODIUM_DEBUG")),
    )
