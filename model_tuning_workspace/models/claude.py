import dotenv
from anthropic import Anthropic

from model_tuning_workspace.models.model_executor import ModelExecutor

SONNET_3_5_MODEL_NAME = "claude-3-5-sonnet-20241022"


class ClaudeApiCaller:

    def __init__(self):
        dotenv.load_dotenv()
        self.client = Anthropic()

    def call_api(
            self,
            sys_msg: str,
            user_input: str,
            model_name: str = SONNET_3_5_MODEL_NAME,
            max_tokens: int = 4000,
            temperature: float = 0.2
    ) -> str:
        message = self.client.beta.messages.create(
            model=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            system=sys_msg,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_input,
                        },

                    ]
                }
            ],
        )

        return message.content[0].text


class Claude35SonnetExec(ModelExecutor):

    ai_model_name = SONNET_3_5_MODEL_NAME

    def __init__(self):
        self.api_caller = ClaudeApiCaller()

    def execute(self, sys_msg: str, user_input: str) -> str:
        resp = self.api_caller.call_api(
            sys_msg=sys_msg,
            user_input=user_input,
            model_name=SONNET_3_5_MODEL_NAME
        )

        return resp
