import torch

def check_available_gpus():
    try:
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            print(f"\nFound {gpu_count} CUDA GPU(s):")
            for i in range(gpu_count):
                print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
        else:
            print("No CUDA GPUs found")
    except ImportError:
        print("PyTorch not installed - cannot check for CUDA GPUs")


if __name__ == "__main__":
    print(f"CUDA available: {torch.cuda.is_available()}")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA version: {torch.version.cuda}")

    check_available_gpus()