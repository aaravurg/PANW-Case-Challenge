"""
Entry point for running the FastAPI backend server.
Usage: uvicorn run:app --reload
"""

from app.main import app

__all__ = ['app']
