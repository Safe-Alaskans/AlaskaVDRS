from model_tuning_workspace.evaluations.validators.result_entities import ValidationResult
from model_tuning_workspace.evaluations.validators.validator_base import Validator
from model_tuning_workspace.models.model_executor import ModelExecutor
from model_tuning_workspace.utils.yaml_parsing import parse_yaml_response


class ReportDetailValidator(Validator):
    def __init__(self, model_exec: ModelExecutor):
        self.model_exec = model_exec

    def validate(self, output: str, eval_case_id: str) -> ValidationResult:
        sys_msg = """
# Context
You will review a narrative that may contain references to toxicology or autopsy findings.
Any references are fine, as long as they include a very concise and minor mention.
1 sentence is enough, no more than 2.

# Your output
Write a single YAML file with the following structure:
```yaml
has_excessive_detail: true/false
```
        """.strip()

        user_msg = f"""
# Narrative to check
{output}
        """.strip()

        resp = self.model_exec.execute(sys_msg=sys_msg, user_input=user_msg)
        resp_dict = parse_yaml_response(resp)

        is_excessive = resp_dict.get("has_excessive_detail")

        return ValidationResult(
            validator=self.__class__.__name__,
            eval_case_id=eval_case_id,
            validator_description="Checking for excessive detail in toxicology/autopsy mentions",
            passed=not is_excessive,
            details=f"Excessive detail: {is_excessive}"
        )