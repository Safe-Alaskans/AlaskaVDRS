import unittest
from model_tuning_workspace.evaluations.validators.result_entities import ValidationResult
from model_tuning_workspace.evaluations.validators.key_info_validator import KeyInfoValidator
from model_tuning_workspace.models.claude import Claude35SonnetExec
from tests.assets.load import load_test_narrative


class TestKeyInfoValidator(unittest.TestCase):
    def setUp(self):
        self.model_exec = Claude35SonnetExec()
        self.eval_case_id = "test_case_001"

    def test_validate_single_info(self):
        test_narrative = load_test_narrative()
        validator = KeyInfoValidator(
            info_to_check=["A shotgun was found on the scene"],
            model_exec=self.model_exec
        )

        result = validator.validate(
            output=test_narrative,
            eval_case_id=self.eval_case_id
        )

        self.assertIsInstance(result, ValidationResult)
        self.assertTrue(result.passed)

    def test_validate_multiple_info(self):
        test_narrative = load_test_narrative()
        validator = KeyInfoValidator(
            info_to_check=[
                "LE found the victim",
                "A shotgun was found on the scene",
                "The victim was shot in the head",
                "The victim was found on a sofa",
                "Toxicology reports showed the victim had 0.250 BAC"
            ],
            model_exec=self.model_exec
        )

        result = validator.validate(
            output=test_narrative,
            eval_case_id=self.eval_case_id
        )

        self.assertIsInstance(result, ValidationResult)
        self.assertTrue(result.passed)

if __name__ == "__main__":
    unittest.main()