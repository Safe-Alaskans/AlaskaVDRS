from typing import List

from input_doc import InputDoc


def build_user_message(input_docs: List[InputDoc]) -> str:
    docs = "\n".join(
        f"## {doc.document_name}:{doc.document_text}"
        for doc in input_docs
    )

    # print(docs)

    return f"""
# Docs

{docs}

Provide only the narrative no other text or formatting is required.""".strip()

def build_user_message_revision(narrative: str, feedback: str, input_docs: List[InputDoc]) -> str:

    docs = "\n".join(
        f"## {doc.document_name}:{doc.document_text}"
        for doc in input_docs
    )

    message = f"""# Narrative:
{narrative}

# Feedback:
{feedback}

# Docs
{docs}

Provide only the revised narrative, no other text or formatting is required."""
    
    return message.strip()

