from typing import Dict

from model_tuning_workspace.evaluations.validators.result_entities import ValidationResult
from model_tuning_workspace.evaluations.validators.validator_base import Validator
from model_tuning_workspace.models.model_executor import ModelExecutor
from model_tuning_workspace.utils.yaml_parsing import parse_yaml_response


class PIIValidator(Validator):
    def __init__(self, model_exec: ModelExecutor):
        self.model_exec = model_exec

    def validate(self, output: str, eval_case_id: str) -> ValidationResult:
        sys_msg = """
# Context
You will be provided with a narrative text that should not contain any personally identifiable information (PII).
Your task is to identify if any PII is present in the text.

PII includes:
- Names of individuals
- Dates of birth
- Addresses
- Organization names (businesses, hospitals, law enforcement agencies, etc.)

# Your output
Write a single YAML file with the following structure:
```yaml
results:
  has_pii: true/false  # true if ANY PII is found
  found_pii: []  # list of any PII items found
```

Example:
```yaml
results:
  has_pii: true
  found_pii:
    - John Smith
    - ...
```
        """.strip()

        user_msg = f"""
# Narrative to check
{output}
        """.strip()

        resp = self.model_exec.execute(sys_msg=sys_msg, user_input=user_msg)
        resp_dict = parse_yaml_response(resp)

        # Extract results
        results: Dict = resp_dict.get("results", {})

        if "has_pii" not in results:
            raise ValueError(
                f"Missing 'has_pii' in results. Full response: {resp}"
            )

        # Convert found PII to CSV string for details
        found_pii = results.get("found_pii", [])
        details = ""
        if found_pii:
            pii_entries = [
                f"{item}"
                for item in found_pii
            ]
            details = "text\n" + "\n".join(pii_entries)

        return ValidationResult(
            validator=self.__class__.__name__,
            eval_case_id=eval_case_id,
            validator_description="Checking for presence of PII (names, DOBs, addresses, organization names)",
            passed=not results["has_pii"],
            details=details
        )