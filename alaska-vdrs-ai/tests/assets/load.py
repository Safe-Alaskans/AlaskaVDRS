import os


def load_test_narrative() -> str:
    # Get the directory where load.py is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "test_narrative.txt")
    with open(file_path, "r") as f:
        return f.read()