import logging
import time
from openai import OpenAI
import re
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv("OPENAI_API_KEY")

# Set up your OpenAI client
client = OpenAI(api_key=API_KEY)

# Global variable to track total tokens used
total_tokens_used = 0

def clean_content(content):
    # Remove leading/trailing whitespace
    content = content.strip()
    # Remove leading symbols like », •, etc., but preserve them if they're in the middle of the content
    content = re.sub(r'^[»•-]\s*', '', content)
    # Replace multiple spaces with a single space, but preserve line breaks
    content = re.sub(r' +', ' ', content)
    return content

def rewrite_text_with_openai(chunk, is_summary=False, is_keywords=False, custom_prompt=None):
    global total_tokens_used
    retry_attempts = 5
    for attempt in range(retry_attempts):
        try:
            if custom_prompt:
                prompt = custom_prompt
            elif is_summary:
                prompt = "Provide a concise summary of a document based on these summaries of its sections:"
            elif is_keywords:
                prompt = "Refine and limit the following keywords to the 10 most relevant and representative terms:"
            else:
                prompt = "Process the following text extracted from a document, adding appropriate structural markup while preserving information:"

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": (
                        "You are an expert in text processing and formatting for LLM training data. "
                        "Your task is to review and enhance the following text extracted from a document. "
                        "It is crucial to preserve ALL information from the original input. "
                        "Correct any formatting issues to improve readability while retaining exact words and meaning. "
                        "Identify and mark different sections using the following JSON-friendly markup: "
                        "{{TITLE}}, {{SUBTITLE}}, {{CHAPTER}}, {{SECTION}}, {{SUBSECTION}}, {{PARAGRAPH}}, {{LIST_ITEM}}, {{QUOTE}}, {{TABLE}}, {{FIGURE}}. "
                        "Place the markup at the beginning of the line, followed by a newline, then the content. "
                        "For example:\n{{TITLE}}\nThis is the title content"
                        "Each marked section should start on a new line. "
                        "For tables, lists, and other structured content, preserve the original formatting, including symbols and line breaks. "
                        "If content doesn't fit into any predefined category, include it without a category marker. "
                        "Remove only clearly irrelevant content like page numbers or headers/footers. "
                        "Generate a concise summary of the content (max 3 sentences) that captures the main points without being overly detailed. "
                        "Provide a list of relevant, topic-specific keywords (max 10), focusing on core concepts and important terms. "
                        "The summary should be clearly marked with the tags {{SUMMARY}} and {{END_SUMMARY}}, and the keywords with {{KEYWORDS}} and {{END_KEYWORDS}}. "
                        "Exclude URLs, external links, or any non-keyword material in the list of keywords. "
                        "The goal is to create high-quality, structured text data for LoRA-based LLM training while preserving all original information. "
                        "Do not include any code blocks, backticks, or markdown syntax in the output."
                    )},
                    {"role": "user", "content": f"{prompt}\n\n{chunk}"}
                ],
                max_tokens=10000,
                temperature=0.2,
            )
            processed_text = response.choices[0].message.content

            # Update total tokens used
            if hasattr(response, 'usage') and hasattr(response.usage, 'total_tokens'):
                total_tokens_used += response.usage.total_tokens
                logging.info(f"Tokens used for this request: {response.usage.total_tokens}")
                logging.info(f"Total tokens used so far: {total_tokens_used}")
                
                if response.usage.total_tokens > 15000:
                    logging.warning("High token usage detected.")
            else:
                logging.warning("Token usage information not available.")

            # Extract the summary and keywords
            summary_match = re.search(r'\{\{SUMMARY\}\}\s*(.*?)\s*\{\{END_SUMMARY\}\}', processed_text, re.DOTALL)
            keywords_match = re.search(r'\{\{KEYWORDS\}\}\s*(.*?)\s*\{\{END_KEYWORDS\}\}', processed_text, re.DOTALL)

            summary = [summary_match.group(1).strip()] if summary_match else ["No summary generated."]
            keywords = keywords_match.group(1).strip().split(',') if keywords_match else []

            # Clean the processed text by removing the summary and keywords sections
            processed_text = re.sub(r'\{\{SUMMARY\}\}.*?\{\{END_SUMMARY\}\}', '', processed_text, flags=re.DOTALL)
            processed_text = re.sub(r'\{\{KEYWORDS\}\}.*?\{\{END_KEYWORDS\}\}', '', processed_text, flags=re.DOTALL)

            structured_content = []
            current_type = None
            current_content = []
            in_table = False

            for line in processed_text.split('\n'):
                line = line.strip()
                if line.startswith("{{"):
                    if current_type:
                        content = "\n".join(current_content).strip()
                        if current_type.lower() != "table":
                            content = clean_content(content)
                        structured_content.append({"type": current_type.lower(), "content": content})
                        current_content = []
                    current_type = line.strip("{{ }}").lower()
                    in_table = (current_type == "table")
                else:
                    if in_table:
                        current_content.append(line)  # Preserve original table formatting
                    elif current_type:
                        current_content.append(clean_content(line))
                    else:
                        # If we encounter content without a type, create a new "unclassified" type
                        structured_content.append({"type": "unclassified", "content": clean_content(line)})

            # Add the last section
            if current_type:
                content = "\n".join(current_content).strip()
                if current_type.lower() != "table":
                    content = clean_content(content)
                structured_content.append({"type": current_type.lower(), "content": content})

            # Return processed text, summary, and keywords for this chunk
            return {
                "summary": summary,
                "keywords": [kw.strip() for kw in keywords if kw.strip()],
                "structured_content": structured_content
            }

        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retry_attempts - 1:
                wait_time = 2 ** attempt
                logging.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logging.error("Max retry attempts reached. Failed to process text with OpenAI API.")
                return None

def get_total_tokens_used():
    global total_tokens_used
    return total_tokens_used