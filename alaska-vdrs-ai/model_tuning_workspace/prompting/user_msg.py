from typing import List

from model_tuning_workspace.prompting.input_doc import InputDoc


def build_user_message(input_docs: List[InputDoc]) -> str:
    docs = "\n".join(
        f"## {doc.document_name}\n{doc.document_text}"
        for doc in input_docs
    )

    return f"""
# Docs

{docs}
""".strip()