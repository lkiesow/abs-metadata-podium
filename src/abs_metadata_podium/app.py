import logging

from flask import Flask, jsonify, request

from abs_metadata_podium import podium
from abs_metadata_podium.config import Config


def _configure_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("abs_metadata_podium").setLevel(level)


def create_app(config: Config) -> Flask:
    _configure_logging(config.debug)

    app = Flask(__name__)
    app.logger.setLevel(logging.DEBUG if config.debug else logging.INFO)

    if not config.auth_token:
        app.logger.warning(
            "ABS_METADATA_PODIUM_TOKEN is not set - the /search endpoint will accept "
            "requests without checking the AUTHORIZATION header."
        )

    @app.get("/search")
    def search_route():
        query = request.args.get("query")
        author = request.args.get("author")
        app.logger.debug("Received /search request: query=%r author=%r", query, author)

        if config.auth_token:
            supplied = request.headers.get("AUTHORIZATION")
            if supplied != config.auth_token:
                app.logger.debug("Rejecting request: missing or incorrect AUTHORIZATION header")
                return jsonify({"error": "Unauthorized"}), 401

        if not query:
            app.logger.debug("Rejecting request: 'query' parameter is missing")
            return jsonify({"error": "'query' parameter is required"}), 400

        try:
            results = podium.search(query, author=author)
        except Exception:
            app.logger.exception("search failed for query=%r", query)
            return jsonify({"error": "Internal error while searching Podium"}), 500

        matches = [book.to_dict() for book in results]
        app.logger.debug("Returning %d match(es) for query=%r: %s", len(matches), query, matches)
        return jsonify({"matches": matches})

    return app
