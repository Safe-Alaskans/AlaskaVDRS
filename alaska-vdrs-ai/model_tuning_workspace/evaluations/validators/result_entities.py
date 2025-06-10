from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    validator: str
    eval_case_id: str
    validator_description: str
    passed: bool
    details: str


class ValidationResults(BaseModel):
    results: List[ValidationResult]

    @property
    def passed(self) -> bool:
        return all(result.passed for result in self.results)


class CaseResult(BaseModel):
    case_id: str = Field(..., min_length=1)
    input_text: str = Field(..., min_length=1)
    output_text: Optional[str] = None
    passed: bool
    execution_time_seconds: Optional[float] = Field(None, ge=0)
    validator_results: ValidationResults

    class Config:
        from_attributes = True


class EvalRun(BaseModel):
    ai_model: str
    system_message: str = Field(..., min_length=1)
    case_results: List[CaseResult] = Field(..., )
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_time_seconds: Optional[float] = Field(None, ge=0)
    accuracy_percentage: Optional[float] = Field(None, ge=0, le=100)
