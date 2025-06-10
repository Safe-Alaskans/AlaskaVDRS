import os

from model_tuning_workspace.prompting.input_doc import InputDoc


def load_txt_input_doc(sub_dir: str, file_name: str) -> InputDoc:
    # Get the directory where load.py is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir,sub_dir, f"{file_name}.txt")
    with open(file_path, "r") as f:
        content = f.read()
        return InputDoc(document_name=file_name, document_text=content)