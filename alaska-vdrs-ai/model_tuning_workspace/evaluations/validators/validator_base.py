from abc import ABC, abstractmethod

from model_tuning_workspace.evaluations.validators.result_entities import ValidationResult


class Validator(ABC):
    """Abstract base class for all validators"""

    @abstractmethod
    def validate(self, output: str, eval_case_id: str) -> ValidationResult:
        """Validate the output against a specific criterion"""
        pass
