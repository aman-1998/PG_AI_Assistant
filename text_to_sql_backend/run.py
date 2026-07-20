"""Run text_to_sql_backend with:  python run.py"""
from __future__ import annotations

import os
import sys

import uvicorn

from config.settings import settings

if __name__ == "__main__":
    # In a frozen desktop build there is no source tree to watch and the reloader
    # (which re-execs the interpreter) does not work inside a PyInstaller bundle,
    # so run the imported app object directly without reload.
    if getattr(sys, "frozen", False):
        from app import app

        uvicorn.run(app, host=settings.HOST, port=settings.PORT)
    else:
        # Only watch this backend package for reloads. Launching from the
        # workspace root would otherwise make uvicorn watch the whole repo
        # (frontend, etc.), restarting the server on unrelated file changes and
        # briefly dropping requests mid-use.
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        uvicorn.run(
            "app:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=True,
            reload_dirs=[backend_dir],
        )
