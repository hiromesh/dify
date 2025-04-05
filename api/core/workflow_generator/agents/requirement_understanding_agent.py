import logging
from typing import Any, Dict, Generator

from .base_agent import BaseWorkflowAgent
from core.model_runtime.entities.message_entities import (
    UserPromptMessage,
    AssistantPromptMessage
)
from core.workflow_generator.prompt.requirement_understanding_prompts import (
    SYSTEM_PROMPT,
    PROMPT_TEMPLATE
)
from core.workflow_generator.utils.output_parser import WorkflowOutputParser
from core.workflow_generator.utils.sse_response import stream_generator

logger = logging.getLogger(__name__)


class RequirementUnderstandingAgent(BaseWorkflowAgent):
    """
    Agent for understanding user requirements and generating standardized requirement inputs.

    This agent takes raw user input, understands the intent, and reformulates it into
    a standardized format for further processing. It interacts with the user to clarify
    requirements until a complete understanding is achieved.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.requirement = {}
        self.model_parameters = {"temperature": 0.3, "max_tokens": 4096}
        self.output_parser = WorkflowOutputParser(
            result_type=dict,
            default_schema=self.default_schema
        )

    @property
    def default_schema(self) -> Dict[str, Any]:
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

        def _post_process(content: str) -> Dict[str, Any]:
            return self._process_response(input_data, content)
        return stream_generator(response_chunks, _post_process)

    def _process_response(self, input_data: str, response_content: str) -> Dict[str, Any]:
        self.history_messages.append(UserPromptMessage(content=input_data))

        self.requirement: Dict[str, Any] = self.output_parser.parse_response(
            response_content)
        if self.requirement.get('complete', False):
            self.history_messages.append(
                AssistantPromptMessage(content=self.requirement.get('clarification_questions', '')))
        else:
            self.history_messages.append(
                AssistantPromptMessage(content=self.requirement.get('requirement', '')))
        return self.requirement
