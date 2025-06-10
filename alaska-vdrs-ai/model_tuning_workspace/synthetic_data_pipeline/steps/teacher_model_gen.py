from model_tuning_workspace.models.model_executor import ModelExecutor
from model_tuning_workspace.prompting.input_doc import InputDoc
from model_tuning_workspace.prompting.user_msg import build_user_message
from model_tuning_workspace.prompting.system_msg import sys_msg
from model_tuning_workspace.synthetic_data_pipeline.framework.pipeline import PipelineStep, PipelineContext


class TeacherModelGenStep(PipelineStep):

    def __init__(self, teacher_model: ModelExecutor):
        super().__init__(step_name="teacher_model_gen")
        self.teacher_model = teacher_model

    def execute(self, context: PipelineContext) -> tuple[str, bool]:
        me_report = context.get_output("generate_me_report")
        me_input_doc = InputDoc(document_name="ME Report", document_text=me_report)

        autopsy_report = context.get_output("gen_autopsy")
        autopsy_input_doc = InputDoc(document_name="Autopsy Report", document_text=autopsy_report)

        toxicology_report = context.get_output("gen_toxicology_report")
        toxicology_input_doc = InputDoc(document_name="Toxicology Report", document_text=toxicology_report)

        teacher_input_docs = [me_input_doc, autopsy_input_doc, toxicology_input_doc]
        teacher_usr_msg = build_user_message(input_docs=teacher_input_docs)
        teacher_sys_msg = sys_msg

        teacher_resp = self.teacher_model.execute(sys_msg=teacher_sys_msg, user_input=teacher_usr_msg)
        context.set_output(self.step_name, teacher_resp)
        return teacher_resp, True

