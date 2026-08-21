from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import database as db
from ..config import settings
from ..groq_client import get_chat_completion
from ..models import ChatRequest, ChatResponse, MessageOut, SessionDetailOut, SessionOut
from ..rag.retrieve import get_index, retrieve_context
from ..system_prompt import SYSTEM_PROMPT

router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/sections/{section_number}")
def get_section_detail(section_number: int):
    index = get_index()
    sec = index.get_by_number(section_number)
    if not sec:
        raise HTTPException(status_code=404, detail=f"Section {section_number} not found")
    return {"section": sec.number, "title": sec.title, "chapter": sec.chapter, "text": sec.text}


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions():
    return db.list_sessions()


@router.post("/sessions", response_model=SessionOut)
def new_session():
    return db.create_session()


@router.get("/sessions/{session_id}", response_model=SessionDetailOut)
def get_session(session_id: str):
    session = db.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {**session, "messages": db.get_messages(session_id)}


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    db.delete_session(session_id)
    return {"ok": True}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id
    if session_id:
        db.ensure_session(session_id)
    else:
        session_id = db.create_session()["id"]

    is_first_message = len(db.get_messages(session_id)) == 0

    db.add_message(session_id, "user", req.message)
    if is_first_message:
        db.rename_session_if_default(session_id, req.message)

    # --- Retrieval (architecture report §4.8): find relevant Act sections ---
    context_block, citations = retrieve_context(req.message)

    # Build the context window sent to the model: system prompt + retrieved
    # context (as a separate system-role message, so it's clearly distinct
    # from conversation history) + recent history.
    history = db.get_messages(session_id)[-(settings.MAX_HISTORY_TURNS * 2):]
    llm_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if context_block:
        llm_messages.append(
            {
                "role": "system",
                "content": "Retrieved sections from the Bangladesh Labour Act 2006, "
                "relevant to the user's latest message:\n\n" + context_block,
            }
        )
    llm_messages += [{"role": m["role"], "content": m["content"]} for m in history]

    reply_text = await get_chat_completion(llm_messages)

    reply = db.add_message(session_id, "assistant", reply_text)
    db.touch_session(session_id)

    reply_out = MessageOut(**reply, citations=citations)
    return {"session_id": session_id, "reply": reply_out, "citations": citations}
