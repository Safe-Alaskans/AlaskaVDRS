import random
from datetime import timedelta

from model_tuning_workspace.models.model_executor import ModelExecutor
from model_tuning_workspace.synthetic_data_pipeline.features.mortality_cause import MortalityCauseFeature
from model_tuning_workspace.synthetic_data_pipeline.features.participants import ParticipantsFeature
from model_tuning_workspace.synthetic_data_pipeline.features.timeline import TimelineFeature
from model_tuning_workspace.synthetic_data_pipeline.framework.pipeline import PipelineStep, PipelineContext
from model_tuning_workspace.synthetic_data_pipeline.steps.autopsy_gen_utils.create_final_autopsy_doc import \
    create_final_autopsy_doc
from model_tuning_workspace.synthetic_data_pipeline.steps.autopsy_gen_utils.gen_clothing_list import generate_clothing_list
from model_tuning_workspace.synthetic_data_pipeline.steps.autopsy_gen_utils.gen_evidence_of_injury import \
    generate_evidence_of_injury
from model_tuning_workspace.synthetic_data_pipeline.steps.autopsy_gen_utils.gen_general_desc import \
    generate_general_desc
from model_tuning_workspace.synthetic_data_pipeline.steps.autopsy_gen_utils.generate_conclusive_remarks import \
    generate_conclusive_remarks


class GenerateAutopsyStep(PipelineStep):

    def __init__(self, synth_data_gen_model: ModelExecutor):
        super().__init__(step_name="gen_autopsy")
        self.synth_data_gen_model = synth_data_gen_model


    def execute(self, context: PipelineContext) -> tuple[str, bool]:
        mortality_cause_ft = context.get_feature("mortality_cause", MortalityCauseFeature)
        mortality_cause = mortality_cause_ft.build_prompt()

        participant_ft = context.get_feature("participants", ParticipantsFeature)
        victim = participant_ft.get_victim()

        evidence_of_inj = generate_evidence_of_injury(
            model_exec=self.synth_data_gen_model,
            mortality_cause=mortality_cause,
        )

        conclusive_remarks = generate_conclusive_remarks(
            model_exec=self.synth_data_gen_model,
            evidence_of_injury=evidence_of_inj,
            mortality_cause=mortality_cause,
        )

        clothing_list = generate_clothing_list(
            model_exec=self.synth_data_gen_model,
            victim=victim,
        )

        general_desc = generate_general_desc(
            model_exec=self.synth_data_gen_model,
            victim=victim,
            mortality_cause=mortality_cause,
        )

        timeline_ft = context.get_feature("timeline", TimelineFeature)
        case_date = timeline_ft.date_of_incident.get_date_of_case()
        days_after_incident = int(timeline_ft.days_after_case_before_autopsy.selected_value)
        autopsy_date = case_date + timedelta(days=days_after_incident)

        case_number = _generate_case_number()

        autopsy_doc = create_final_autopsy_doc(
            general_desc=general_desc,
            evidence_of_injury=evidence_of_inj,
            clothing_list=clothing_list,
            conclusive_remarks=conclusive_remarks,
            victim_name=victim.full_name,
            case_number=case_number,
            date_of_exam=autopsy_date.strftime("%B %d, %Y"),
        )

        context.set_output(self.step_name, autopsy_doc)
        return autopsy_doc, True

def _generate_case_number():
    case_num_prefix = str(random.randint(1, 99)).zfill(2)
    case_num = str(random.randint(0, 99999)).zfill(5)
    return f"#{case_num_prefix}-{case_num}"