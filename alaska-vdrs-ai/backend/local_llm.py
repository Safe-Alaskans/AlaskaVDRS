import os
from typing import List

import requests

from case_loader import load_case_docs_in_chunks
from prompting.input_doc import InputDoc
from prompting.system_msg import SYS_MSG, SYS_MSG_REVISION
from prompting.user_msg import build_user_message, build_user_message_revision
from loguru import logger

should_mock = False

ollama_model_name = os.getenv("OLLAMA_MODEL_NAME")
ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
if ollama_model_name is None:
    raise Exception("OLLAMA_MODEL_NAME environment variable not set")

def exec_llm(docs: List[InputDoc]) -> str:
    sys_msg = SYS_MSG
    usr_msg = build_user_message(docs)
    
    if should_mock:
        return "This is a mock response"
    response = _make_chat_completion(sys_msg, usr_msg)
    return response["choices"][0]["message"]["content"]

def exec_llm_revision(narrative: str, feedback: str, docs: List[InputDoc]) -> str:
    sys_msg = SYS_MSG_REVISION
    usr_msg = build_user_message_revision(narrative, feedback, docs)
    
    if should_mock:
        return "This is a mock response"
    response = _make_chat_completion(sys_msg, usr_msg)
    return response["choices"][0]["message"]["content"]

def exec_llm_refine(chunks: List[List[InputDoc]]) -> str:
    """Execute the refine approach for large document summarization."""
    
    # Process first chunk to get initial narrative
    logger.info("Generating initial narrative from first chunk")
    narrative = exec_llm(chunks[0])
    
    # Process remaining chunks to refine the narrative
    for i, chunk in enumerate(chunks[1:], 1):
        logger.info(f"Refining narrative with chunk {i+1}/{len(chunks)}")
        feedback = "Please refine the narrative integrating neccessary information from the additional documents while maintaining the same format and structure."
        narrative = exec_llm_revision(narrative, feedback, chunk)
    
    return narrative

def exec_llm_user_revision(narrative: str, user_feedback: str, chunks: List[List[InputDoc]]):
    """
    Execute revision with user feedback using document chunking to process large documents.
    """

    # Initialize revised narrative with original
    revised_narrative = narrative
    
    # Process first chunk with original user feedback
    logger.info(f"Starting revision with user feedback: {user_feedback}")
    revised_narrative = exec_llm_revision(revised_narrative, user_feedback, chunks[0])
    
    # Process remaining chunks
    for i, chunk in enumerate(chunks[1:], 1):
        logger.info(f"Continuing revision with chunk {i+1}/{len(chunks)}")
        chunk_feedback = (
            f"Continue refining based on the original feedback: '{user_feedback}' "
            f"Now consider this information from theadditional document chunk while maintaining the same format and structure."
        )
        revised_narrative = exec_llm_revision(revised_narrative, chunk_feedback, chunk)
    
    return revised_narrative


def _make_chat_completion(sys_msg: str, user_msg: str, temp: float = 0.1) -> dict:
    headers = {
        "Content-Type": "application/json",
    }
    
   
    data = {
        "model": ollama_model_name,
        "messages": [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": user_msg}
        ],
        "temperature": temp
    }

    try:
        host = ollama_base_url
        
        # logger.debug(host)
        # logger.debug(ollama_model_name)

        response = requests.post(
            f"{host}/v1/chat/completions",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"API call failed: {str(e)}")