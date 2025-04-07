"""
Workflow Detailing Agent.
This agent is responsible for adding detailed node parameters and data transformations
to a coarse workflow, generating a complete Dify workflow in YAML format.
"""

import json
import logging
from typing import Any

import yaml

from core.workflow_generator.prompt.workflow_detailing_prompts import PROMPT_TEMPLATE, SYSTEM_PROMPT

from .base_agent import BaseWorkflowAgent

logger = logging.getLogger(__name__)

class WorkflowDetailingAgent(BaseWorkflowAgent):
    """
    Agent for adding detailed parameters to workflow nodes.
    
    This agent takes a coarse workflow structure and adds detailed parameters and
    data transformations to generate a complete Dify workflow in YAML format.
    """
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the workflow detailing agent.
        
        Returns:
            The system prompt as a string.
        """
        return SYSTEM_PROMPT
    
    def get_prompt_template(self) -> str:
        """
        Get the prompt template for the workflow detailing agent.
        
        Returns:
            The prompt template as a string.
        """
        return PROMPT_TEMPLATE
    
    def process(self, coarse_workflow: dict[str, Any], detailed_requirements: dict[str, Any]) -> str:
        """
        Process the coarse workflow and detailed requirements to generate a complete workflow.
        
        Args:
            coarse_workflow: The coarse workflow structure as a dictionary.
            detailed_requirements: The detailed requirements as a dictionary.
            
        Returns:
            A string containing the complete Dify workflow in YAML format.
        """
        # Convert input data to formatted strings for the prompt
        coarse_workflow_str = json.dumps(coarse_workflow, indent=2)
        detailed_requirements_str = json.dumps(detailed_requirements, indent=2)
        
        # Prepare the prompt with the coarse workflow and detailed requirements
        prompt = self.get_prompt_template().format(
            coarse_workflow=coarse_workflow_str,
            detailed_requirements=detailed_requirements_str
        )
        
        # Prepare messages for the LLM
        messages = self._construct_messages(prompt)
        
        # Here you would call the LLM with these messages
        # For now, we'll just return a placeholder
        # In a real implementation, you would:
        # 1. Call the LLM
        # 2. Parse the response
        # 3. Format it as needed
        
        # Placeholder for LLM call result - a sample Dify workflow in YAML format
        sample_workflow = {
            "name": coarse_workflow.get("workflow_name", "Sample Workflow"),
            "description": coarse_workflow.get("description", "A sample workflow"),
            "nodes": [
                {
                    "id": "node_1",
                    "type": "llm",
                    "name": "Initial Processing",
                    "description": "Process the initial user input",
                    "parameters": {
                        "model": "gpt-4",
                        "temperature": 0.7,
                        "max_tokens": 1000,
                        "prompt_template": "Process the following user input: {{input}}",
                        "output_key": "processed_input"
                    }
                },
                {
                    "id": "node_2",
                    "type": "conditional",
                    "name": "Input Validation",
                    "description": "Validate the user input",
                    "parameters": {
                        "conditions": [
                            {
                                "condition": "{{processed_input.length}} > 0",
                                "target": "node_3",
                                "description": "Input is not empty"
                            },
                            {
                                "condition": "default",
                                "target": "node_error",
                                "description": "Input is empty"
                            }
                        ]
                    }
                },
                {
                    "id": "node_3",
                    "type": "data_processing",
                    "name": "Data Transformation",
                    "description": "Transform the data for further processing",
                    "parameters": {
                        "transformation_type": "json",
                        "input_key": "processed_input",
                        "output_key": "transformed_data",
                        "transformation_script": "return JSON.parse(input);"
                    }
                },
                {
                    "id": "node_error",
                    "type": "output",
                    "name": "Error Output",
                    "description": "Handle error case",
                    "parameters": {
                        "message": "Error: Input validation failed",
                        "status": "error"
                    }
                }
            ],
            "connections": [
                {
                    "source": "node_1",
                    "target": "node_2"
                },
                {
                    "source": "node_2",
                    "target": "node_3",
                    "condition": "input_valid == true"
                },
                {
                    "source": "node_2",
                    "target": "node_error",
                    "condition": "default"
                }
            ]
        }
        
        # Convert the sample workflow to YAML
        yaml_workflow = yaml.dump(sample_workflow, sort_keys=False, default_flow_style=False)
        
        return yaml_workflow
    
    def parse_llm_response(self, response: str) -> str:
        """
        Parse the LLM response and ensure it's valid YAML.
        
        Args:
            response: The raw response from the LLM.
            
        Returns:
            A string containing the validated YAML workflow.
        """
        # Extract YAML content if wrapped in markdown code blocks
        if "```yaml" in response or "```yml" in response:
            # Extract content between yaml code blocks
            start_idx = response.find("```yaml")
            if start_idx == -1:
                start_idx = response.find("```yml")
            
            if start_idx != -1:
                start_idx = response.find("\n", start_idx) + 1
                end_idx = response.find("```", start_idx)
                if end_idx != -1:
                    yaml_content = response[start_idx:end_idx].strip()
                else:
                    yaml_content = response[start_idx:].strip()
            else:
                yaml_content = response
        else:
            yaml_content = response
        
        # Validate the YAML
        try:
            workflow = yaml.safe_load(yaml_content)
            # Re-dump to ensure proper formatting
            return yaml.dump(workflow, sort_keys=False, default_flow_style=False)
        except yaml.YAMLError as e:
            logger.exception("Invalid YAML in LLM response")
            # Return the original content if validation fails
            return yaml_content
