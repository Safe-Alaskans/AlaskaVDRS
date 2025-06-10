from model_tuning_workspace.models.claude import Claude35SonnetExec
from model_tuning_workspace.models.model_executor import ModelExecutor

# Model used for validating the evals
validator_model: ModelExecutor = Claude35SonnetExec()