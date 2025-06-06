import json
import os

from dotenv import load_dotenv

from model_tuning_workspace.prompting.system_msg import sys_msg
from model_tuning_workspace.synthetic_data_pipeline.storage.mongo_storage import MongoDBHandler

if __name__ == "__main__":
    load_dotenv()
    db_handler = MongoDBHandler(
        connection_string=os.getenv('MONGO_CONNECTION_STRING'),
        database_name=os.getenv('MONGO_DB_NAME')
    )

    all_dps = db_handler.get_all_documents(collection_name="synthetic_data")

    all_conversations = []
    for dp in all_dps:

        me_report = dp['outputs']['generate_me_report']
        autopsy_report = dp['outputs']['gen_autopsy']
        toxicology_report = dp['outputs']['generate_toxicology_report']

        recreated_user_input = f"# Docs\n\n## ME Report: {me_report}\n## Autopsy Report: {autopsy_report}\n## Toxicology Report: {toxicology_report}"

        conversation = {
            "conversation": [
                {
                    "role": "system",
                    "content": sys_msg,
                },
                {
                    "role": "user",
                    "content": recreated_user_input,
                },
                {
                    "role": "assistant",
                    "content": dp['outputs']['teacher_model_gen'],
                },
            ]
        }
        all_conversations.append(conversation)

    with open("all_conversations_v0_3.jsonl", "w") as f:
        for conv in all_conversations:
            f.write(json.dumps(conv) + "\n")