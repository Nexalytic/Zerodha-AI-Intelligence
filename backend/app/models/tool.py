from typing import Any

from pydantic import BaseModel


class ToolResponse(BaseModel):
    tool: str
    status: str
    data: Any