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

_SMALL_TALK_PATTERNS = [
    r"^(hi|hello|hey|hola|greetings|good\s*(morning|afternoon|evening|day)|howdy)(\s+(there|assistant|bot|friend|sromo|shromik))?$",
    r"^(what\s+can\s+you\s+do.*|what\s+do\s+you\s+do.*|who\s+are\s+you.*|what\s+is\s+your\s+name.*|who\s+created\s+you.*|what\s+are\s+your\s+features.*)$",
    r"^(how\s+are\s+you.*|how\s+is\s+it\s+going.*|whats\s+up.*|whatup|sup)$",
    r"^(thanks.*|thank\s+you.*|thanks\s+a\s+lot.*|thank\s+you\s+so\s+much.*|ok|okay|bye|goodbye|see\s+you.*)$",
    r"^(help|can\s+you\s+help\s+me|tell\s+me\s+about\s+yourself|introduce\s+yourself)$",
]

_index: RagIndex | None = None


def get_index() -> RagIndex:
    global _index
    if _index is None:
        _index = RagIndex.load_or_build()
    return _index


def is_small_talk(query: str) -> bool:
    """Returns True if the query is a greeting, small talk, or conversational check."""
    q = query.strip()
    cleaned = re.sub(r"[^\w\s]", "", q.lower()).strip()
    if not cleaned:
        return True
    for pattern in _SMALL_TALK_PATTERNS:
        if re.match(pattern, cleaned, re.IGNORECASE):
            return True
    return False


def retrieve_context(query: str, top_k: int = 4) -> tuple[str, list[dict]]:
    """
    Returns (context_block_text, citations) where citations is a list of
    {"section": int, "title": str, "chapter": str, "text": str}.
    """
    cleaned_query = query.strip()
    if is_small_talk(cleaned_query):
        return "", []

    index = get_index()
    sections: list = []

    # Check for explicit section references in the user query
    section_refs = [int(m.group(1)) for m in _SECTION_REF_RE.finditer(cleaned_query)]

    if section_refs:
        has_valid = False
        for sec_num in section_refs:
            if sec_num > 354 or sec_num < 1:
                continue
            sec = index.get_by_number(sec_num)
            if sec and sec not in sections:
                sections.append(sec)
                has_valid = True

        if not has_valid and any(s > 354 for s in section_refs):
            return "", []

    # Perform hybrid search for top_k relevant sections (no score truncation)
    if len(sections) < top_k:
        search_results = index.search(cleaned_query, top_k=top_k)
        for sec, _score in search_results:
            if sec not in sections:
                sections.append(sec)
            if len(sections) >= top_k:
                break

    if not sections:
        return "", []

    blocks = [sec.as_context_block() for sec in sections]
    context = "\n\n".join(blocks)
    citations = [
        {"section": s.number, "title": s.title, "chapter": s.chapter, "text": s.text}
        for s in sections
    ]
    return context, citations

