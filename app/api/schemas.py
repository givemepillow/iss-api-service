from __future__ import annotations

from pydantic import BaseModel


class ResponseSchema(BaseModel):
    detail: str