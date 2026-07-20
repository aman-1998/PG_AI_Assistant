"""Run text_to_sql_backend with:  python run.py"""
from __future__ import annotations

import os

import uvicorn

from config.settings import settings

if __name__ == "__main__":
    # Only watch this backend package for reloads. Launching from the workspace
    # root would otherwise make uvicorn watch the whole repo (frontend, etc.),
    # restarting the server on unrelated file changes and briefly dropping
    # requests mid-use.
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        reload_dirs=[backend_dir],
    )
