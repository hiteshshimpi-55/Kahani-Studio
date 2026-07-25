from pydantic import BaseModel


class AuditScore(BaseModel):
    name: str
    score: float
    comment: str


class StructuralAuditResult(BaseModel):
    overall_score: float

    hook_score: AuditScore
    pacing_score: AuditScore
    dialogue_score: AuditScore
    cliffhanger_score: AuditScore