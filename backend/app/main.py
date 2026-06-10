"""FastAPI app: streaming /chat (SSE), part deep-links, health."""

from __future__ import annotations

import json
import logging
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from backend.app import config, retrieval
from backend.app.agent import chat_stream

logger = logging.getLogger(__name__)

app = FastAPI(title="PartSelect Chat Agent")


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = uuid.uuid4().hex[:12]
    config.request_id_var.set(rid)
    try:
        response = await call_next(request)
    except Exception:  # noqa: BLE001 - single safety net; details stay in logs
        logger.exception("unhandled error")
        return JSONResponse({"error": "internal error", "request_id": rid}, status_code=500)
    response.headers["X-Request-ID"] = rid
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
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
    return {
        "status": "ok",
        "parts_count": parts_count,
        "llm_model": "MOCK" if config.settings.mock_llm else config.settings.llm_model,
    }
