from typing import Any

from pydantic import BaseModel


class VectorSearchHitResponse(BaseModel):
    fields: dict[str, Any]


class VectorSearchResponse(BaseModel):
    endpoint_name: str
    index_name: str
    hits: list[VectorSearchHitResponse]
    count: int
