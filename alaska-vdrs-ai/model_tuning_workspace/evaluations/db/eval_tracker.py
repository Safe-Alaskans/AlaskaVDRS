from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from model_tuning_workspace.evaluations.db import Base
from model_tuning_workspace.evaluations.db.models import EvalRunModel, CaseResultModel, ValidatorResultModel
from model_tuning_workspace.evaluations.validators.result_entities import EvalRun


class EvalTracker:
    def __init__(self, db_path: str = "sqlite:///db/eval_runs.db"):
        self.engine = create_engine(db_path)
        Base.metadata.create_all(self.engine)

    def create_eval_run(self, eval_run: EvalRun) -> int:
        """
        Create a new eval run with associated case results and validator results.

        Returns:
            The ID of the created eval run
        """
        try:
            with Session(self.engine) as session:
                eval_run_model = EvalRunModel(
                    ai_model=eval_run.ai_model,
                    system_message=eval_run.system_message,
                    started_at=eval_run.started_at,
                    completed_at=eval_run.completed_at,
                    total_time_seconds=eval_run.total_time_seconds,
                    accuracy_percentage=eval_run.accuracy_percentage
                )

                session.add(eval_run_model)
                session.flush()  # Flush to get the ID

                # Store the ID before adding case results
                eval_run_id = eval_run_model.id

                for case_data in eval_run.case_results:
                    case_result_model = CaseResultModel(
                        eval_run_id=eval_run_id,
                        case_id=case_data.case_id,
                        user_msg=case_data.input_text,
                        llm_output=case_data.output_text,
                        passed=case_data.passed,
                        execution_time_seconds=case_data.execution_time_seconds,
                    )

                    session.add(case_result_model)
                    session.flush()  # Flush to get the ID

                    for validator_data in case_data.validator_results.results:
                        validator_result_model = ValidatorResultModel(
                            case_result_id=case_result_model.id,
                            validator_type=validator_data.validator,
                            validator_description=validator_data.validator_description,
                            passed=validator_data.passed,
                            details=validator_data.details
                        )

                        session.add(validator_result_model)

                session.commit()

                return eval_run_id

        except SQLAlchemyError as e:
            session.rollback()
            raise SQLAlchemyError(f"Failed to create eval run: {str(e)}")
