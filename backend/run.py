from src.api import app

if __name__ == "__main__":
    # Note: For development only. Use a production WSGI server for deployment.
    app.run(debug=True)
