from huggingface_hub import snapshot_download
from pathlib import Path
import os

def download_model(model_id, output_dir):
    """
    Downloads a model from Hugging Face Hub to a local directory.

    Args:
        model_id (str): The model ID on Hugging Face (e.g., 'bert-base-uncased')
        output_dir (str): Local directory path where the model should be saved
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        # Download the model files
        local_dir = snapshot_download(
            repo_id=model_id,
            local_dir=output_dir,
            local_dir_use_symlinks=False  # Download actual files instead of symlinks
        )
        print(f"Successfully downloaded model '{model_id}' to {local_dir}")

        # List downloaded files
        print("\nDownloaded files:")
        for file in os.listdir(local_dir):
            print(f"- {file}")

    except Exception as e:
        print(f"Error downloading model: {str(e)}")

if __name__ == "__main__":
    # Example usage
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--hf_model_id", type=str, required=True)
    args = parser.parse_args()

    parser.add_argument("--output_dir", type=str, required=False)

    output_dir = args.output_dir
    if output_dir is None:
        output_dir = "./models"

    download_model(args.hf_model_id, output_dir)