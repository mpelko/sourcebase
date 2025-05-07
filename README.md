# SourceBase

A document processing and LLM interaction system that allows users to work with large documents as a knowledge base for LLM conversations.

## Features

- Document ingestion and processing
- Vector-based semantic search
- LLM-powered document querying
- Extensible architecture for different vector databases and LLM providers

## Requirements

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager

## Installation

This project uses [uv](https://github.com/astral-sh/uv) as its package manager. To install:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/yourusername/sourcebase.git
cd sourcebase

# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package in development mode with test dependencies
uv pip install -e ".[test]"

# Install pre-commit hooks
pre-commit install
```

## Development

The project uses:
- [Ruff](https://github.com/astral-sh/ruff) for linting and formatting
- [Mypy](https://mypy-lang.org/) for static type checking
- [Pytest](https://docs.pytest.org/) for testing
- [pre-commit](https://pre-commit.com/) for git hooks

To run the linters and tests:

```bash
# Format code
ruff format .

# Check types
mypy backend/src/

# Run tests
pytest

# Run tests with coverage
pytest --cov

# Run pre-commit hooks manually
pre-commit run --all-files
```

## License

MIT 

## Running the Backend Server

To run the Flask development server:

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Run the application:
   ```bash
   python run.py
   ```

The server will start, typically on `http://127.0.0.1:5000/`. You can access the sample `/hello` route at `http://120.0.1:5000/hello`. 