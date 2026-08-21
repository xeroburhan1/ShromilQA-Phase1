from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = None


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: str
    citations: list[dict] | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: MessageOut
    citations: list[dict] = Field(default_factory=list)


class SessionOut(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class SessionDetailOut(SessionOut):
    messages: list[MessageOut]
