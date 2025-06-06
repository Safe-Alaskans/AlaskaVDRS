import hashlib
from typing import Optional, List

from pydantic import BaseModel, Field

from model_tuning_workspace.evaluations.validators.result_entities import ValidationResults
from model_tuning_workspace.evaluations.validators.validator_base import Validator


class EvalCase(BaseModel):
    id: Optional[str] = Field(default=None, description="Hash-based identifier for the evaluation case")
    description: Optional[str]
    input_text: str
    validators: List[Validator]

    def model_post_init(self, __context) -> None:
        """Post initialization hook to ensure ID is set"""
        if self.id is None:
            sha_256_of_input_txt = hashlib.sha256(self.input_text.encode('utf-8'))
            # First 8 characters of the hash for a shorter, but still unique ID
            self.id = sha_256_of_input_txt.hexdigest()[:8]

    class Config:
        arbitrary_types_allowed = True

    def evaluate(self, model_output: str) -> ValidationResults:
        results = [validator.validate(output=model_output, eval_case_id=self.id) for validator in self.validators]
        return ValidationResults(results=results)
