"""WSGI entry point for the application."""

from . import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
