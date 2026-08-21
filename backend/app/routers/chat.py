import re
from fastapi import APIRouter, HTTPException

from .. import database as db
from ..config import settings
from ..groq_client import get_chat_completion
from ..models import ChatRequest, ChatResponse, MessageOut, SessionDetailOut, SessionOut
from ..rag.retrieve import get_index, is_small_talk, retrieve_context
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

    # --- Small-talk / Formal conversation check ---
    if is_small_talk(req.message):
        context_block, citations = "", []
    else:
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
    if not reply_text or not reply_text.strip():
        reply_text = "I apologize, but I was unable to generate a detailed response for your question. Please try rephrasing your prompt."

    # For non-small-talk queries, ensure any section numbers mentioned in reply_text are included in citations
    if not is_small_talk(req.message):
        index = get_index()
        mentioned_sec_nums = [
            int(n) for n in re.findall(r"\bSection\s*(\d{1,3})\b", reply_text, re.IGNORECASE)
        ]

        existing_sec_nums = {c["section"] for c in citations}
        added_citations = []

        for sec_num in mentioned_sec_nums:
            if sec_num not in existing_sec_nums and 1 <= sec_num <= 354:
                sec = index.get_by_number(sec_num)
                if sec:
                    existing_sec_nums.add(sec_num)
                    added_citations.append(
                        {"section": sec.number, "title": sec.title, "chapter": sec.chapter, "text": sec.text}
                    )

        # Place sections directly cited by the LLM response first
        citations = added_citations + citations

        # Fallback: If citations is still empty for a relevant legal question, perform top_k search
        if not citations:
            _, citations = retrieve_context(req.message, top_k=3)

    reply = db.add_message(session_id, "assistant", reply_text, citations=citations)
    db.touch_session(session_id)

    reply_out = MessageOut(**reply)
    return {"session_id": session_id, "reply": reply_out, "citations": citations}
