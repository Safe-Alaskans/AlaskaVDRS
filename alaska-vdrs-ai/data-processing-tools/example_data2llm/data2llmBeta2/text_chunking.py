import tiktoken
import functools
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)

# Use functools.lru_cache to cache the tokenizer
@functools.lru_cache(maxsize=None)
def get_tokenizer():
    return tiktoken.encoding_for_model("gpt-4")

def count_tokens(text):
    """Count the number of tokens in a given text."""
    encoding = get_tokenizer()
    return len(encoding.encode(text))

def chunk_text_by_tokens(text, max_tokens=5000, min_tokens=4000):
    """Splits text into chunks of up to max_tokens, ensuring chunks are not too small, using paragraphs as the base unit."""
    encoding = get_tokenizer()
    paragraphs = text.split('\n\n')  # Split text into paragraphs
    chunks = []
    current_chunk = []
    current_tokens = 0
    warned = False

    for paragraph in paragraphs:
        paragraph_tokens = encoding.encode(paragraph)
        paragraph_token_count = len(paragraph_tokens)

        if current_tokens + paragraph_token_count <= max_tokens:
            # If adding this paragraph doesn't exceed max_tokens, add it to the current chunk
            current_chunk.extend(paragraph_tokens)
            current_tokens += paragraph_token_count
        else:
            # If adding this paragraph would exceed max_tokens, end the current chunk
            if current_chunk:
                chunks.append(encoding.decode(current_chunk))
                current_chunk = paragraph_tokens
                current_tokens = paragraph_token_count
            else:
                # If the current chunk is empty, this paragraph exceeds max_tokens on its own
                # In this case, we'll split the paragraph
                for i in range(0, len(paragraph_tokens), max_tokens):
                    chunk = paragraph_tokens[i:i + max_tokens]
                    chunks.append(encoding.decode(chunk))
                current_chunk = []
                current_tokens = 0

    # Add any remaining content as the last chunk
    if current_chunk:
        chunks.append(encoding.decode(current_chunk))

    # Log warnings for small chunks only once
    for i, chunk in enumerate(chunks):
        chunk_tokens = count_tokens(chunk)
        if chunk_tokens < min_tokens and not warned:
            logger.warning(f"Chunk {i+1} has only {chunk_tokens} tokens, which is below the minimum of {min_tokens}.")
            warned = True
        logger.debug(f"Chunk {i+1} has {chunk_tokens} tokens.")

    soft_chunked = len(chunks) > 1
    
    return chunks, soft_chunked