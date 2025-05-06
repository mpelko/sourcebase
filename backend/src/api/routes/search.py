"""Search endpoints."""

from flask import Blueprint, Response, jsonify

bp = Blueprint("search", __name__, url_prefix="/api/v1/search")


@bp.route("/", methods=["POST"])
def search_documents() -> tuple[Response, int]:
    """Search documents using semantic search."""
    # TODO: Implement semantic search
    return jsonify({"message": "Not implemented"}), 501
