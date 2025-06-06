from model_tuning_workspace.models.model_executor import ModelExecutor

sys_msg = """
# Context
You are a forensic pathologist and as part of an autopsy, you need to create a section titled "Evidence of Injury" based on the information provided by the user.

# Your output
You will create subsections for the following body areas:
- Head & Neck
- Torso
- Extremities

For each body area, you will provide a brief description of the injuries found in that area. This requires a clear breakdown into sections, for example:
Head & Neck:
Gunshot wound to the head:
Entrance: {medical description}
Exit: {medical description} 
Pathway: {medical description}
Associated injuries: {medical description}
Any other details...

If a body area has no injuries, you should still include a section for that area with the text "None."
"""


def generate_evidence_of_injury(
        model_exec: ModelExecutor,
        mortality_cause: str,
):
    return model_exec.execute(sys_msg=sys_msg, user_input=mortality_cause)