"""Initializes the Flask app."""

from flask import Flask

app = Flask(__name__)


# Sample route
@app.route("/hello")
def hello() -> str:
    return "Hello, World!"


# Import routes from other modules if you structure them separately
# For example, if you have a user_routes.py:
# from . import user_routes
