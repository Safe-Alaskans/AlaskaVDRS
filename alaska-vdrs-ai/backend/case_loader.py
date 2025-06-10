import base64
import io
import os
from pathlib import Path
import re
import shutil
from typing import Dict, List
import unicodedata
from flask import current_app
import fitz
import docx
from loguru import logger
from transformers import AutoTokenizer
 # Use Marker for conversion
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from marker.config.parser import ConfigParser
from input_doc import InputDoc
import tempfile

# config = {
#     "output_format": "markdown",
#     "disable_image_extraction": True
# }
# config_parser = ConfigParser(config)

temp_dir = Path(os.getcwd()).parent / "temp_marker_data"
os.makedirs(temp_dir, exist_ok=True)


# Load the finetuned tokenizer
tokenizer = AutoTokenizer.from_pretrained("modularai/Llama-3.1-8B-Instruct-GGUF")
converter = PdfConverter(
                    artifact_dict=create_model_dict(),
                )

def clean_text(text):

    # Normalize Unicode to ensure consistency (e.g., non-breaking spaces become normal spaces)
    text = unicodedata.normalize("NFKC", text)
    
    # Replace non-breaking spaces and all newlines
    text = text.replace("\xa0", " ").replace("\n", " ").replace("\r", " ")
    
    # Collapse multiple spaces into a single space using regex
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text.strip()

def categorize_document(file_info):
    """Categorize a document based on its name."""
    file_name = file_info.get('name', '').lower()
    
    if "me" in file_name or "menarrative" in file_name:
        return "ME Report"
    elif "autopsy" in file_name:
        return "Autopsy Report"
    elif "tox" in file_name or "toxicology" in file_name:
        return "Toxicology Report"
    else:
        return "Other"

def extract_text_from_file(file_info, use_marker=False):
    """Extract text from a file."""
    file_name = file_info.get('name', 'unknown')
    file_type = file_info.get('type', '')
    file_data = file_info.get('data', '')
    
    # Skip if no data
    if not file_data:
        return ""
        
    # Extract base64 data
    if ',' in file_data:
        file_data = file_data.split(',', 1)[1]

    # Decode the base64 data
    try:
        binary_data = base64.b64decode(file_data)
        
        # Handle different file types
        if file_type.startswith('text/') or file_name.endswith(('.txt', '.csv', '.json')):
            try:
                text_content = binary_data.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text_content = binary_data.decode('cp1252')
                except UnicodeDecodeError:
                    text_content = binary_data.decode('utf-8', errors='replace')
                    
        # Handle PDF files
        elif file_type == 'application/pdf' or file_name.endswith('.pdf'):
            try:
                pdf_document = fitz.open(stream=binary_data, filetype="pdf")
                text_content = ""
                
                for page_num in range(len(pdf_document)):
                    page = pdf_document.load_page(page_num)
                    text_content += page.get_text()
                
                pdf_document.close()
            except Exception as e:
                logger.error(f"Error processing PDF: {e}")
                return ""
        
        # Handle DOCX files
        elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or file_name.endswith('.docx'):
            try:
                doc = docx.Document(io.BytesIO(binary_data))
                text_content = ""
                for para in doc.paragraphs:
                    text_content += para.text + "\n"
            except Exception as e:
                logger.error(f"Error processing DOCX: {e}")
                return ""
        
        # Unsupported file type
        else:
            logger.warning(f"Unsupported file type: {file_type}")
            return ""
        
        # Clean up the text
        return clean_text(text_content)
        
    except Exception as e:
        logger.error(f"Error decoding file {file_name}: {e}")
        return ""

def load_example_case_docs(case_id: int) -> List[InputDoc]:
    parent_dir = Path(__file__).parent
    case_dir = parent_dir / "assets" / "cases" / f"case_{case_id}"
    print(f"Looking for case {case_id} in {case_dir}")
    if not case_dir.exists():
        print(f"Case {case_id} not found")
        return []

    case_docs = []
    for file in case_dir.iterdir():
        if file.is_file() and file.suffix == ".txt":
            with open(file, "r", encoding="utf-8") as f:
                case_docs.append(InputDoc(document_name=file.stem, document_text=f.read()))

    return case_docs

