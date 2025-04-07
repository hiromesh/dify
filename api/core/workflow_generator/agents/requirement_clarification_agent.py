import json
import logging
from typing import Any

from core.workflow_generator.prompt.requirement_clarification_prompts import PROMPT_TEMPLATE, SYSTEM_PROMPT

from .base_agent import BaseWorkflowAgent

logger = logging.getLogger(__name__)


class RequirementClarificationAgent(BaseWorkflowAgent):
    """
    Agent for clarifying and refining user requirements.

    This agent takes standardized requirement inputs, imports planning documents if available,
    and generates detailed requirement specifications with complete rules.
    """

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the requirement clarification agent.

        Returns:
            The system prompt as a string.
        """
        return SYSTEM_PROMPT

    def get_prompt_template(self) -> str:
        """
        Get the prompt template for the requirement clarification agent.

        Returns:
            The prompt template as a string.
        """
        return PROMPT_TEMPLATE

    def process(self, input_data: dict[str, Any], planning_document: str = "") -> dict[str, Any]:
        """
        Process the standardized requirement and planning document to generate detailed requirements.

        Args:
            input_data: The standardized requirement as a dictionary.
            planning_document: Optional planning document content as a string.

        Returns:
            A dictionary containing the detailed requirement specification.
        """
        # Convert input_data to a formatted string for the prompt
        input_requirement = json.dumps(input_data, indent=2)

        # Prepare the prompt with the input requirement and planning document
        prompt = self.get_prompt_template().format(
            input_requirement=input_requirement,
            planning_document=planning_document or "No planning document provided."
        )

        # Prepare messages for the LLM
        messages = self._construct_messages(prompt)

        # Here you would call the LLM with these messages
        # For now, we'll just return a placeholder
        # In a real implementation, you would:
        # 1. Call the LLM
        # 2. Parse the response
        # 3. Format it as needed

        # Placeholder for LLM call result
        result = {
            "refined_intent": "Extract refined intent from LLM response",
            "detailed_functionalities": [
                {
                    "name": "Functionality 1",
                    "description": "Detailed description",
                    "behavior": "Expected behavior"
                }
            ],
            "workflow_steps": [
                {
                    "name": "Step 1",
                    "description": "Step description",
                    "inputs": ["Input 1"],
                    "outputs": ["Output 1"]
                }
            ],
            "business_rules": [
                {
                    "rule": "Business rule 1",
                    "description": "Rule description"
                }
            ],
            "data_requirements": [
                {
                    "name": "Data element 1",
                    "type": "string",
                    "description": "Data description"
                }
            ],
            "integration_points": [
                {
                    "system": "System 1",
                    "purpose": "Integration purpose",
                    "data_flow": "Data flow description"
                }
            ],
            "validation_criteria": [
                "Validation criterion 1"
            ]
        }

        return result

    def parse_llm_response(self, response: str) -> dict[str, Any]:
        """
        Parse the LLM response into a structured format.

        Args:
            response: The raw response from the LLM.

        Returns:
            A dictionary containing the parsed response.
        """
        try:
            # Attempt to parse as JSON
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError:
            # If not valid JSON, attempt to extract structured information
            logger.warning(
                "Failed to parse LLM response as JSON, attempting to extract structured information")

            # Fallback parsing logic - extract key sections
            result = {
                "refined_intent": "",
                "detailed_functionalities": [],
                "workflow_steps": [],
                "business_rules": [],
                "data_requirements": [],
                "integration_points": [],
                "validation_criteria": []
            }

            # Simple extraction based on section headers
            # This is a simplified implementation and would need to be more robust in production
            current_section = None
            current_items = []

            lines = response.split("\n")
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line.lower().startswith("refined intent:"):
                    if current_section and current_items:
                        result[current_section] = current_items
                    current_section = "refined_intent"
                    result[current_section] = line.split(":", 1)[1].strip()
                    current_items = []
                elif line.lower().startswith("detailed functionalities:"):
                    if current_section and current_items and current_section != "refined_intent":
                        result[current_section] = current_items
                    current_section = "detailed_functionalities"
                    current_items = []
                elif line.lower().startswith("workflow steps:"):
                    if current_section and current_items and current_section != "refined_intent":
                        result[current_section] = current_items
                    current_section = "workflow_steps"
                    current_items = []
                elif line.lower().startswith("business rules:"):
                    if current_section and current_items and current_section != "refined_intent":
                        result[current_section] = current_items
                    current_section = "business_rules"
                    current_items = []
                elif line.lower().startswith("data requirements:"):
                    if current_section and current_items and current_section != "refined_intent":
                        result[current_section] = current_items
                    current_section = "data_requirements"
                    current_items = []
                elif line.lower().startswith("integration points:"):
                    if current_section and current_items and current_section != "refined_intent":
                        result[current_section] = current_items
                    current_section = "integration_points"
                    current_items = []
                elif line.lower().startswith("validation criteria:"):
                    if current_section and current_items and current_section != "refined_intent":
                        result[current_section] = current_items
                    current_section = "validation_criteria"
                    current_items = []
                elif current_section and current_section != "refined_intent":
                    # Add item to current section
                    if line.startswith("- ") or line.startswith("* "):
                        current_items.append(line[2:])
                    else:
                        current_items.append(line)

            # Add the last section
            if current_section and current_items and current_section != "refined_intent":
                result[current_section] = current_items

            return result
