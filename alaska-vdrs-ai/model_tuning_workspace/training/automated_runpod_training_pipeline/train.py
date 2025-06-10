from unsloth import FastLanguageModel, is_bfloat16_supported
from datasets import Dataset
from transformers import AutoTokenizer, TrainingArguments
from trl import SFTTrainer

import argparse
import json
import os


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

def parse_args():
    parser = argparse.ArgumentParser(description='Model Training Script')
    parser.add_argument('--model_name', type=str, required=True,
                        help='Name of the new fine-tuned model')
    parser.add_argument('--model_version', type=float, required=True,
                        help='Version of the new fine-tuned model')
    parser.add_argument('--model_to_ft', type=str, required=True,
                        help='Base model to fine-tune')
    parser.add_argument('--dataset_path', type=str, required=True,
                        help='Path to the dataset')
    parser.add_argument('--max_seq_length', type=int, required=True,
                        help='Maximum sequence length')
    parser.add_argument('--hf_token', type=str, required=True,
                        help='Hugging Face token')

    return parser.parse_args()

def main():
    args = parse_args()
    model_name = args.model_name
    model_version = args.model_version
    model_to_ft = args.model_to_ft
    dataset_path = args.dataset_path
    max_seq_length = args.max_seq_length
    hf_token = args.hf_token
    os.environ["HF_TOKEN"] = hf_token


    print(f"Loading model: {model_to_ft}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_to_ft,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=False,
        token=hf_token,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        lora_alpha=16,
        lora_dropout=0,
        target_modules=["q_proj", "k_proj", "v_proj", "up_proj", "down_proj", "o_proj", "gate_proj"],
        use_rslora=True,
        use_gradient_checkpointing="unsloth"
    )
    print(model.print_trainable_parameters())

    d_set, dataset_text_field = convert_jsonl_to_dataset(dataset_path, model_to_ft)

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=d_set,
        dataset_text_field=dataset_text_field,
        max_seq_length=max_seq_length,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=2,
            gradient_accumulation_steps=2,
            warmup_steps=3,
            num_train_epochs=3,
            learning_rate=2e-4,
            fp16=not is_bfloat16_supported(),
            bf16=is_bfloat16_supported(),
            logging_steps=1,
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="linear",
            seed=4567,
            output_dir="outputs",
        ),
    )

    final_model_name = f"{model_name}-v{model_version}"
    print(f"Training model: {final_model_name}")
    trainer.train()

    model = FastLanguageModel.for_inference(model)

    commit_msg = "Initial commit"
    commit_desc = "Initial commit of the"

    # Saves just the LoRA adapter
    model.push_to_hub(
        f"{final_model_name}-lora",
        commit_message=commit_msg,
        commit_description=f"{commit_desc} adapter",
        token=hf_token,
        private=True,
    )

    # Saves 16 bit merged model
    model.push_to_hub_merged(
        final_model_name,
        tokenizer,
        save_method="merged_16bit",
        commit_message=commit_msg,
        commit_description=f"{commit_desc} model",
        token=hf_token,
        private=True,
    )

if __name__ == "__main__":
    main()