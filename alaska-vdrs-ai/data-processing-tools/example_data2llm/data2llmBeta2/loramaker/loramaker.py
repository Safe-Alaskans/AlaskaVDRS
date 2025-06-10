# ********************************************************************************
# * NOTE: This script processes JSON files containing knowledgebase information  *
# * and generates question-answer pairs using the OpenAI API.                    *
# * The question and answer pairs are designed to be educational and informative,*
# * covering a variety of aspects of the topic.                                  *
# * The results will be used for supervised LLM fine-tuning.                     *
# ********************************************************************************
# * NOTE: The prompt may be customized to specialize in different topics. It is  *
# * generic by default.                                                          *
# ********************************************************************************

import concurrent.futures
import os
import json
import logging
import time
from typing import List, Tuple, Optional
from tqdm import tqdm
import datetime
import tiktoken
import sys
from openai import OpenAI, RateLimitError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Replace the hardcoded API key with an environment variable
API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client
client = OpenAI(api_key=API_KEY)

class PairCountMismatchError(Exception):
    pass

def make_api_request(messages, model, temperature, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature
            )
            return response
        except RateLimitError:
            retry_after = 20  # Default to 20 seconds if no Retry-After header
            logging.warning(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
        except Exception as e:
            logging.error(f"API request failed: {str(e)}")
            return None
    
    logging.error("Max retries reached. Could not complete the API request.")
    return None

def configure_logging(debug_mode):
    if debug_mode:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def estimate_tokens(text: str) -> int:
    encoding = tiktoken.encoding_for_model("gpt-4")
    return len(encoding.encode(text))

def get_total_input_tokens(directory: str) -> int:
    total_tokens = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_content = json.load(f)
                json_str = json.dumps(json_content)
                total_tokens += estimate_tokens(json_str)
    return total_tokens

def process_single_file(file, directory, model, temperature, debug_mode, expected_pairs):
    # Add a small delay before processing each file
    time.sleep(1)  # 1 second delay, adjust as needed
    
    file_path = os.path.join(directory, file)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        json_content = json.load(f)

    json_str = json.dumps(json_content)

    messages = [
        {"role": "system", "content": (
            "You are tasked with generating meticulously detailed question-answer pairs based on input text. "
            "Ensure that each question-answer pair provides valuable insights for someone learning about the topic. "
            "Question-answer pairs should contain enough information for a patient teacher to instruct an enthusiastic new student. "
            "Format the output as a JSON array of objects labeled instruction: <generated question> and output: <generated answer>. "
        )},
        {"role": "user", "content": (
            f"Text: <input-text>\n\n{json_str}\n\n</input-text> Generate {expected_pairs} detailed question-and-answer pairs based on the input text. "
            "Each question must include enough context for the answer to be understood without any additional information. "
            "Focus on expanding and varying the complexity of questions to include both straightforward and in-depth ones. "
            "Include different question types, such as factual, open-ended, analytical, hypothetical, and problem-solving. "
            "While the wording of the answers may differ from the input text, ensure that the meaning and information remain the same. "
            "Reverse the order of phrases or sentences in some answers to vary the responses. "
            "Ensure that each answer not only addresses the question directly but also discusses the broader implications and underlying principles."
            "Focus only on the content from the input text, excluding any metadata. "
        )}
    ]

    response = make_api_request(messages, model, temperature)

    if response is None:
        logging.error(f"Failed to get a valid response from the API for file {file}.")
        return None, 0

    if debug_mode:
        print(f"\nRaw API response for file {file}:")
        print(response)
        print("\n" + "="*50 + "\n")

    try:
        qa_content = response.choices[0].message.content

        json_start = qa_content.find('[')
        json_end = qa_content.rfind(']') + 1
        if json_start != -1 and json_end != -1:
            qa_content = qa_content[json_start:json_end]

        qa_pairs = json.loads(qa_content)
        num_pairs = len(qa_pairs)
        logging.info(f"Generated {num_pairs} question-answer pairs for file {file}")

        tokens_used = response.usage.total_tokens
        logging.info(f"Tokens used for file {file}: {tokens_used}")

        if num_pairs != expected_pairs:
            raise PairCountMismatchError(f"Expected {expected_pairs} pairs, but generated {num_pairs} pairs for file {file}")

        return qa_pairs, tokens_used

    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        logging.error(f"Failed to process API response for file {file}. Error: {str(e)}")
        logging.debug(f"Problematic content: {response}")
        return None, 0

def create_output_directory(input_directory, user_suffix):
    # Get the base name of the input directory
    base_name = os.path.basename(input_directory)
    
    # Truncate the base name to 10 characters
    truncated_name = base_name[:10]
    
    # Get the current date in MMDDYY format
    current_date = datetime.datetime.now().strftime("%m%d%y")
    
    # Create the new directory name
    new_dir_name = f"{truncated_name}_QA_Pairs_{current_date}"
    
    # Add user suffix if provided
    if user_suffix:
        new_dir_name += f"-{user_suffix}"
    
    # Create the full path for the new directory
    new_dir_path = os.path.join(os.path.dirname(input_directory), new_dir_name)
    
    # Create the directory if it doesn't exist
    os.makedirs(new_dir_path, exist_ok=True)
    
    return new_dir_path

def save_qa_pairs(output_directory: str, qa_pairs: List[dict], file_counter: int) -> None:
    output_filename = os.path.join(output_directory, f"QA_Pairs_{file_counter:03d}.json")
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
    logging.info(f"Saved {len(qa_pairs)} Q&A pairs to {output_filename}")

def process_json_files(directory: str, max_workers: int, model: str, temperature: float, debug_mode: bool, expected_pairs: int, output_directory: str) -> None:
    json_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    
    all_qa_pairs = []
    total_tokens_used = 0
    pairs_per_file = 500
    file_counter = 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(process_single_file, file, os.path.dirname(file), model, temperature, debug_mode, expected_pairs): file for file in json_files}
        
        for future in tqdm(concurrent.futures.as_completed(future_to_file), total=len(json_files), desc="Processing files"):
            file = future_to_file[future]
            try:
                qa_pair, tokens = future.result()
                if qa_pair:
                    all_qa_pairs.extend(qa_pair)
                    total_tokens_used += tokens
                    
                    if len(all_qa_pairs) >= pairs_per_file:
                        save_qa_pairs(output_directory, all_qa_pairs, file_counter)
                        file_counter += 1
                        all_qa_pairs = []
            except PairCountMismatchError as e:
                logging.warning(str(e))
                user_choice = input("Mismatch detected. Do you want to (c)ontinue, (s)ave and exit, or (e)xit without saving? ").lower()
                if user_choice == 's':
                    save_qa_pairs(output_directory, all_qa_pairs, file_counter)
                    sys.exit("Saving and exiting as requested.")
                elif user_choice == 'e':
                    sys.exit("Exiting without saving as requested.")
                # If 'c', we just continue processing
            except Exception as exc:
                logging.error(f'{file} generated an exception: {exc}')

    # Save any remaining pairs
    if all_qa_pairs:
        save_qa_pairs(output_directory, all_qa_pairs, file_counter)

    logging.info(f"Total tokens used across all files: {total_tokens_used}")
    logging.info(f"Output files saved in: {output_directory}")

