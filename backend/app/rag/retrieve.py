"""
Retrieve + orchestrate (architecture report §4.8): given a user message,
returns the statutory sections to ground the LLM's answer in.

Two retrieval paths, matching the report's design:
1. An explicit "Section 27" (or "section-27", "sec. 27") reference in the
   query is looked up directly — this guarantees exact citation lookups
   are never missed by approximate search alone.
2. Otherwise, hybrid dense+sparse search (see index.py) finds the top-k
   most relevant sections. Greetings and small talk skip retrieval to
   conserve token budget and avoid API rate limits.
"""
from __future__ import annotations

import re

from .index import RagIndex

_SECTION_REF_RE = re.compile(r"\bsec(?:tion)?\.?\s*(\d{1,3})\b", re.IGNORECASE)

_SMALL_TALK_RE = re.compile(
    r"^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening|day)|howdy|what\s+can\s+you\s+do|what\s+do\s+you\s+do|who\s+are\s+you|why\s+you|why\s+should\s+i\s+trust\s+you|thanks|thank\s+you|bye|goodbye)[\s!?.]*$",
    re.IGNORECASE,
)

_index: RagIndex | None = None


def get_index() -> RagIndex:
    global _index
    if _index is None:
        _index = RagIndex.load_or_build()
    return _index


def retrieve_context(query: str, top_k: int = 4, min_score: float = 0.20) -> tuple[str, list[dict]]:
    """
    Returns (context_block_text, citations) where citations is a list of
    {"section": int, "title": str, "chapter": str} for the frontend/logs.
    """
    cleaned_query = query.strip()
    if _SMALL_TALK_RE.match(cleaned_query):
        return "", []

    index = get_index()
    sections: list = []

    # Check for explicit section references
    section_refs = [int(m.group(1)) for m in _SECTION_REF_RE.finditer(cleaned_query)]
    
    # If the user explicitly asked for a section number > 354 (or < 1), do not fallback to vector search
    if section_refs:
        has_valid = False
        for sec_num in section_refs:
            if sec_num > 354 or sec_num < 1:
                continue
            sec = index.get_by_number(sec_num)
            if sec and sec not in sections:
                sections.append(sec)
                has_valid = True
        
        # If section numbers were mentioned but all were out of range (> 354), return empty context
        if not has_valid and any(s > 354 for s in section_refs):
            return "", []

    if len(sections) < top_k:
        for sec, score in index.search(cleaned_query, top_k=top_k):
            if score >= min_score and sec not in sections:
                sections.append(sec)
            if len(sections) >= top_k:
                break

    if not sections:
        return "", []

    blocks = [sec.as_context_block() for sec in sections]
    context = "\n\n".join(blocks)
    citations = [
        {"section": s.number, "title": s.title, "chapter": s.chapter, "text": s.text} for s in sections
    ]
    return context, citations

