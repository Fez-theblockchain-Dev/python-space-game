"""Backend APIs package for the space game."""

# Export the FastAPI app from server module for easy access
from backend_apis.server import app

__all__ = ["app"]


API_BASE_LAYER="(e.g. http://localhost:8000)"