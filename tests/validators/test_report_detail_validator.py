import unittest

from model_tuning_workspace.evaluations.validators.report_detail_validator import ReportDetailValidator
from model_tuning_workspace.models.claude import Claude35SonnetExec


class TestReportDetailValidator(unittest.TestCase):
    def setUp(self):
        self.model_exec = Claude35SonnetExec()
        self.eval_case_id = "test_case_001"
        self.validator = ReportDetailValidator(model_exec=self.model_exec)

    def test_validate_no_excessive_detail(self):
        """Test case where narrative contains no excessive detail"""
        narrative = """The decedent was found deceased from a self-inflicted gunshot wound to the head, with an entrance wound in the forehead and exit wound at the back of the head."""

        result = self.validator.validate(
            output=narrative,
            eval_case_id=self.eval_case_id
        )

        self.assertTrue(result.passed)

    def test_validate_with_excessive_detail(self):
        """Test case where narrative contains excessive detail"""
        narrative = ("The decedent, a 30-year-old female, sustained a self-inflicted gunshot wound with the entrance "
                     "wound located on the anterior forehead/bridge of nose showing extensive soot staining. "
                     "The bullet trajectory went front to back, causing extensive fracturing of the calvarial and "
                     "basilar skull with pulpefaction of brain tissue. The exit wound was found 1.5 inches from "
                     "the top of the head with protruding hemorrhagic brain tissue.")

        result = self.validator.validate(
            output=narrative,
            eval_case_id=self.eval_case_id
        )

        self.assertFalse(result.passed)