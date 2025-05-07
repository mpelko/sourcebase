import os

# Define the base directory of the backend application
# This assumes config.py is in backend/src/
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INSTANCE_FOLDER = os.path.join(BASE_DIR, "instance")

# Ensure the instance folder exists
if not os.path.exists(INSTANCE_FOLDER):
    os.makedirs(INSTANCE_FOLDER)

# SQLite database configuration
DATABASE_NAME = "metadata.db"
SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(INSTANCE_FOLDER, DATABASE_NAME)}"

# Other configurations can be added here
# For example:
# SECRET_KEY = os.environ.get('SECRET_KEY', 'a_default_secret_key')
# DEBUG = True
