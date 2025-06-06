import os
import logging
from datetime import datetime
import concurrent.futures
import pymupdf
import re
from text_chunking import chunk_text_by_tokens, count_tokens
from oaiapi_interaction import rewrite_text_with_openai, get_total_tokens_used
from output_generation import save_as_json, merge_small_json_files, validate_json_files
import platform
import time
import uuid  # Add this import at the top

# Configure logging
logger = logging.getLogger(__name__)

def get_output_directory(file_path, user_suffix):
    """Creates and returns the path to the output directory."""
    parent_dir = os.path.dirname(file_path)
    current_date = datetime.now().strftime("%m%d%y")
    output_dir_name = f"Chunked Output {current_date}"
    
    if user_suffix:
        output_dir_name += f"-{user_suffix}"
    
    output_dir = os.path.join(parent_dir, output_dir_name)
    
    # Check for maximum path length (Windows limitation)
    if platform.system() == "Windows" and len(output_dir) > 260:
        logger.warning("Output directory path is too long for Windows. Shortening...")
        max_length = 260 - len(os.path.dirname(output_dir)) - 1  # -1 for the path separator
        output_dir = output_dir[:max_length]
    
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def get_file_info(input_path):
    """Gathers information about supported files in the input path."""
    supported_files = []
    total_size = 0
    
    if os.path.isfile(input_path):
        if input_path.lower().endswith(('.pdf', '.epub', '.txt')):
            size = os.path.getsize(input_path)
            supported_files.append(input_path)
            total_size += size
    elif os.path.isdir(input_path):
        for root, _, files in os.walk(input_path):
            for file in files:
                if file.lower().endswith(('.pdf', '.epub', '.txt')):
                    file_path = os.path.join(root, file)
                    size = os.path.getsize(file_path)
                    supported_files.append(file_path)
                    total_size += size
    
    return len(supported_files), total_size / (1024 * 1024)  # Return count and size in MB

def process_input(input_path, save_raw_text=False, chunked_output=False, output_suffix=None, debug_mode=False, progress_callback=None, max_workers=1):
    logger.debug(f"Starting process_input with {input_path}")
    output_directory = get_output_directory(input_path, output_suffix)
    processed_files = 0
    total_files = 1 if os.path.isfile(input_path) else len([f for f in os.listdir(input_path) if f.lower().endswith(('.pdf', '.epub', '.txt'))])
    
    if os.path.isfile(input_path):
        def chunk_progress(current_chunk, total_chunks):
            if progress_callback:
                progress_callback(1, total_files, current_chunk, total_chunks)
        
        processed_files = process_file(input_path, save_raw_text, chunked_output, output_directory, debug_mode, chunk_progress)
        if progress_callback:
            progress_callback(1, total_files, 0, 0)  # File complete, reset chunk progress
    elif os.path.isdir(input_path):
        all_files = [f for f in [os.path.join(root, file) for root, _, files in os.walk(input_path) for file in files] if f.lower().endswith(('.pdf', '.epub', '.txt'))]
        
        if max_workers > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(process_file, file_path, save_raw_text, chunked_output, output_directory, debug_mode, 
                                           lambda current_chunk, total_chunks: progress_callback(processed_files + 1, total_files, current_chunk, total_chunks) if progress_callback else None): 
                           file_path for file_path in all_files}
                
                for future in concurrent.futures.as_completed(futures):
                    processed_files += future.result()
                    if progress_callback:
                        progress_callback(processed_files, total_files, 0, 0)  # Reset chunk progress after each file
        else:
            for file_num, file_path in enumerate(all_files, 1):
                def chunk_progress(current_chunk, total_chunks):
                    if progress_callback:
                        progress_callback(file_num, total_files, current_chunk, total_chunks)
                
                processed_files += process_file(file_path, save_raw_text, chunked_output, output_directory, debug_mode, chunk_progress)
                if progress_callback:
                    progress_callback(file_num, total_files, 0, 0)  # Reset chunk progress after each file
    else:
        logger.error(f"Invalid input path: {input_path}")
    
    # Validate JSON files after processing
    logger.info("Validating JSON files...")
    validate_json_files(output_directory)
    
    return processed_files, get_total_tokens_used()  # Return both processed files count and total tokens used

