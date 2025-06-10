from typing import List

from model_tuning_workspace.evaluations.validators.result_entities import ValidationResult
from model_tuning_workspace.evaluations.validators.validator_base import Validator
from model_tuning_workspace.models.model_executor import ModelExecutor
from model_tuning_workspace.utils.yaml_parsing import parse_yaml_response


class KeyInfoValidator(Validator):

    def __init__(
            self,
            info_to_check: List[str],
            model_exec: ModelExecutor,
    ):
        self.info_to_check = info_to_check
        self.model_exec = model_exec

    def _create_user_message(self, output: str) -> str:
        numbered_info = "\n".join(
            f"{i+1}. {info}"
            for i, info in enumerate(self.info_to_check)
        )

        return f"""
# Narrative
{output}

# Key information to check for
{numbered_info}
        """.strip()

    def validate(self, output: str, eval_case_id: str) -> ValidationResult:
        sys_msg = """
# Context
The user will provide a narrative of a violent incident that occurred.
You will be asked to confirm that key information items are present in the narrative.
Each key information item will have a numeric ID.

# Your output
You need to write a single YAML file with the following structure:
```yaml
results:
  1: true/false  # true if info #1 is present, false if not
  2: true/false  # true if info #2 is present, false if not
  # etc. for each numbered info item
```
No other text should be present in the file.
        """.strip()

        user_msg = self._create_user_message(output)
        resp = self.model_exec.execute(sys_msg=sys_msg, user_input=user_msg)
        resp_dict = parse_yaml_response(resp)

        # Extract results
        results = resp_dict.get("results", {})

        # Verify all info items were checked
        expected_keys = set(str(i+1) for i in range(len(self.info_to_check)))
        actual_keys = set(str(k) for k in results.keys())

        if expected_keys != actual_keys:
            raise ValueError(
                f"Missing results for some key info items. "
                f"Expected keys {expected_keys}, got {actual_keys}. "
                f"Full response: {resp}"
            )

        # Create detailed results string matching original key info descriptions
        details = "\n".join(
            f"'{self.info_to_check[int(k)-1]}': {v}"
            for k, v in sorted(results.items(), key=lambda x: int(x[0]))
        )

        # Consider validation passed only if all results are True
        passed = all(results.values())

        return ValidationResult(
            validator=self.__class__.__name__,
            eval_case_id=eval_case_id,
            validator_description=f"Checking for {len(self.info_to_check)} key information items",
            passed=passed,
            details=details
        )