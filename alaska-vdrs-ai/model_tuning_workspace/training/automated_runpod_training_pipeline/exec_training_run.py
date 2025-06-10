import os

from dotenv import load_dotenv

from model_tuning_workspace.training.automated_runpod_training_pipeline.runpod_trainer import RunPodTrainer

if __name__ == "__main__":
    load_dotenv()

    trainer = RunPodTrainer(
        runpod_api_key=os.getenv("RUNPOD_API_KEY"),
        hf_token=os.getenv("HF_TOKEN"),
        path_to_dataset="./all_conversations.jsonl",
        model_to_ft="meta-llama/Llama-3.1-8B-Instruct",
        model_name="NVDRS",
        new_model_version=0.2,
        training_script_path="./train.py",
        gpu_id="NVIDIA A100 80GB PCIe",
        num_gpus=1,
        max_seq_length=5500,
    )

    if trainer.setup_training_environment():
        trained_successfully = trainer.run_training()
        if trained_successfully:
            print("Training completed successfully")
        else:
            print("Training failed")
    else:
        print("Failed to setup training environment")