from model_tuning_workspace.models.model_executor import ModelExecutor
from model_tuning_workspace.synthetic_data_pipeline.features.models.participant import Participant

sys_msg = """
# Context
You are a forensic pathologist and as part of an autopsy, you need to create a section titled "General Description" based on the information provided by the user.

# Your output
You will provide a general description of the body in 2-3 paragraphs. Including details such as the body's physical appearance, general health, identifying features such as finger nails, hair.
Begin with an overall of the body, then work from head to toe, describing the body in a logical order.
You should maintain a medical tone.
You should include measurements of the body, such as height and weight, length of hair.

After this part, you should create a subsection titled "Scars and Marks" and list any scars, marks, or tattoos found on the body.
Start with "The body is that of a".
"""


def generate_general_desc(
        model_exec: ModelExecutor,
        victim: Participant,
        mortality_cause: str,
):
    usr_msg = (
        f"# Decedent\n"
        f"{victim.to_prompt_str()}\n\n"
        f"{mortality_cause}"
    )
    return model_exec.execute(sys_msg=sys_msg, user_input=usr_msg)