if __name__ == "__main__":
    directory = input("Please enter the directory path of your JSON knowledgebase (subdirectories WILL be included): ")
    
    default_model = "gpt-4o-2024-08-06"
    print(f"Enter the chat model to use (default is {default_model}): ", end='')
    model = input() or default_model
    
    default_temperature = 0.5
    print(f"Enter the temperature to use (default is {default_temperature}): ", end='')
    temperature_input = input() or default_temperature
    temperature = float(temperature_input)  # Convert to float here

    default_expected_pairs = 20
    print(f"Enter the number of expected question-answer pairs (default is {default_expected_pairs}): ", end='')
    expected_pairs_input = input()
    EXPECTED_PAIRS = int(expected_pairs_input) if expected_pairs_input else default_expected_pairs

    debug_mode = input("Run in debug mode? (y/n): ").lower() == 'y'
    
    print("Output pairs will be placed in a new folder in the root of your input directory.")
    user_suffix = input("Enter any valid text string to add to the name of the new folder (or press Enter for none): ")
    
    # Configure logging based on debug mode
    configure_logging(debug_mode)

    total_input_tokens = get_total_input_tokens(directory)
    print(f"Estimated total input tokens: {total_input_tokens}")
    
    confirmation = input("Do you want to proceed with processing? (y/n): ").lower()
    if confirmation != 'y':
        print("Operation cancelled by user.")
        exit()
    
    # Create the output directory
    output_directory = create_output_directory(directory, user_suffix)
    print(f"Output will be saved in: {output_directory}")
    
    process_json_files(directory, max_workers=2, model=model, temperature=temperature, debug_mode=debug_mode, expected_pairs=EXPECTED_PAIRS, output_directory=output_directory)