def handle_error():
    while True:
        try:
            user_choice = input("An error occurred. Do you want to (1) Save existing output and exit, (2) Exit without saving, or (3) Continue? Enter 1, 2, or 3: ")
            if user_choice in ['1', '2', '3']:
                if user_choice == '1':
                    print("Saving existing output and exiting...")
                elif user_choice == '2':
                    print("Exiting without saving...")
                return user_choice
            else:
                print("Invalid input. Please enter 1, 2, or 3.")
        except Exception as e:
            logger.error(f"Error in handle_error: {str(e)}")
            print("An error occurred. Please try again.")

def process_file(file_path, save_raw_text=False, chunked_output=False, output_directory=None, debug_mode=False, chunk_progress_callback=None):
    logger.info(f"Processing file: {file_path}")
    
    file_uuid = str(uuid.uuid4())[:8]  # Generate a short UUID for the file
    truncated_filename = f"{file_uuid}_{os.path.splitext(os.path.basename(file_path))[0][:10]}"
    
    if file_path.lower().endswith(('.pdf', '.epub')):
        metadata_dict = extract_text_from_file(file_path)
    elif file_path.lower().endswith('.txt'):
        metadata_dict = extract_text_from_txt(file_path)
    else:
        logger.error(f"Unsupported file format: {file_path}")
        return 0

    if metadata_dict is None:
        logger.error(f"Failed to extract text from file: {file_path}")
        return 0

    logger.info(f"Text and metadata extracted from file: {file_path}")

    full_text = "\n\n".join(page["content"] for page in metadata_dict["content"])
    total_tokens = count_tokens(full_text)
    logger.info(f"Total tokens in full text: {total_tokens}")
    
    max_tokens = 5000  # Maximum tokens per chunk
    text_chunks, is_soft_chunked = chunk_text_by_tokens(full_text, max_tokens=max_tokens)
    logger.debug(f"File {file_path}: is_soft_chunked: {is_soft_chunked}, chunked_output: {chunked_output}")
    
    if chunked_output:
        logger.debug(f"Processing file {file_path} with process_chunked")
        processed_chunks = process_chunked(text_chunks, output_directory, truncated_filename, debug_mode, chunk_progress_callback)
    else:
        logger.debug(f"Processing file {file_path} with process_whole_document")
        processed_chunks = process_whole_document(text_chunks, output_directory, truncated_filename, debug_mode, chunk_progress_callback)
        if is_soft_chunked:
            logger.debug(f"Calling merge_small_json_files for {file_path}")
            merge_small_json_files(output_directory, truncated_filename, is_soft_chunked, chunked_output)

    logger.info(f"Processed {processed_chunks} chunks for {file_path}")

    if save_raw_text:
        raw_text_file_path = os.path.join(output_directory, f"{truncated_filename}_raw.txt")
        with open(raw_text_file_path, 'w', encoding='utf-8') as raw_text_file:
            raw_text_file.write(full_text)

    logger.info(f"Processing complete for {file_path}")
    return processed_chunks

def extract_text_from_file(file_path):
    """Extracts text and metadata from a PDF file with improved formatting and structure."""
    try:
        with pymupdf.open(file_path) as document:
            metadata = document.metadata
            text_content = []
            raw_text = []

            for page in document:
                page_text = page.get_text()
                
                # Clean up the extracted text
                page_text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', page_text)
                page_text = re.sub(r'\n(?!\n)', ' ', page_text)
                page_text = re.sub(r'\n{2,}', '\n\n', page_text)
                page_text = page_text.strip()
                page_text = re.sub(r'\s*Page \d+\s*', '', page_text)

                text_content.append({
                    "page_number": page.number,
                    "content": page_text
                })
                raw_text.append(page_text)

        return {
            "summary": "",
            "creation_date": metadata.get('/CreationDate', 'Unknown'),
            "modification_date": metadata.get('/ModDate', 'Unknown'),
            "total_pages": len(text_content),
            "extracted_date": datetime.now().isoformat(),
            "content": text_content
        }
    except Exception as e:
        logger.error(f"Error extracting text from file {file_path}: {str(e)}")
        return None

