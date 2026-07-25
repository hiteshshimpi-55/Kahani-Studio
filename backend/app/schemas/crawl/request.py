from pydantic import BaseModel

from app.schemas.extraction.response import ExtractionResponse


class CrawlRequest(BaseModel):
    extraction_id: int | None = None
    extraction: ExtractionResponse | None = None
