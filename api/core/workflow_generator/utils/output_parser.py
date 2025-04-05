"""
Output parser utilities for workflow generator agents.
Provides generic JSON parsing capabilities with streaming support.
"""

import json
import re
from collections.abc import Generator
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic, Callable

from core.model_runtime.entities.llm_entities import LLMResultChunk, LLMResult

T = TypeVar('T')


class WorkflowOutputParser(Generic[T]):
    """
    Generic output parser for workflow generator agents.
    Supports both streaming and non-streaming LLM outputs.
    """

    def __init__(
        self,
        result_type: type,
        result_factory: Optional[Callable[[Dict[str, Any]], T]] = None,
        default_schema: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the output parser.

        Args:
            result_type: The type of result to return
            result_factory: Optional factory function to convert parsed JSON to result type
            default_schema: Optional default schema to use if JSON parsing fails
        """
        self.result_type = result_type
        self.result_factory = result_factory or (lambda x: result_type(**x))
        self.default_schema = default_schema or {}

    def parse_response(self, response: Union[str, LLMResult]) -> T:
        """
        Parse a complete LLM response (non-streaming).

        Args:
            response: The LLM response to parse

        Returns:
            Parsed result of type T
        """
        if isinstance(response, LLMResult):
            content = response.message.content
        else:
            content = response

        json_data = self._extract_json_from_response(content)
        return self.result_factory(json_data)

    def handle_stream_output(
        self,
        llm_response: Generator[LLMResultChunk, None, None],
        usage_dict: dict
    ) -> Generator[Union[str, Dict[str, Any]], None, None]:
        """
        Handle streaming LLM response and extract JSON data.

        Args:
            llm_response: Generator of LLM result chunks
            usage_dict: Dictionary to store usage information

        Returns:
            Generator yielding either text chunks or parsed JSON data
        """
        def extract_json_from_code_block(code_block) -> List[Union[List, Dict]]:
            """Extract JSON from code blocks in the response."""
            blocks = re.findall(
                r"```[json]*\s*([\[{].*[]}])\s*```", code_block, re.DOTALL | re.IGNORECASE)
            if not blocks:
                return []
            try:
                json_blocks = []
                for block in blocks:
                    json_text = re.sub(
                        r"^[a-zA-Z]+\n", "", block.strip(), flags=re.MULTILINE)
                    json_blocks.append(json.loads(json_text, strict=False))
                return json_blocks
            except:
                return []

        # Initialize state variables for parsing
        code_block_cache = ""
        code_block_delimiter_count = 0
        in_code_block = False
        json_cache = ""
        json_quote_count = 0
        in_json = False
        got_json = False

        for response in llm_response:
            if response.delta.usage:
                usage_dict["usage"] = response.delta.usage
            response_content = response.delta.message.content
            if not isinstance(response_content, str):
                continue

            # Process the response content character by character
            index = 0
            while index < len(response_content):
                steps = 1
                delta = response_content[index: index + steps]

                # Handle code block delimiters
                if not in_json and delta == "`":
                    last_character = delta
                    code_block_cache += delta
                    code_block_delimiter_count += 1
                else:
                    if not in_code_block:
                        if code_block_delimiter_count > 0:
                            last_character = delta
                            yield code_block_cache
                        code_block_cache = ""
                    else:
                        last_character = delta
                        code_block_cache += delta
                    code_block_delimiter_count = 0

                # Handle code block completion (triple backticks)
                if code_block_delimiter_count == 3:
                    if in_code_block:
                        last_character = delta
                        json_blocks = extract_json_from_code_block(
                            code_block_cache)
                        if json_blocks:
                            for json_block in json_blocks:
                                yield json_block
                            code_block_cache = ""
                        else:
                            index += steps
                            continue

                    in_code_block = not in_code_block
                    code_block_delimiter_count = 0

                # Handle JSON outside code blocks
                if not in_code_block:
                    # Start of JSON object
                    if delta == "{":
                        json_quote_count += 1
                        in_json = True
                        json_cache += delta
                    # End of JSON object
                    elif delta == "}":
                        json_cache += delta
                        if json_quote_count > 0:
                            json_quote_count -= 1
                            if json_quote_count == 0:
                                in_json = False
                                got_json = True
                                index += steps
                                continue
                    # Inside JSON object
                    else:
                        if in_json:
                            json_cache += delta

                    # Process completed JSON
                    if got_json:
                        got_json = False
                        try:
                            json_obj = json.loads(json_cache)
                            yield json_obj
                        except json.JSONDecodeError:
                            yield json_cache
                        json_cache = ""
                        json_quote_count = 0
                        in_json = False

                # Yield regular text outside code blocks and JSON
                if not in_code_block and not in_json:
                    yield delta.replace("`", "")

                index += steps

        # Handle any remaining content
        if code_block_cache:
            yield code_block_cache

        if json_cache:
            try:
                json_obj = json.loads(json_cache)
                yield json_obj
            except json.JSONDecodeError:
                yield json_cache

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response text.

        Args:
            response: The raw response text from LLM

        Returns:
            Extracted JSON as dictionary
        """
        # Try to find JSON in code blocks
        json_blocks = self._extract_json_from_code_block(response)
        if json_blocks and len(json_blocks) > 0:
            # Return the first JSON block found
            if isinstance(json_blocks[0], dict):
                return json_blocks[0]
            elif isinstance(json_blocks[0], list) and len(json_blocks[0]) > 0 and isinstance(json_blocks[0][0], dict):
                return json_blocks[0][0]

        # Try to find JSON without code blocks
        json_match = re.search(r'{[\s\S]*?}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # If no JSON found and default schema provided, use fallback extraction
        if self.default_schema:
            return self._extract_structured_information(response, self.default_schema)

        # Return empty dict if all extraction methods fail
        return {}

    def _extract_json_from_code_block(self, code_block: str) -> List[Union[List, Dict]]:
        """
        Extract JSON from code blocks in the response.

        Args:
            code_block: The code block to extract JSON from

        Returns:
            List of extracted JSON objects
        """
        blocks = re.findall(
            r"```[json]*\s*([\[{].*[]}])\s*```", code_block, re.DOTALL | re.IGNORECASE)
        if not blocks:
            return []
        try:
            json_blocks = []
            for block in blocks:
                json_text = re.sub(r"^[a-zA-Z]+\n", "",
                                   block.strip(), flags=re.MULTILINE)
                json_blocks.append(json.loads(json_text, strict=False))
            return json_blocks
        except:
            return []

    def _extract_structured_information(self, response: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured information from text based on a schema.

        Args:
            response: The raw response text
            schema: The schema to use for extraction

        Returns:
            Extracted information as dictionary
        """
        # Create a result dictionary with the same structure as the schema
        result = {}
        for key, value in schema.items():
            if isinstance(value, list):
                result[key] = []
            else:
                result[key] = value

        # Simple extraction based on section headers
        sections = response.split("\n\n")
        for section in sections:
            for key in schema.keys():
                # Create a pattern that matches the key name with some flexibility
                pattern = f"{key}\\s*:(.+?)(?=\\n\\n|$)"
                match = re.search(pattern, section, re.IGNORECASE | re.DOTALL)
                if match:
                    content = match.group(1).strip()
                    if isinstance(schema[key], list):
                        # Extract list items
                        items = re.findall(
                            r"[-*•]\s*(.+?)(?=\n[-*•]|\n\n|$)", content, re.DOTALL)
                        if items:
                            result[key] = [item.strip()
                                           for item in items if item.strip()]
                        else:
                            # If no bullet points, try splitting by newlines
                            items = content.split("\n")
                            result[key] = [item.strip()
                                           for item in items if item.strip()]
                    else:
                        result[key] = content

        return result
