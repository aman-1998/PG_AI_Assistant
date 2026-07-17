"""FastAPI application bootstrap for text_to_sql_backend."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from core.agent import clear_cache as clear_agent_cache
from db.postgres import init_db
from routes import auth, chat, database_connections, feedback, health, llm_config, rag_uploads
from services import mcp_client_service
from services.llm_factory import clear_cache as clear_llm_cache
from services.rag import rag_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    rag_db.init_schema()
    yield
    clear_agent_cache()
    clear_llm_cache()
    mcp_client_service.clear_all()


app = FastAPI(title="Text-to-SQL Postgres Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(database_connections.router)
app.include_router(llm_config.router)
app.include_router(chat.router)
app.include_router(rag_uploads.router)
app.include_router(feedback.router)
