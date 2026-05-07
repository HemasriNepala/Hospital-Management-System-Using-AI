"""WSGI entrypoint for production servers (Gunicorn)."""
from app import create_app

app = create_app()

