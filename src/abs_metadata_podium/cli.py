import argparse

from abs_metadata_podium.app import create_app
from abs_metadata_podium.config import load_config_from_env


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="abs-metadata-podium",
        description="Audiobookshelf custom metadata provider for Podium Entertainment",
    )
    parser.add_argument("--host", help="Override ABS_METADATA_PODIUM_HOST")
    parser.add_argument("--port", type=int, help="Override ABS_METADATA_PODIUM_PORT")
    parser.add_argument("--token", help="Override ABS_METADATA_PODIUM_TOKEN")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    config = load_config_from_env()
    if args.host:
        config.host = args.host
    if args.port:
        config.port = args.port
    if args.token:
        config.auth_token = args.token

    app = create_app(config)
    app.run(host=config.host, port=config.port)
    return 0
