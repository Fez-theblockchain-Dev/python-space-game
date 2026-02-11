"""Backend APIs package for the space game."""

# Note: FastAPI app lives in server.py at project root (from server import app)
# Avoid importing app here to prevent circular import (server imports backend_apis.*)

__all__: list[str] = []

API_BASE_LAYER = "(e.g. http://localhost:8000)"