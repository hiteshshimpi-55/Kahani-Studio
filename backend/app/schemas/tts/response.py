from pydantic import BaseModel


class SynthesizeSpeechResponse(BaseModel):
    path: str
    relative_path: str
    voice_id: str
    model_id: str
    output_format: str
    character_count: int
    bytes: int
    series_id: str
    seq_id: str


class EnqueueSynthesizeResponse(BaseModel):
    job_id: str | None
    queued: bool
    series_id: str
    seq_id: str
