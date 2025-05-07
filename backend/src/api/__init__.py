"""Initializes the Flask app."""

import os
import sqlite3

import click  # Add click import for CLI commands
from flask import Flask

app: Flask = Flask(
    __name__, instance_path=None
)  # instance_path will be derived from config

# Load configuration from src.config
# Make sure this path is correct relative to where the app is run from or use absolute
# imports if project is packaged
app.config.from_object("src.config")

# Ensure the instance folder from config is used if needed,
# or that paths in config.py are absolute or correctly relative.
# Flask's instance_relative_config=True might be useful if instance folder is relative
# to app root.
# For now, config.py creates an absolute path to instance folder.


# Sample route
@app.route("/hello")
def hello() -> str:
    return "Hello, World!"


# Import routes from other modules if you structure them separately
# For example, if you have a user_routes.py:
# from . import user_routes

# You might want to initialize your database connection here or in a separate module
# For example, using Flask-SQLAlchemy:
# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy(app)
# from . import models # if you have a models.py with your table definitions

# Or using sqlite3 directly:


def get_db_connection() -> sqlite3.Connection:
    # Ensure the database path from config is absolute or correctly resolved
    db_path = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
    if not os.path.isabs(db_path):
        # Assuming INSTANCE_FOLDER in config.py is an absolute path or relative to
        # BASE_DIR
        # This logic might need adjustment based on how SQLALCHEMY_DATABASE_URI is
        # constructed in config.py
        # For now, we assume it's an absolute path or correctly relative path that
        # sqlite3.connect can handle.
        pass  # If it's not absolute, sqlite3 will create it relative to CWD of `flask run` or `python run.py`  # noqa: E501

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    db_path = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
    # Ensure instance directory exists before trying to connect/create DB
    instance_dir = os.path.dirname(db_path)
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
        print(f"Created instance directory: {instance_dir}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT,
            pub_date TEXT, 
            doc_type TEXT NOT NULL,
            date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()
    # click.echo will print to console when CLI command is run
    # print(f"Database initialized at {db_path}") # Use click.echo for CLI commands


# Flask CLI command to initialize the database
@app.cli.command("init-db")
def init_db_command() -> None:
    """Clear existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")
