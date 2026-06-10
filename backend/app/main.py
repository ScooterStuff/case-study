"""FastAPI app: streaming /chat (SSE), part deep-links, health."""
from __future__ import annotations

import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from backend.app import retrieval
from backend.app.agent import chat_stream
from backend.app.config import settings

app = FastAPI(title="PartSelect Chat Agent")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"], allow_headers=["*"],
)


class ChatIn(BaseModel):
    session_id: str
    message: str


@app.post("/chat")
async def chat(body: ChatIn) -> EventSourceResponse:
    async def gen():
        async for event in chat_stream(body.session_id, body.message):
            yield {"event": event["event"], "data": json.dumps(event["data"])}
    return EventSourceResponse(gen())


@app.get("/parts/{ps_number}")
def part(ps_number: str) -> dict:
    found = retrieval.get_part(ps_number)
    if found is None:
        raise HTTPException(404, "part not found")
    return found


@app.get("/health")
def health() -> dict:
    parts_count = retrieval.get_conn().execute("SELECT count(*) FROM parts").fetchone()[0]
    return {"status": "ok", "parts_count": parts_count,
            "llm_model": "MOCK" if settings.mock_llm else settings.llm_model}
