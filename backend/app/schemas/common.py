from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel):
    items: list
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)


class Message(BaseModel):
    message: str


class IDResponse(BaseModel):
    id: UUID
