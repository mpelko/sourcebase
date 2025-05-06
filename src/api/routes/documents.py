"""Document management endpoints."""

from flask import Blueprint, Response, jsonify

bp = Blueprint("documents", __name__, url_prefix="/api/v1/documents")


@bp.route("/", methods=["POST"])
def add_document() -> tuple[Response, int]:
    """Add a new document."""
    # TODO: Implement document addition
    return jsonify({"message": "Not implemented"}), 501


@bp.route("/", methods=["GET"])
def list_documents() -> tuple[Response, int]:
    """List all documents."""
    # TODO: Implement document listing
    return jsonify({"message": "Not implemented"}), 501


@bp.route("/<document_id>", methods=["GET"])
def get_document(document_id: str) -> tuple[Response, int]:
    """Get a specific document."""
    # TODO: Implement document retrieval
    return jsonify({"message": "Not implemented"}), 501


@bp.route("/<document_id>", methods=["DELETE"])
def delete_document(document_id: str) -> tuple[Response, int]:
    """Delete a specific document."""
    # TODO: Implement document deletion
    return jsonify({"message": "Not implemented"}), 501
