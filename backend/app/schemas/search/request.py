from pydantic import BaseModel, Field


class VectorSearchRequest(BaseModel):
    query_text: str = Field(..., min_length=1, max_length=4000)
    num_results: int = Field(default=5, ge=1, le=50)
    columns: list[str] | None = None
    query_type: str = Field(default="ANN", description="ANN | HYBRID | …")
    filters: dict | None = None
    endpoint_name: str | None = None
    index_name: str | None = None
