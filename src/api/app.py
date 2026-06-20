"""FastAPI application for FitAgent."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from agent.service import FitAgentService, build_service
from api.schemas import ChatPayload, ChatResponse, ConversationResponse, ProfilePayload, ProfileResponse, ProgressResponse
from logging_config import configure_logging


logger = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).resolve().parents[2] / "static"


def create_app(service: FitAgentService | None = None) -> FastAPI:
    configure_logging()
    app = FastAPI(
        title="FitAgent API",
        description="Safety-aware health and fitness coaching API",
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    agent_service = service or build_service()

    def get_service() -> FitAgentService:
        return agent_service

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
        logger.exception(
            "unhandled_api_error",
            extra={"category": "api", "error_type": exc.__class__.__name__},
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "FitAgent hit an unexpected error. Please try again."},
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/profiles", response_model=ProfileResponse)
    def submit_profile(payload: ProfilePayload, svc: FitAgentService = Depends(get_service)) -> dict:
        try:
            return svc.submit_profile(payload.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/profiles/{session_id}", response_model=ProfileResponse)
    def get_profile(session_id: str, svc: FitAgentService = Depends(get_service)) -> dict:
        profile = svc.store.get_profile(session_id)
        from tools.profile import missing_profile_fields

        return {"session_id": session_id, "profile": profile, "missing_fields": missing_profile_fields(profile)}

    @app.post("/api/chat", response_model=ChatResponse)
    def chat(payload: ChatPayload, svc: FitAgentService = Depends(get_service)) -> dict:
        try:
            return svc.answer_question(payload.message, payload.session_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/conversations/{session_id}", response_model=ConversationResponse)
    def conversation(session_id: str, svc: FitAgentService = Depends(get_service)) -> dict:
        return svc.conversation_history(session_id)

    @app.get("/api/progress/{session_id}", response_model=ProgressResponse)
    def progress(session_id: str, svc: FitAgentService = Depends(get_service)) -> dict:
        return svc.progress(session_id)

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

        @app.get("/")
        def index() -> FileResponse:
            return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
