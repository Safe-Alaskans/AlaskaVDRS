import unittest

from model_tuning_workspace.evaluations.validators.length_validator import LengthValidator


class TestLengthValidator(unittest.TestCase):

    def setUp(self):
        self.eval_case_id = "test_case_001"
        self.max_words = 600
        self.validator = LengthValidator(max_words=self.max_words)

    def test_validate_output_within_limit(self):
        input_str = " ".join(["word"] * self.max_words)
        result = self.validator.validate(output=input_str, eval_case_id=self.eval_case_id)
        assert result.passed

    def test_validate_output_exceeds_limit(self):
        input_str = " ".join(["word"] * (self.max_words + 1))
        result = self.validator.validate(output=input_str, eval_case_id=self.eval_case_id)
        assert not result.passed

if __name__ == '__main__':
    unittest.main()
