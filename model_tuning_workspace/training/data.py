import json

from datasets import Dataset
from transformers import AutoTokenizer


def convert_jsonl_to_dataset(jsonl_path: str, hf_model: str) -> tuple[Dataset, str]:
    """
    Convert JSONL file to a Hugging Face dataset with formatted templates.

    Returns:
        Dataset: Hugging Face dataset with formatted text
    """
    tokenizer = AutoTokenizer.from_pretrained(hf_model)
    formatted_texts = []

    # Read and process JSONL file
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            conversation = data["conversation"]

            formatted = tokenizer.apply_chat_template(
                conversation,
                tokenize=False,
                add_generation_prompt=False
            ) + tokenizer.eos_token
            formatted_texts.append(formatted)

    dataset_text_field = "text"
    return Dataset.from_dict({dataset_text_field: formatted_texts}), dataset_text_field