def truncate_text_to_token_limit(text: str, token_limit: int, tokenizer) -> str:
    """
    Truncate text to fit within token limit.
    
    Args:
        text: The text to truncate
        token_limit: Maximum number of tokens allowed
        tokenizer: The tokenizer to use
        
    Returns:
        Truncated text that fits within token limit
    """

    tokens = tokenizer.encode(text)
    
    if len(tokens) <= token_limit:
        return text
    
    # Truncate tokens and decode
    truncated_tokens = tokens[:token_limit]
    try:

        return tokenizer.decode(truncated_tokens)
      
    except Exception as e:
        
        print(f"Error during text truncation: {e}")
        
        # Fallback approach - approximate by character ratio
        approx_ratio = token_limit / len(tokens)
        char_limit = int(len(text) * approx_ratio)
        
        return text[:char_limit] + "..."
    
def distribute_tokens_proportionally(doc_infos, max_tokens):
    """
    Distribute tokens to documents proportionally based on their original size.
    
    Args:
        doc_infos: List of document information dictionaries
        max_tokens: Maximum number of tokens to distribute
        
    Returns:
        List of token allocations for each document
    """

    total_original_tokens = sum(doc['tokens'] for doc in doc_infos)
    
    # Calculate proportional allocation
    allocations = []
    for doc in doc_infos:
        proportion = doc['tokens'] / total_original_tokens
        allocation = int(proportion * max_tokens)
        allocations.append(allocation)
    
    # Adjust for rounding errors - assign any remaining tokens
    allocated_sum = sum(allocations)
    remainder = max_tokens - allocated_sum
    
    # Add remainder to the largest document or distribute it
    if remainder > 0:
        # Find index of document with most tokens
        largest_doc_index = max(range(len(doc_infos)), key=lambda i: doc_infos[i]['tokens'])
        allocations[largest_doc_index] += remainder
    
    return allocations

