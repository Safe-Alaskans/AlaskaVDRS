import unittest
from model_tuning_workspace.evaluations.validators.result_entities import ValidationResult
from model_tuning_workspace.evaluations.validators.date_mention_validator import DateMentionValidator
from tests.assets.load import load_test_narrative


class TestDateMentionValidator(unittest.TestCase):
    def setUp(self):
        self.eval_case_id = "test_case_001"
        self.validator = DateMentionValidator()

    def test_validate_no_dates(self):
        """Test case where narrative contains no date mentions"""
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

    def test_validate_with_explicit_dates(self):
        """Test case where narrative contains explicit dates"""
        narrative = """
        The officers responded to a call and arrived at the scene on March 15, 2024.
        The incident appeared to have occurred around 3 PM. Initial evidence suggested
        the event took place on a Friday afternoon.
        """

        result = self.validator.validate(
            output=narrative,
            eval_case_id=self.eval_case_id
        )

        self.assertFalse(result.passed)

    def test_validate_with_holidays(self):
        """Test case where narrative contains holiday references"""
        narrative = """
        The incident occurred during the Christmas holiday period.
        Neighbors reported hearing disturbances since Thanksgiving.
        """

        result = self.validator.validate(
            output=narrative,
            eval_case_id=self.eval_case_id
        )

        self.assertFalse(result.passed)

    def test_validate_with_seasons(self):
        """Test case where narrative contains seasonal references"""
        narrative = """
        The investigation began in the summer. Evidence suggested
        the incidents had been occurring since spring.
        """

        result = self.validator.validate(
            output=narrative,
            eval_case_id=self.eval_case_id
        )

        self.assertFalse(result.passed)

    def test_validate_with_relative_dates(self):
        """Test case where narrative contains relative date references"""
        narrative = """
        The witness reported hearing disturbances yesterday and last weekend.
        The neighbor mentioned seeing suspicious activity next Friday.
        """

        result = self.validator.validate(
            output=narrative,
            eval_case_id=self.eval_case_id
        )

        self.assertFalse(result.passed)

    def test_validate_with_test_narrative(self):
        """Test case with standard test narrative"""
        narrative = load_test_narrative()

        result = self.validator.validate(
            output=narrative,
            eval_case_id=self.eval_case_id
        )

        self.assertTrue(result.passed)

    def test_validate_with_month_mentions(self):
        """Test case where narrative contains month references"""
        narrative = """
        The investigation started in January. Follow-up interviews
        were conducted through Feb and March.
        """

        result = self.validator.validate(
            output=narrative,
            eval_case_id=self.eval_case_id
        )

        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()