def extract_text_from_txt(txt_path):
    """Extracts text from a TXT file."""
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            full_text = file.read()

        metadata_dict = {
            "summary": "",  # Placeholder for the summary
            "total_pages": full_text.count('\n'),
            "extracted_date": datetime.now().isoformat(),
            "content": [{"content": full_text}]
        }

        return metadata_dict
    except Exception as e:
        logger.error(f"Error extracting text from TXT {txt_path}: {str(e)}")
        return None

def process_chunked(text_chunks, output_directory, truncated_filename, debug_mode, chunk_progress_callback=None):
    processed_chunks = []

    total_chunks = len(text_chunks)
    for i, chunk in enumerate(text_chunks, 1):
        if debug_mode:
            logger.debug(f"Processing chunk {i} of {total_chunks}")
        
        chunk_data = rewrite_text_with_openai(chunk)
        if chunk_data:
            chunk_filename = f"{truncated_filename}_chunk_{i:03d}.json"  # Use 3-digit padding for chunk numbers
            chunk_path = os.path.join(output_directory, chunk_filename)
            save_as_json(chunk_data, chunk_path)
            processed_chunks.append(chunk_data)

        if chunk_progress_callback:
            chunk_progress_callback(i, total_chunks)

    return len(processed_chunks)

def process_whole_document(text_chunks, output_directory, truncated_filename, debug_mode, chunk_progress_callback=None):
    total_chunks = len(text_chunks)
    logger.info(f"Document split into {total_chunks} chunks.")

    processed_chunks = []

    for i, chunk in enumerate(text_chunks, 1):
        logger.info(f"Processing chunk {i} of {total_chunks}")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                chunk_data = rewrite_text_with_openai(chunk)
                if chunk_data:
                    processed_chunks.append(chunk_data)
                    logger.info(f"Successfully processed chunk {i}")
                    break  # Successfully processed, break the retry loop
                else:
                    logger.warning(f"Chunk {i} returned no data")
            except Exception as e:
                logger.error(f"Error processing chunk {i} (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying chunk {i} in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to process chunk {i} after {max_retries} attempts.")
        
        if chunk_progress_callback:
            chunk_progress_callback(i, total_chunks)

    logger.info(f"Processed {len(processed_chunks)} out of {total_chunks} chunks.")

    if processed_chunks:
        logger.info("Combining summaries and keywords...")
        combined_summary = combine_summaries([chunk['summary'][0] for chunk in processed_chunks])
        combined_keywords = combine_keywords([chunk['keywords'] for chunk in processed_chunks])

        final_output = {
            "summary": [combined_summary],
            "keywords": combined_keywords,
            "structured_content": [item for chunk in processed_chunks for item in chunk['structured_content']]
        }

        output_filename = f"{truncated_filename}_full.json"
        output_path = os.path.join(output_directory, output_filename)
        save_as_json(final_output, output_path)
        logger.info(f"Saved combined output to {output_path}")
    else:
        logger.error(f"No chunks were successfully processed for {truncated_filename}")

    logger.info(f"Finished processing document: {truncated_filename}")
    return len(processed_chunks)  # Return the number of processed chunks

def combine_summaries(summaries):
    combined_text = "\n\n".join(summaries)
    prompt = "The following are summaries of different sections of a document. Please provide a concise overall summary that captures the main points of the entire document:"
    combined_summary_result = rewrite_text_with_openai(combined_text, is_summary=True, custom_prompt=prompt)
    return combined_summary_result['summary'][0] if combined_summary_result and 'summary' in combined_summary_result else "Failed to generate combined summary."

def combine_keywords(keyword_lists):
    all_keywords = list(set([keyword for sublist in keyword_lists for keyword in sublist]))
    prompt = "The following is a list of keywords from different sections of a document. Please refine and limit this to the 10 most relevant and representative terms for the entire document:"
    combined_keywords_result = rewrite_text_with_openai(", ".join(all_keywords), is_keywords=True, custom_prompt=prompt)
    return combined_keywords_result['keywords'] if combined_keywords_result and 'keywords' in combined_keywords_result else all_keywords[:10]  # Limit to 10 if API call fails