import logging

from flask import Flask, jsonify, request

from abs_metadata_podium import podium
from abs_metadata_podium.config import Config


def create_app(config: Config) -> Flask:
    app = Flask(__name__)
    app.logger.setLevel(logging.INFO)

    if not config.auth_token:
        app.logger.warning(
            "ABS_METADATA_PODIUM_TOKEN is not set - the /search endpoint will accept "
            "requests without checking the AUTHORIZATION header."
        )

    @app.get("/search")
    def search_route():
        if config.auth_token:
            supplied = request.headers.get("AUTHORIZATION")
            if supplied != config.auth_token:
                return jsonify({"error": "Unauthorized"}), 401

        query = request.args.get("query")
        if not query:
            return jsonify({"error": "'query' parameter is required"}), 400
        author = request.args.get("author")

        try:
            results = podium.search(query, author=author)
        except Exception:
            app.logger.exception("search failed for query=%r", query)
            return jsonify({"error": "Internal error while searching Podium"}), 500

        return jsonify({"matches": [book.to_dict() for book in results]})

    return app
