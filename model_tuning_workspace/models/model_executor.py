import abc


class ModelExecutor(abc.ABC):
    """
    Abstract base class for executing single prompt, single response type LLM calls.

    This class defines the interface for executing a model with a given system message and user input,
    and returning the model's response. Subclasses should implement the `execute` method to provide
    the specific logic for interacting with the LLM.
    """

    ai_model_name: str

    @abc.abstractmethod
    def execute(self, sys_msg: str, user_input: str) -> str:
        pass
