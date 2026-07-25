from pydantic import BaseModel


class ExtractRequest(BaseModel):
    prompt: str
