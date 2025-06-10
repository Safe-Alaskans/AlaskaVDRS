from model_tuning_workspace.models.model_executor import ModelExecutor
from model_tuning_workspace.synthetic_data_pipeline.features.models.participant import Participant

sys_msg = """
The user will provide you with the clothing found on somebody coming in for an autopsy. 
Your job is to create a list of 5-10 items of clothing that the person was wearing which is consistent with the information provided by the user.

# Your output
Only a numbered list of clothing items found on the person. 
No other text before or after. Each item should be on a new line and numbered.
"""

def generate_clothing_list(
        model_exec: ModelExecutor,
        victim: Participant,
):
    clothing_description = (
        f"# Person details\n"
        f"Age: {victim.age_feature.selected_value}\n"
        f"Weight: {victim.physical_description.weight_feature.selected_value}\n"
        f"Height: {victim.physical_description.height_feature.selected_value}\n"
        f"# General clothing\n"
        f"{victim.attire_feature.selected_value}\n\n"
    )
    return model_exec.execute(sys_msg=sys_msg, user_input=clothing_description)