def load_case_docs(files_data: List[Dict], folder_name: str, case_id: int = None, max_tokens = 3500, use_marker = False) -> List[InputDoc]:
    
    # Can create a case_dir in the assets/cases folder
    storage_dir = Path(os.getcwd()) / "local_server" / "assets" / "cases"
    print(f"Storage directory: {storage_dir}")

    if case_id:
        case_dir = storage_dir / f"case_{case_id}"
    else:
        case_dir = storage_dir / folder_name
        
    case_dir.mkdir(parents=True, exist_ok=True)

    try:
        debug_mode = current_app.debug
    except RuntimeError:
        debug_mode = False

    # Save the files to the case_dir and also load them into case_docs
    case_docs = []
    total_token_count = 0
    
    # First pass: collect all document texts and their token counts
    doc_infos = []
 
    with tempfile.TemporaryDirectory() as temp_dir:
        for file_info in files_data:
            file_name = file_info.get('name', 'unknown')
            file_type = file_info.get('type', '')
            file_data = file_info.get('data', '')
            safe_name = "".join(c for c in file_name if c.isalnum() or c in "._-")
            temp_file_path = os.path.join(temp_dir, f"temp_{safe_name}")

            print(f"Processing file {file_name} with type {file_type}")
            
            # Skip if no data
            if not file_data:
                continue
                
            # Extract base64 data (remove data URL prefix)
            if ',' in file_data:
                file_data = file_data.split(',', 1)[1]

            # Categorize the file based on its name
            category = "Other"
            if "me" in file_name.lower() or "menarrative" in file_name.lower():
                category = "ME Report"
            elif "autopsy" in file_name.lower():
                category = "Autopsy Report"
            elif "tox" in file_name.lower() or "toxicology" in file_name.lower():
                category = "Toxicology Report"

            # Decode the base64 data
            try:
                binary_data = base64.b64decode(file_data)
                # Save file temporarily to disk for Marker processing if needed
                with open(temp_file_path, 'wb') as f:
                    f.write(binary_data)
            

                # Add pdf support
                if file_type.startswith('text/') or file_name.endswith(('.txt', '.csv', '.json')):
                    
                    # Try different encodings when UTF-8 fails
                    try:
                        text_content = binary_data.decode('utf-8')
                    except UnicodeDecodeError:
                        # Try Windows-1252 encoding if UTF-8 fails
                        try:
                            text_content = binary_data.decode('cp1252')
                            print(f"Decoded file {file_name} with cp1252")
                        except UnicodeDecodeError:
                            # If that fails too, try with error handling
                            text_content = binary_data.decode('utf-8', errors='replace')
                            print(f"Decoded file {file_name} with utf-8")
                    
                # Handle PDF files
                elif file_type == 'application/pdf' or file_name.endswith('.pdf'):
                    try:     
                        if use_marker:
                            rendered = converter(str(temp_file_path))
                            text_content, _, _ = text_from_rendered(rendered)
                        else:
                            pdf_document = fitz.open(stream=binary_data, filetype="pdf")
                            text_content = ""
                            
                            for page_num in range(len(pdf_document)):
                                page = pdf_document.load_page(page_num)
                                text_content += page.get_text()
                        
                            pdf_document.close()
                    except ImportError:
                        print(f"PyMuPDF (fitz) library not installed. Skipping PDF file {file_name}")
                
                # Handle DOCX files
                elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or file_name.endswith('.docx'):
                    try:
                        doc = docx.Document(io.BytesIO(binary_data))
                        text_content = ""
                        for para in doc.paragraphs:
                            text_content += para.text
                    except ImportError:
                        print(f"python-docx library not installed. Skipping DOCX file {file_name}")

                # Clean up temporary file
                if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                
                # Normalize line breaks and whitespace
                if not use_marker or file_type != 'application/pdf':
                    text_content = clean_text(text_content)

                # Get token count for this document
                doc_token_count = len(tokenizer.encode(text_content))
                
                # Store document info for later processing
                doc_infos.append({
                    'name': category,
                    'text': text_content,
                    'tokens': doc_token_count
                })
            
            except Exception as e:
                print(f"Error decoding file {file_name}: {e}")
    
     # Calculate total tokens across all documents
    total_tokens = sum(doc['tokens'] for doc in doc_infos)
    print(f"Total tokens across all documents: {total_tokens}")
    
    # If total tokens is less than or equal to max, include all documents as is
    if total_tokens <= max_tokens:
        for doc_info in doc_infos:
            case_docs.append(InputDoc(
                document_name=doc_info['name'],
                document_text=doc_info['text']
            ))
            print(f"Added full document {doc_info['name']}: {doc_info['tokens']} tokens")
        
        print(f"Total token count: {total_tokens}/{max_tokens}")
        return case_docs
    
    # Otherwise, we need to distribute tokens across documents
    print(f"Need to distribute {max_tokens} tokens across {len(doc_infos)} documents")
    
    # Option 1: Distribute tokens proportionally based on original size
    proportion_based_tokens = distribute_tokens_proportionally(doc_infos, max_tokens)
    
    # Add truncated versions of each document
    total_token_count = 0
    for i, doc_info in enumerate(doc_infos):
        allocated_tokens = proportion_based_tokens[i]
        if allocated_tokens <= 0:
            # Ensure each document gets at least some minimal representation
            allocated_tokens = min(50, max_tokens - total_token_count)
        
        if allocated_tokens <= 0:
            print(f"Cannot allocate any tokens to document {doc_info['name']}")
            continue
            
        truncated_text = truncate_text_to_token_limit(doc_info['text'], allocated_tokens, tokenizer)
        truncated_tokens = len(tokenizer.encode(truncated_text))
        
        # Adjust if we're about to exceed the limit
        if total_token_count + truncated_tokens > max_tokens:
            available_tokens = max_tokens - total_token_count
            if available_tokens > 0:
                truncated_text = truncate_text_to_token_limit(truncated_text, available_tokens, tokenizer)
                truncated_tokens = len(tokenizer.encode(truncated_text))
            else:
                print(f"Cannot add more content from {doc_info['name']}")
                continue
        
        case_docs.append(InputDoc(
            document_name=doc_info['name'],
            document_text=truncated_text
        ))
        
        total_token_count += truncated_tokens
        print(f"Added partial document {doc_info['name']}: {truncated_tokens}/{doc_info['tokens']} tokens")
        
        # Check if we've reached the limit
        if total_token_count >= max_tokens:
            break
    
    print(f"Final token count: {total_token_count}/{max_tokens}")
    return case_docs

