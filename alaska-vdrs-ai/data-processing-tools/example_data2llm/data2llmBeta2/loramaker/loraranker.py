import os
from dotenv import load_dotenv
import json
from pathlib import Path
from openai import OpenAI
import logging
from collections import deque
import jsonlines

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

# Global variables for default settings
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_SYSTEM_PROMPT = """Your role is to help inventors, innovators, and researchers obtain a Phase I Small Business Innovation Research (SBIR) grant. Their projects may or may not be incorporated into a small business yet. They may be starting from scratch and need to understand everything about the SBIR process in order to gain comprehensive knowledge. With your role in mind, rate the relevance rank of the following question-answer pairs on a scale of 0-100. 0 = not relevant to someone new learning about the SBIR process, 100 = very relevant to someone new learning about the SBIR process. Respond with your rank only."""
DEFAULT_TEMPERATURE = 0.2

def get_directory():
    while True:
        directory = input("Enter the directory path containing JSON files (subdirectories WILL NOT be included): ")
        if os.path.isdir(directory):
            return directory
        print("Invalid directory. Please try again.")

def count_qa_pairs(directory):
    count = 0
    for file in Path(directory).glob('*.json'):
        with open(file, 'r') as f:
            data = json.load(f)
            count += len(data)
    return count

def get_user_confirmation(prompt, default):
    user_input = input(f"{prompt} (default: {default}): ").strip()
    return user_input if user_input else default

def rank_qa_pair(client, qa_pair):
    question = qa_pair.get('instruction', '')
    answer = qa_pair.get('output', '')

    prompt = f"""
    Question: {question}
    Answer: {answer}
    """
    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=DEFAULT_TEMPERATURE
        )
        rank = int(response.choices[0].message.content.strip())
        logging.info(f"Successfully ranked question. Rank: {rank}")
        return rank
    except Exception as e:
        logging.error(f"Error ranking question: {str(e)}")
        return 0  # or some default value

def process_files(directory):
    client = OpenAI()
    total_ranked = 0
    last_five_ranks = deque(maxlen=5)
    
    for file in Path(directory).glob('*.json'):
        logging.info(f"Processing file: {file}")
        
        try:
            with open(file, 'r') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                logging.warning(f"File {file} does not contain a JSON array. Skipping.")
                continue
            
            for i, item in enumerate(data):
                if not isinstance(item, dict):
                    logging.warning(f"Skipping invalid item at index {i} in {file}: not a dictionary")
                    continue

                if 'instruction' not in item or 'output' not in item:
                    logging.warning(f"Skipping item without valid question-answer pair at index {i} in {file}")
                    continue

                qa_pair = {
                    'instruction': item['instruction'],
                    'output': item['output']
                }

                rank = rank_qa_pair(client, qa_pair)
                
                # Add the rank to the existing item
                item['rank'] = rank
                
                total_ranked += 1
                
                # Check for repeated ranks
                last_five_ranks.append(rank)
                if len(last_five_ranks) == 5 and len(set(last_five_ranks)) == 1:
                    logging.warning(f"Warning: Last 5 ranks are identical ({rank}). Possible error in ranking.")
                
                if total_ranked % 10 == 0:  # Log progress every 10 questions
                    logging.info(f"Ranked {total_ranked} questions in total. Current file: {file.name}")

            # Write the updated data back to a new file
            output_file = file.parent / f"ranked_{file.name}"
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=4)
            
            logging.info(f"Processed and saved: {output_file}")

        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON in {file}: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error processing file {file}: {str(e)}")

    logging.info(f"Ranking complete. Total questions ranked: {total_ranked}")

def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set the OPENAI_API_KEY in your .env file or environment variables.")
        return

    directory = get_directory()
    pair_count = count_qa_pairs(directory)
    print(f"Found {pair_count} question-answer pairs in the directory.")

    proceed = input("Do you want to proceed with ranking? (y/n): ").lower()
    if proceed != 'y':
        print("Operation cancelled.")
        return

    # Confirm model
    global DEFAULT_MODEL
    DEFAULT_MODEL = get_user_confirmation("Enter desired chat model", DEFAULT_MODEL)

    # Confirm system prompt
    global DEFAULT_SYSTEM_PROMPT
    DEFAULT_SYSTEM_PROMPT = get_user_confirmation("Enter the system prompt appropriate for the context of your task", DEFAULT_SYSTEM_PROMPT)

    # Confirm temperature
    global DEFAULT_TEMPERATURE
    DEFAULT_TEMPERATURE = float(get_user_confirmation("Enter the desiredmodel temperature", DEFAULT_TEMPERATURE))

    print("\nConfirmed settings:")
    print(f"Model: {DEFAULT_MODEL}")
    print(f"System Prompt: {DEFAULT_SYSTEM_PROMPT}")
    print(f"Temperature: {DEFAULT_TEMPERATURE}")

    final_confirm = input("\nDo you want to proceed with these settings? (y/n): ").lower()
    if final_confirm != 'y':
        print("Operation cancelled.")
        return

    process_files(directory)
    print("Ranking complete.")

if __name__ == "__main__":
    main()
