"""Chat endpoints."""

from flask import Blueprint, Response, jsonify

bp = Blueprint("chat", __name__, url_prefix="/api/v1/chat")


@bp.route("/", methods=["POST"])
def chat() -> tuple[Response, int]:
    """Chat with context from documents."""
    # TODO: Implement chat functionality
    return jsonify({"message": "Not implemented"}), 501
