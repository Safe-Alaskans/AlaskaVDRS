from time import time
from typing import List

from model_tuning_workspace.evaluations.cases import base_cases
from model_tuning_workspace.evaluations.cases.base_cases import all_base_cases
from model_tuning_workspace.evaluations.db.eval_tracker import EvalTracker
from model_tuning_workspace.evaluations.eval_case import EvalCase
from model_tuning_workspace.evaluations.validators.result_entities import EvalRun, CaseResult
from model_tuning_workspace.models.claude import Claude35SonnetExec
from model_tuning_workspace.models.model_executor import ModelExecutor
from model_tuning_workspace.models.runpod_vllm import NvdrsV0Dot1
from model_tuning_workspace.prompting.system_msg import sys_msg


def run_eval_cases(
        eval_cases: List[EvalCase], model_exec: ModelExecutor, sys_msg: str
) -> EvalRun:
    start_time = time()
    case_results: List[CaseResult] = []
    passed_cases = 0

    for case in eval_cases:
        result = run_eval(case, model_exec, sys_msg)
        if result.passed:
            passed_cases += 1
        case_results.append(result)

    end_time = time()
    total_time = end_time - start_time

    total_cases = len(eval_cases)
    accuracy = (passed_cases / total_cases) * 100 if total_cases > 0 else 0

    return EvalRun(
        ai_model=model_exec.ai_model_name,
        system_message=sys_msg,
        case_results=case_results,
        started_at=start_time,
        completed_at=end_time,
        total_time_seconds=total_time,
        accuracy_percentage=accuracy
    )


def run_eval(
        case: EvalCase, model_exec: ModelExecutor, sys_msg: str
) -> CaseResult:
    case_start_time = time()
    case.input_text = case.input_text.strip()

    output = model_exec.execute(sys_msg, case.input_text)

    case_end_time = time()
    case_execution_time = case_end_time - case_start_time

    print(f"Case {case.id} completed in {case_execution_time:.2f} seconds. Now validating...")
    validation_results = case.evaluate(output)
    print(f"Validation results for case {case.id}: {validation_results.passed}")
    result = CaseResult(
        case_id=case.id,
        input_text=case.input_text,
        output_text=output,
        passed=validation_results.passed,
        execution_time_seconds=case_execution_time,
        validator_results=validation_results,
    )
    return result


if __name__ == "__main__":
    tracker = EvalTracker()
    exec_to_eval = NvdrsV0Dot1()
    all_eval_cases = [
        *all_base_cases,
    ]

    eval_run_data = run_eval_cases(all_eval_cases, exec_to_eval, sys_msg)

    id_of_eval_run_in_db = tracker.create_eval_run(eval_run_data)

    print(f"Evaluation run completed and stored with ID: {id_of_eval_run_in_db}")
    print(f"Overall accuracy: {eval_run_data.accuracy_percentage:.2f}%")

    for case_result in eval_run_data.case_results:
        if not case_result.passed:
            print(f"\nFailures for case {case_result.case_id}:")
            for validator_result in case_result.validator_results.results:
                if not validator_result.passed:
                    print(f"\t❌ {validator_result.validator}: {validator_result.details}")
