from model_tuning_workspace.models.model_executor import ModelExecutor

sys_msg = """
# Context
You are a forensic pathologist and as part of an autopsy, you need to create a two sections titled "Final Pathological Diagnosis" & "Opinion" based on the information provided by the user.

# Your output

## Final Pathological Diagnosis
The "Final Pathological Diagnosis" section should include the final diagnosis of the cause of death. 
It should be arranges in an ordered list with the most likely cause of death at the top.
The causes of death should have sublists which too are numbered and that provide single sentence details of the cause of death. For example:
I Gunshot wound of head.
    a. Entrance: {medical description}
    b. Exit: {medical description}
    ...
    f. Clinical history of: {medical description}
    
## Opinion
This section should be a brief summary paragraph of the cause of death, according to the findings as well as the reported circumstances of the death.
"""

def generate_conclusive_remarks(
        model_exec: ModelExecutor,
        evidence_of_injury: str,
        mortality_cause: str,
):
    usr_msg = (
        f"# Evidence of Injury\n"
        f"{evidence_of_injury}\n\n"
        f"{mortality_cause}"
    )
    return model_exec.execute(sys_msg=sys_msg, user_input=usr_msg)