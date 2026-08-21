# Sromo — Bangladesh Labour Law Assistant (Phase 1, RAG-grounded)

A conversational chatbot built on Groq-hosted LLMs, with **retrieval-augmented
generation over the actual Bangladesh Labour Act 2006**, persistent chat
history, and a modern animated React UI. This is Phase 1 of the staged
architecture from the project's architecture report: a working RAG pipeline
(parse → chunk → embed → vector store → retrieve → generate → chat), scoped
to the Act text currently ingested. Phase 2 adds amendments, translation,
and bilingual replies on top of this same pipeline.

```
labour-law-chatbot/
├── backend/
│   ├── app/
│   │   ├── rag/            ← the RAG pipeline (new)
│   │   │   ├── corpus.py     parse & chunk the Act into sections
│   │   │   ├── index.py      TF-IDF+SVD embeddings + FAISS vector store
│   │   │   └── retrieve.py   hybrid search + explicit "Section N" lookup
│   │   ├── routers/chat.py ← retrieves context, injects it, calls Groq
│   │   └── system_prompt.py← instructs the model to cite retrieved sections
│   └── data/
│       ├── source/labour_act_2006.txt   the ingested corpus (Ch. I-VII)
│       └── rag_index/                   pre-built vector index (auto-rebuilds if missing)
└── frontend/    React (Vite) + framer-motion, shows §-citation chips
```

## 1. Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Your Groq API key is already in `backend/.env`. If you ever need to reset
it, copy `.env.example` to `.env` and fill in `GROQ_API_KEY`.

> **Security note:** the API key you originally pasted into chat is recorded
> in that conversation's history. It's stored safely here (`.env` is
> git-ignored, never hardcoded in source), but it's worth rotating it in
> your Groq console once you've confirmed everything works.

Run the API:

```bash
uvicorn app.main:app --reload --port 8000
```

On startup you should see `[Sromo] RAG index ready: 80 sections loaded.`
Check it's alive: `curl http://localhost:8000/api/health`

## 2. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (default `http://localhost:5173`).

## 3. How the RAG pipeline works

1. **Corpus** (`data/source/labour_act_2006.txt`) — the Act's text for
   Chapters I-VII (Sections 1-80: preliminary provisions, conditions of
   service and employment, employment of adolescents, maternity benefit,
   health & hygiene, and safety), fetched from a public legal-text mirror.
   **This is a partial corpus** — Chapters VIII-XXI (sections 81-354:
   welfare, working hours & leave, wages, workers' compensation, trade
   unions, industrial disputes, etc.) are not yet ingested. Sromo is
   instructed to say so plainly rather than guess when a question falls
   outside what's ingested.
2. **Parse & chunk** (`app/rag/corpus.py`) — regex-splits the raw text into
   one chunk per numbered section, tagged with section number, title, and
   chapter.
3. **Embed & index** (`app/rag/index.py`) — TF-IDF vectors reduced to a
   dense space via truncated SVD, indexed in FAISS. This is a deliberately
   lightweight, fully offline choice (see the architecture report's
   "small, static, single-source" reasoning) — no multi-gigabyte model
   download needed. Retrieval blends this dense score with a raw TF-IDF
   cosine score and a title-keyword boost (a lightweight hybrid
   dense+sparse re-ranker) to catch cases where the query's wording
   differs from the statute's (e.g. "maternity leave" → Section 46
   "maternity benefit").
4. **Retrieve** (`app/rag/retrieve.py`) — an explicit "Section 27" mention
   in the query is looked up directly (guaranteed exact match); otherwise
   the top-4 sections by hybrid score are returned.
5. **Generate** (`app/routers/chat.py` + `app/system_prompt.py`) — retrieved
   sections are injected as a system message before the user's question;
   the model is instructed to cite the section number for every claim and
   to say plainly when the retrieved sections don't answer the question.
6. **Citations in the UI** — every assistant reply that used retrieval shows
   §-chips under the message (`MessageBubble.jsx`), sourced straight from
   the API response.

To rebuild the index after editing the corpus:

```bash
cd backend
python3 -m app.rag.index
```

### Extending the corpus (next step)

To cover the rest of the Act, append the remaining sections (81-354) to
`data/source/labour_act_2006.txt` in the same format the parser expects
(`NN. Title: text...`), delete `data/rag_index/`, and restart the server —
it rebuilds automatically. `app/rag/corpus.py`'s regex-based parser needs
no changes for this.

## 4. What's included (recap from Phase 1 chat layer)

- **Small talk handling** — greetings, "what can you do", "why you",
  thanks/bye are all handled naturally before pivoting to labour-law
  questions (`system_prompt.py`).
- **Persistent chat history** — SQLite-backed (`data/sromo.db`), survives
  restarts, browsable from the sidebar; frontend also remembers your
  last-open chat via `localStorage`.
- **Modern animated UI** — framer-motion message entrances, a bouncing
  typing indicator, an animated send button, citation chips, a collapsible
  sidebar on mobile.

## 5. Next step (Phase 2, not built yet)

Per the architecture report: ingest the 2013/2018 amendments and Rules 2015
(mostly Bangla, needs translation), switch to a multilingual embedding
model, add bilingual replies, amendment-aware retrieval (surfacing an
amendment when it supersedes a retrieved base-Act section), and a
document-upload path. The RAG module is structured so each of these is an
addition to `app/rag/`, not a rewrite.
