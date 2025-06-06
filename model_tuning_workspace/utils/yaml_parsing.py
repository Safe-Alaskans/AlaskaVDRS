from typing import Dict, Any
import yaml
from yaml.error import YAMLError
import re

def parse_yaml_response(response: str) -> Dict[str, Any]:
    """
    Extract and parse YAML content from a string that may contain other text and markdown.
    Looks for YAML content either:
    1. Between ```yaml and ``` markers
    2. Between ```yml and ``` markers
    3. If no markers found, tries to parse the entire string as YAML

    Args:
        response (str): String that may contain YAML content with surrounding text

    Returns:
        Dict[str, Any]: Parsed YAML as a dictionary

    Raises:
        YAMLError: If the YAML is malformed
        ValueError: If no valid YAML content found or parsed result is not a dictionary
    """
    yaml_patterns = [
        r"```\s*yaml\s*\n(.*?)\n\s*```",
        r"```\s*yml\s*\n(.*?)\n\s*```",
    ]

    yaml_content = None
    for pattern in yaml_patterns:
        match = re.search(pattern, response, re.DOTALL)
        if match:
            yaml_content = match.group(1)
            break

    # If no markdown code blocks found, try to parse the entire string
    if yaml_content is None:
        yaml_content = response

    try:
        result = yaml.safe_load(yaml_content)
        if result is None:
            raise ValueError("No YAML content found")

        return result

    except YAMLError as e:
        raise YAMLError(f"Failed to parse YAML: {str(e)}")