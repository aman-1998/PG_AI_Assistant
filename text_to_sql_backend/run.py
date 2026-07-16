"""Run text_to_sql_backend with:  python run.py"""
from __future__ import annotations

import uvicorn

from config.settings import settings

if __name__ == "__main__":
    uvicorn.run("app:app", host=settings.HOST, port=settings.PORT, reload=True)