def load_case_docs_in_chunks(files_data, folder_name, case_id=None, max_tokens=3000, use_marker=False):
    """Load case documents in chunks that maximize token usage up to the limit."""
    
    # Extract text from all files and categorize them
    doc_infos = []
    for file_info in files_data:
        text = extract_text_from_file(file_info, use_marker)
        category = categorize_document(file_info)
        
        if not text:
            continue
            
        token_count = len(tokenizer.encode(text))
        
        doc_infos.append({
            'name': category,
            'text': text,
            'tokens': token_count
        })
    
    # Sort documents by category priority
    category_priority = {
        "ME Report": 0,
        "Autopsy Report": 1,
        "Toxicology Report": 2,
        "Other": 3
    }
    doc_infos.sort(key=lambda x: category_priority.get(x['name'], 4))
    
    # Create chunks maximizing token usage
    chunks = []
    
    # Track how much of each document we've used
    doc_positions = [0] * len(doc_infos)
    all_docs_processed = False
    
    while not all_docs_processed:
        current_chunk = []
        current_tokens = 0
        docs_added_to_chunk = False
        
        # Try to add documents to current chunk
        for i, doc_info in enumerate(doc_infos):
            # Skip if we've already processed this document completely
            if doc_positions[i] >= len(doc_info['text']):
                continue
                
            # Calculate how much text remains in this document
            remaining_text = doc_info['text'][doc_positions[i]:]
            remaining_tokens = len(tokenizer.encode(remaining_text))
            
            # If entire remaining document fits in chunk, add it
            if current_tokens + remaining_tokens <= max_tokens:
                current_chunk.append(InputDoc(document_name=doc_info['name'], document_text=remaining_text))
                current_tokens += remaining_tokens
                doc_positions[i] = len(doc_info['text'])  # Mark as fully processed
                docs_added_to_chunk = True
            else:
                # Document doesn't fit entirely, take as much as possible
                # Use binary search to find maximum text that fits
                left, right = 0, len(remaining_text)
                chunk_text = ""
                
                while left <= right:
                    mid = (left + right) // 2
                    test_text = remaining_text[:mid]
                    test_tokens = len(tokenizer.encode(test_text))
                    
                    if current_tokens + test_tokens <= max_tokens:
                        chunk_text = test_text
                        left = mid + 1
                    else:
                        right = mid - 1
                
                # If we found text that fits, add it to chunk
                if chunk_text:
                    current_chunk.append(InputDoc(document_name=doc_info['name'], document_text=chunk_text))
                    current_tokens += len(tokenizer.encode(chunk_text))
                    doc_positions[i] += len(chunk_text)  # Update position in document
                    docs_added_to_chunk = True
                
                # Break after adding part of a document - we'll come back to remaining docs in next chunk
                break
        
        # Add this chunk if it contains documents
        if current_chunk:
            chunks.append(current_chunk)
        
        # Check if all documents have been processed
        if not docs_added_to_chunk or all(pos >= len(doc_infos[i]['text']) for i, pos in enumerate(doc_positions)):
            all_docs_processed = True
    
    # Log how many chunks we created
    logger.info(f"Created {len(chunks)} document chunks")
    for i, chunk in enumerate(chunks):
        chunk_tokens = sum(len(tokenizer.encode(doc.document_text)) for doc in chunk)
        logger.info(f"Chunk {i+1}: {len(chunk)} documents, {chunk_tokens} tokens")
    
    return chunks