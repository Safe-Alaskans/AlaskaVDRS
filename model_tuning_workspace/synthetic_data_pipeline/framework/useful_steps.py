from typing import List

from model_tuning_workspace.synthetic_data_pipeline.framework.feature import TopLevelFeature
from model_tuning_workspace.synthetic_data_pipeline.framework.pipeline import PipelineStep, PipelineContext
from model_tuning_workspace.synthetic_data_pipeline.storage.mongo_storage import MongoDBHandler


class FeatureSelectionStep(PipelineStep):
    def __init__(self, features: List[TopLevelFeature]):
        super().__init__(step_name="feature_selection")
        self.features: List[TopLevelFeature] = features

    def execute(self, context: PipelineContext) -> tuple[str, bool]:
        for feature in self.features:
            try:
                feature.init_sub_feature_values()
                context.add_feature(feature)
            except Exception as e:
                raise ValueError(f"Error adding feature {feature.name}: {str(e)}")
        return "", True

class ValidationStep(PipelineStep):
    def __init__(self, output_to_validate: str = "teacher"):
        super().__init__(step_name="validation")
        self.output_to_validate = output_to_validate

    def execute(self, context: PipelineContext) -> tuple[str, bool]:
        teacher_output = context.get_output(self.output_to_validate)
        for feature in context.features.values():
            if not feature.validate_sub_features(teacher_output):
                return f"Validation failed for feature {feature.name}", False

        return "", True


class StoreAllSteps(PipelineStep):
    def __init__(self, db_handler: MongoDBHandler):
        super().__init__(step_name="store_all_steps")
        self.db_handler = db_handler

    def execute(self, context: PipelineContext) -> tuple[str, bool]:
        all_features = context.features.values()
        all_ft_dicts = [ft.serialize() for ft in all_features]
        new_doc = {
            "pipeline_run_id": context.pipeline_run_uuid,
            "iteration_id": context.iteration_id,
            "features": all_ft_dicts,
            "outputs": context.intermediate_outputs,
        }
        self.db_handler.insert_document(collection_name="synthetic_data", data=new_doc)
        return "", True


class ReviewTeacherOutputStep(PipelineStep):
    def __init__(self, db_handler: MongoDBHandler):
        super().__init__(step_name="review_teacher_output")
        self.db_handler = db_handler

    def execute(self, context: PipelineContext) -> tuple[str, bool]:
        teacher_output = context.get_output("teacher_model_gen")

        # Write original output to file
        with open("teacher_output.txt", "w") as f:
            f.write(teacher_output)

        print("\nTeacher output has been written to teacher_output.txt")
        print("Please review and edit the file if needed.")

        while True:
            user_input = input("Type 'y' when done reviewing: ").lower()
            if user_input == 'y':
                break

        # Read the possibly edited file
        with open("teacher_output.txt", "r") as f:
            edited_output = f.read()

        # Check if the output was modified
        if edited_output != teacher_output:
            # Update MongoDB document with edited output
            query = {
                "pipeline_run_id": context.pipeline_run_uuid,
                "iteration_id": context.iteration_id
            }
            update = {
                "$set": {"edited_teacher_output": edited_output}
            }
            self.db_handler.update_document_by_query(
                collection_name="synthetic_data",
                query=query,
                update=update
            )
            print("Updated MongoDB with edited teacher output")
        else:
            print("No changes detected in teacher output")

        return "", True