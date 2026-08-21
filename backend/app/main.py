from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .rag.retrieve import get_index
from .routers import chat

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)


@app.on_event("startup")
def on_startup():
    init_db()
    index = get_index()
    from .config import settings as _settings
    print(f"[{_settings.ASSISTANT_NAME}] RAG index ready: {len(index.sections)} sections loaded.")


@app.get("/api/health")
def health():
    return {"status": "ok", "assistant": settings.ASSISTANT_NAME}
