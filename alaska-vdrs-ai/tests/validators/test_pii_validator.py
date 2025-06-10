import unittest
from model_tuning_workspace.evaluations.validators.result_entities import ValidationResult
from model_tuning_workspace.evaluations.validators.pii_validator import PIIValidator
from model_tuning_workspace.models.claude import Claude35SonnetExec
from tests.assets.load import load_test_narrative


class TestPIIValidator(unittest.TestCase):
    def setUp(self):
        self.model_exec = Claude35SonnetExec()
        self.eval_case_id = "test_case_001"
        self.validator = PIIValidator(model_exec=self.model_exec)

    def test_validate_no_pii(self):
        """Test case where narrative contains no PII"""
        narrative = """
        The officers arrived at the scene after receiving a call about gunshots. 
        Upon arrival, they found evidence of a violent incident including shell casings 
        and blood spatter. The victim had sustained multiple gunshot wounds.
        """

        result = self.validator.validate(
            output=narrative,
            eval_case_id=self.eval_case_id
        )

        self.assertIsInstance(result, ValidationResult)
        self.assertTrue(result.passed)

    def test_validate_with_pii(self):
        """Test case where narrative contains PII"""
        narrative = """
        Officer Jamie Wraith responded to a call at 89 Guilo Road. 
        The victim was transported to Memorial Hospital where Dr. Jane Doe 
        pronounced them deceased at 3:15 PM. The investigation was led by 
        the Springfield Police Department.
        """

        result = self.validator.validate(
            output=narrative,
            eval_case_id=self.eval_case_id
        )

        self.assertFalse(result.passed)


    def test_validate_minimal_narrative(self):
        """Test case with minimal narrative containing PII"""
        narrative = "John Doe was involved in the incident."

        result = self.validator.validate(
            output=narrative,
            eval_case_id=self.eval_case_id
        )

        self.assertFalse(result.passed)

    def test_validate_no_pii_longer_narrative(self):
        """Test case with longer narrative containing no PII"""
        narrative = load_test_narrative()

        result = self.validator.validate(
            output=narrative,
            eval_case_id=self.eval_case_id
        )

        self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()