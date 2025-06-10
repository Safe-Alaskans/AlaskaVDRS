from model_tuning_workspace.evaluations.validators.result_entities import ValidationResult
from model_tuning_workspace.evaluations.validators.validator_base import Validator

class LengthValidator(Validator):

    def __init__(
            self,
            max_words: int = 600,
    ):
        self.max_length = max_words

    def validate(self, output: str, eval_case_id: str) -> ValidationResult:
        words = output.split()
        word_count = len(words)

        if word_count > self.max_length:
            return ValidationResult(
                validator=self.__class__.__name__,
                eval_case_id=eval_case_id,
                validator_description=f"Checking output word count is within limits. Max words: {self.max_length}",
                passed=False,
                details=f"Output exceeded max word count of {self.max_length}. Found {word_count} words."
            )

        return ValidationResult(
            passed=True,
            validator=self.__class__.__name__,
            eval_case_id=eval_case_id,
            validator_description=f"Checking output word count is within limits. Max words: {self.max_length}",
            details=f"Output word count is within limits. Found {word_count} words."
        )