# backend/tests/test_core.py
import os
import sqlite3

import pytest
from src.api import app as flask_app
from src.api import get_db_connection, init_db

TEST_DB_NAME = "test_metadata.db"


@pytest.fixture
def app_instance():
    """Create and configure a new app instance for each test."""
    base_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )  # Should point to backend/
    instance_folder = os.path.join(base_dir, "instance")
    if not os.path.exists(instance_folder):
        os.makedirs(instance_folder)

    test_db_path = os.path.join(instance_folder, TEST_DB_NAME)

    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    flask_app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{test_db_path}",
        }
    )
    # Pushing an app context allows tests to access app.config and other
    # app-specific features. pytest-flask handles this automatically for its
    # `app` and `client` fixtures.
    with flask_app.app_context():
        yield flask_app  # Provide the configured app

    # Teardown: remove the temporary database file
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture
def client(app_instance):
    """A test client for the app."""
    return app_instance.test_client()


@pytest.fixture
def runner(app_instance):
    """A test runner for the app's Click commands."""
    return app_instance.test_cli_runner()


def test_hello_route(client):
    """Test the /hello route."""
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.data == b"Hello, World!"


def test_init_db_command(runner, app_instance):
    """Test the init-db CLI command."""
    # app_instance fixture ensures the app uses the test DB
    result = runner.invoke(args=["init-db"])
    assert "Initialized the database." in result.output

    db_path = app_instance.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
    assert os.path.exists(db_path), "Database file should be created."

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='documents';"
    )
    table_exists = cursor.fetchone()
    conn.close()
    assert table_exists is not None, "'documents' table should exist."


def test_get_db_connection_after_init(app_instance):
    """Test get_db_connection after DB is initialized."""
    # The app_instance fixture pushes an app context.
    # init_db uses app.config which is set up by app_instance
    init_db()

    conn = None
    try:
        conn = get_db_connection()
        assert isinstance(
            conn, sqlite3.Connection
        ), "Should return a sqlite3.Connection."

        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        assert cursor.fetchone() is not None, "Query should succeed."
    finally:
        if conn:
            conn.close()


def test_init_db_function_directly(app_instance):
    """Test the init_db function directly."""
    # app_instance provides the app context and test DB config
    init_db()
    db_path = app_instance.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
    assert os.path.exists(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='documents';"
    )
    table_exists = cursor.fetchone()
    conn.close()
    assert table_exists is not None, "Table 'documents' should be created."
