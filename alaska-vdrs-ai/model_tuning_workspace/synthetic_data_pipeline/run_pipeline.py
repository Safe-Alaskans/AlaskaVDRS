import os

from dotenv import load_dotenv

from model_tuning_workspace.models.claude import Claude35SonnetExec
from model_tuning_workspace.synthetic_data_pipeline.features.location import LocationFeature
from model_tuning_workspace.synthetic_data_pipeline.features.mortality_cause import MortalityCauseFeature
from model_tuning_workspace.synthetic_data_pipeline.features.motive import MotiveFeature
from model_tuning_workspace.synthetic_data_pipeline.features.participants import ParticipantsFeature
from model_tuning_workspace.synthetic_data_pipeline.features.timeline import TimelineFeature
from model_tuning_workspace.synthetic_data_pipeline.features.unrelated_info import UnrelatedInfoFeature
from model_tuning_workspace.synthetic_data_pipeline.features.witnesses import WitnessesFeature
from model_tuning_workspace.synthetic_data_pipeline.framework.pipeline import Pipeline
from model_tuning_workspace.synthetic_data_pipeline.framework.useful_steps import FeatureSelectionStep, StoreAllSteps
from model_tuning_workspace.synthetic_data_pipeline.steps.gen_autopsy_step import GenerateAutopsyStep
from model_tuning_workspace.synthetic_data_pipeline.steps.gen_me_report_step import GenerateMEReportStep
from model_tuning_workspace.synthetic_data_pipeline.steps.gen_toxicology_report import GenerateToxicologyReportStep
from model_tuning_workspace.synthetic_data_pipeline.steps.teacher_model_gen import TeacherModelGenStep
from model_tuning_workspace.synthetic_data_pipeline.storage.mongo_storage import MongoDBHandler

if __name__ == "__main__":
    NUM_OF_ITERATIONS = 10

    load_dotenv()
    db_handler = MongoDBHandler(
        connection_string=os.getenv('MONGO_CONNECTION_STRING'),
        database_name=os.getenv('MONGO_DB_NAME')
    )
    teacher_model = Claude35SonnetExec()

    mortality_cause_ft = MortalityCauseFeature()
    feature_select_step = FeatureSelectionStep(
        features=[
            mortality_cause_ft,
            ParticipantsFeature(mortality_cause_ft=mortality_cause_ft),
            WitnessesFeature(),
            LocationFeature(),
            MotiveFeature(),
            TimelineFeature(),
            UnrelatedInfoFeature(),
        ]
    )

    pipeline = Pipeline(
        steps=[
            feature_select_step,
            GenerateMEReportStep(synth_data_gen_model=teacher_model),
            GenerateToxicologyReportStep(syth_data_gen_model=teacher_model),
            GenerateAutopsyStep(synth_data_gen_model=teacher_model),
            TeacherModelGenStep(teacher_model=teacher_model),
            StoreAllSteps(db_handler=db_handler),
        ],
    )

    try:
        for i in range(NUM_OF_ITERATIONS):
            pipeline.execute(iteration_number=i)
        print(f"\n\nUse runId: {pipeline.run_id} in review_pipeline_run_script.py to review the pipeline run and make changes")
    except Exception as e:
        print(f"Error creating pipeline: {str(e)}")
    finally:
        db_handler.close_connection()
