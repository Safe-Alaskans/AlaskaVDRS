import json
import os
import logging
from text_chunking import count_tokens

# Configure logging for this module
logger = logging.getLogger(__name__)

def save_as_json(metadata_dict, output_path):
    """Saves the processed text and metadata as a JSON file."""
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(metadata_dict, file, ensure_ascii=False, indent=2)
        logger.info(f"Processed text and metadata saved as JSON at {output_path}.")
    except Exception as e:
        logger.error(f"Failed to save JSON file: {e}")

def save_chunked_json(processed_chunks, output_folder, truncated_filename):
    """Saves each processed chunk into its own JSON file."""
    for i, chunk_metadata in enumerate(processed_chunks, 1):
        chunk_filename = f"{truncated_filename}_chunk_{i:03d}.json"  # Use 3-digit padding for chunk numbers
        chunk_path = os.path.join(output_folder, chunk_filename)

        try:
            with open(chunk_path, 'w', encoding='utf-8') as file:
                json.dump(chunk_metadata, file, ensure_ascii=False, indent=2)
            logger.info(f"Chunk {i} saved as {chunk_filename}")
        except Exception as e:
            logger.error(f"Failed to save chunk {i}: {e}")

def merge_small_json_files(output_folder, truncated_filename, is_soft_chunked, chunked_output, max_tokens=5000, min_tokens=2500, progress_callback=None):
    """Merges JSON files that are 2500 tokens or less, up to a maximum of 5000 tokens, only if soft chunking was used and chunked output was not requested."""
    logger.debug(f"merge_small_json_files called for {truncated_filename}. is_soft_chunked: {is_soft_chunked}, chunked_output: {chunked_output}")
    if not is_soft_chunked or chunked_output:
        logger.info(f"Skipping merge_small_json_files for {truncated_filename} as soft chunking was not used or chunked output was requested.")
        return

    json_files = [f for f in os.listdir(output_folder) if f.startswith(truncated_filename) and f.endswith('.json')]
    json_files.sort()  # Ensure files are processed in order

    total_files = len(json_files)
    processed_files = 0

    i = 0
    while i < len(json_files) - 1:
        file1 = json_files[i]
        file2 = json_files[i + 1]
        
        with open(os.path.join(output_folder, file1), 'r', encoding='utf-8') as f1, \
             open(os.path.join(output_folder, file2), 'r', encoding='utf-8') as f2:
            data1 = json.load(f1)
            data2 = json.load(f2)

        content1 = json.dumps(data1["structured_content"])
        content2 = json.dumps(data2["structured_content"])

        tokens1 = count_tokens(content1)
        tokens2 = count_tokens(content2)

        if tokens1 <= min_tokens and tokens2 <= min_tokens and (tokens1 + tokens2) <= max_tokens:
            # Merge the files
            merged_data = {
                "summary": [data1["summary"][0] + " " + data2["summary"][0]],
                "keywords": list(set(data1["keywords"] + data2["keywords"])),
                "structured_content": data1["structured_content"] + data2["structured_content"]
            }

            merged_filename = f"{truncated_filename}_merged_{i}.json"
            with open(os.path.join(output_folder, merged_filename), 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=2)

            # Remove the original files
            os.remove(os.path.join(output_folder, file1))
            os.remove(os.path.join(output_folder, file2))

            # Update the list of files
            json_files[i] = merged_filename
            json_files.pop(i + 1)

            logger.info(f"Merged {file1} and {file2} into {merged_filename}")
            if progress_callback:
                processed_files += 1
                progress_callback(processed_files, total_files)
        else:
            i += 1

    # Rename the files to ensure consistent naming
    for i, filename in enumerate(json_files):
        new_filename = f"{truncated_filename}_chunk_{i+1:03d}.json"  # Use 3-digit padding
        old_path = os.path.join(output_folder, filename)
        new_path = os.path.join(output_folder, new_filename)
        
        if old_path != new_path:
            if os.path.exists(new_path):
                # If the new filename already exists, append a unique identifier
                base, ext = os.path.splitext(new_filename)
                j = 1
                while os.path.exists(os.path.join(output_folder, f"{base}_{j}{ext}")):
                    j += 1
                new_filename = f"{base}_{j}{ext}"
                new_path = os.path.join(output_folder, new_filename)
            
            os.rename(old_path, new_path)
            logger.info(f"Renamed {filename} to {new_filename}")

def validate_content(content):
    """Validates the content of the JSON file."""
    required_keys = ["summary", "keywords", "structured_content"]
    for key in required_keys:
        if key not in content:
            return False, f"Missing required key: {key}"
    
    if not isinstance(content["summary"], list):
        return False, "Summary must be a list"
    if len(content["summary"]) != 1 or not isinstance(content["summary"][0], str):
        return False, "Summary must be a list containing a single string"
    
    if not isinstance(content["keywords"], list):
        return False, "Keywords must be a list"
    
    if not isinstance(content["structured_content"], list):
        return False, "Structured content must be a list"
    
    for item in content["structured_content"]:
        if not isinstance(item, dict):
            return False, "Each item in structured content must be a dictionary"
        if "type" not in item or "content" not in item:
            return False, "Each item in structured content must have 'type' and 'content' keys"
        if not isinstance(item["type"], str) or not isinstance(item["content"], str):
            return False, "Both 'type' and 'content' in structured content items must be strings"
    
    return True, "Content is valid"

# Add this function to validate JSON files after processing
def validate_json_files(output_folder):
    """Validates all JSON files in the output folder."""
    json_files = [f for f in os.listdir(output_folder) if f.endswith('.json')]
    for file in json_files:
        file_path = os.path.join(output_folder, file)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        is_valid, message = validate_content(content)
        if not is_valid:
            logger.error(f"Validation failed for {file}: {message}")
        else:
            logger.info(f"Validation passed for {file}")