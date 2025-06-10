import os

import dotenv
from openai import OpenAI

from model_tuning_workspace.models.model_executor import ModelExecutor


class VLLMModel(ModelExecutor):
    ai_model_name: str = "VLLM"
    serverless_endpoint: str
    model: str

    def __init__(self):
        dotenv.load_dotenv()
        self.client = OpenAI(
            api_key=os.getenv("RUNPOD_API_KEY"),
            base_url=self.serverless_endpoint,
        )

    def execute(self, sys_msg: str, user_input: str) -> str:
        message = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": sys_msg,
                },
                {
                    "role": "user",
                    "content": user_input,
                },
            ],
        )

        return message.choices[0].message.content


class NvdrsV0Dot1(VLLMModel):
    ai_model_name: str = "NVDRS-v0.1"
    serverless_endpoint: str = "https://api.runpod.ai/v2/fo8nlxakp3dnse/openai/v1"
    model: str = "Dan-AiTuning/NVDRS-v0.1"