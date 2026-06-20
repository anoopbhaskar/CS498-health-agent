"""Pydantic schemas for the public REST API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ProfilePayload(BaseModel):
    session_id: str | None = None
    age: int | None = Field(default=None, ge=0, le=120)
    sex: str | None = None
    height_cm: float | None = Field(default=None, gt=0)
    weight_kg: float | None = Field(default=None, gt=0)
    activity_level: str | None = None
    health_conditions: list[str] = Field(default_factory=list)
    dietary_restrictions: list[str] = Field(default_factory=list)
    fitness_goals: list[str] = Field(default_factory=list)
    fitness_level: str | None = None
    current_steps: int | None = Field(default=None, ge=0)


class ProfileResponse(BaseModel):
    session_id: str
    profile: dict[str, Any]
    missing_fields: list[str]


class ChatPayload(BaseModel):
    session_id: str | None = None
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    session_id: str
    response: str
    category: str
    safety_flags: list[str] = Field(default_factory=list)
    used_tools: list[str] = Field(default_factory=list)


class MessageResponse(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    category: str | None = None
    created_at: datetime


class ConversationResponse(BaseModel):
    session_id: str
    messages: list[MessageResponse]


class ProgressResponse(BaseModel):
    session_id: str
    snapshots: list[dict[str, Any]]
    events: list[dict[str, Any]]
    summary: dict[str, Any]
