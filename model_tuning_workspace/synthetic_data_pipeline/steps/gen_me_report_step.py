from model_tuning_workspace.models.model_executor import ModelExecutor
from model_tuning_workspace.synthetic_data_pipeline.features.location import LocationFeature
from model_tuning_workspace.synthetic_data_pipeline.features.mortality_cause import MortalityCauseFeature
from model_tuning_workspace.synthetic_data_pipeline.features.motive import MotiveFeature
from model_tuning_workspace.synthetic_data_pipeline.features.participants import ParticipantsFeature
from model_tuning_workspace.synthetic_data_pipeline.features.timeline import TimelineFeature
from model_tuning_workspace.synthetic_data_pipeline.features.unrelated_info import UnrelatedInfoFeature
from model_tuning_workspace.synthetic_data_pipeline.features.witnesses import WitnessesFeature
from model_tuning_workspace.synthetic_data_pipeline.framework.pipeline import PipelineStep, PipelineContext


class GenerateMEReportStep(PipelineStep):

    def __init__(self, synth_data_gen_model: ModelExecutor):
        super().__init__("generate_me_report")
        self.synth_data_gen_model = synth_data_gen_model

    def execute(self, context: PipelineContext) -> tuple[str, bool]:
        participant_ft = context.get_feature("participants", ParticipantsFeature)
        witnesses_ft = context.get_feature("witnesses", WitnessesFeature)
        location_ft = context.get_feature("location", LocationFeature)
        mortality_cause_ft = context.get_feature("mortality_cause", MortalityCauseFeature)
        motive_ft = context.get_feature("motive", MotiveFeature)
        timeline_ft = context.get_feature("timeline", TimelineFeature)
        irr_info_ft = context.get_feature("unrelated_info", UnrelatedInfoFeature)

        victim = participant_ft.get_victim()
        victim_dob = victim.age_feature.get_dob()
        date_of_case = timeline_ft.date_of_incident.get_date_of_case()
        victims_age = date_of_case.year - victim_dob.year

        sys_msg = _write_sys_msg()
        usr_msg = _write_user_msg(
            participants=participant_ft.build_prompt(),
            witnesses=witnesses_ft.build_prompt(),
            location=location_ft.build_prompt(),
            mortality_cause=mortality_cause_ft.build_prompt(),
            motive=motive_ft.build_prompt(),
            timeline=timeline_ft.build_prompt(),
            irr_info=irr_info_ft.build_prompt(),
            victims_age=victims_age
        )

        model_response = self.synth_data_gen_model.execute(sys_msg=sys_msg, user_input=usr_msg)

        output = model_response
        context.set_output(self.step_name, output)
        return output, True

def _write_user_msg(
    participants: str,
    witnesses: str,
    location: str,
    mortality_cause: str,
    motive: str,
    timeline: str,
    irr_info: str,
    victims_age: int
):
    return f"""
{participants.strip()}

## Victims age
{victims_age} years

{witnesses.strip()}

{location.strip()}

{mortality_cause.strip()}

{motive.strip()}

{timeline.strip()}

## Further timeline info
The key events refer to several events that happened before the death of the victim. 
They should provide a clear timeline of cohesive step by step events that led to the death of the victim.
If present and relevant, provide details on the suspect as they relate to the case.

{irr_info.strip()}
""".strip()


def _write_sys_msg():
    return """
# Context
You will create a short and concise medical examiners narrative based upon the information provided by the user.
It should start with {age} year old {sex}
""".strip()
