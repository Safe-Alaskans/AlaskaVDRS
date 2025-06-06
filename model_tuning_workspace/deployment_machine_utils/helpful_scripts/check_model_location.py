from pathlib import Path

def check_model_exists(model_dir_path: str) -> bool:
    path = Path(model_dir_path)
    path_exists = path.exists()
    path_is_dir = path.is_dir()

    could_load = path_exists and path_is_dir

    if not could_load:
        print(f"Model not found at {model_dir_path}")
        return False

    # Check files contain .safetensors
    model_files = list(path.glob("*.safetensors"))
    if len(model_files) == 0:
        print(f"Model not found at {model_dir_path}")
        return False

    json_files = list(path.glob("*.json"))
    if len(json_files) == 0:
        print(f"Model not found at {model_dir_path}")
        return False

    return True

if __name__ == "__main__":
    # Get dir from args
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_dir", type=str, required=True)
    args = parser.parse_args()

    exists = check_model_exists(args.model_dir)
    if exists:
        print(f"Model found at {args.model_dir}")
    else:
        print(f"Model not found at {args.model_dir}")
