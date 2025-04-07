import logging
from collections.abc import Generator
from typing import Any

from core.workflow_generator.prompt.requirement_understanding_prompts import PROMPT_TEMPLATE, SYSTEM_PROMPT
from core.workflow_generator.utils.output_parser import WorkflowOutputParser
from core.workflow_generator.utils.sse_response import stream_generator

from .base_agent import BaseWorkflowAgent

logger = logging.getLogger(__name__)


class RequirementUnderstandingAgent(BaseWorkflowAgent):
    """
    Agent for understanding user requirements and generating standardized requirement inputs.

    This agent takes raw user input, understands the intent, and reformulates it into
    a standardized format for further processing. It interacts with the user to clarify
    requirements until a complete understanding is achieved.
    
    This implementation is stateless - all state is returned in the response and can be
    managed externally via database persistence.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove self.requirement as we're making this stateless
        self.model_parameters = {"temperature": 0.3, "max_tokens": 4096}
        self.output_parser = WorkflowOutputParser(
            result_type=dict,
            default_schema=self.default_schema
        )

    @property
    def default_schema(self) -> dict[str, Any]:
        return {
            "complete": False,
            "requirement": {
                "intent": "",
                "functionalities": [],
                "components": [],
                "constraints": [],
            },
            "clarification_questions": []
        }

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT

    @property
    def prompt_template(self) -> str:
        return PROMPT_TEMPLATE

    def run(self, input_data: str) -> Generator[str, None, None]:
        prompt = self.prompt_template.format(
            input_requirement=input_data)
        messages = self._construct_messages(prompt)

        response_chunks = self.model_instance.invoke_llm(
            prompt_messages=messages,
            model_parameters=self.model_parameters,
            tools=[],
            stop=[],
            stream=True,
            user=self.user_id,
            callbacks=[],
        )

        def _post_process(content: str) -> dict[str, Any]:
            return self._process_response(input_data, content)
        return stream_generator(response_chunks, _post_process)

    def _process_response(self, input_data: str, response_content: str) -> dict[str, Any]:
        # Apply output parser to get structured requirement data
        try:
            parsed_output = self.output_parser.parse(response_content)
            # Rather than updating internal state, just return the parsed output
            # Any state management will be handled by the caller
            return parsed_output
        except Exception as e:
            logger.exception("Parse response content failed")
            # Return empty dict
            return {}
