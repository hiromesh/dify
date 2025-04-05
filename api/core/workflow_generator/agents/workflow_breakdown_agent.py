"""
Workflow Breakdown Agent.
This agent is responsible for breaking down detailed requirements into a coarse workflow
with node information but without parameter details.
"""

from typing import Any, Dict, List, Optional
import json
import logging

from .base_agent import BaseWorkflowAgent
from core.model_runtime.entities.message_entities import (
    UserPromptMessage,
    SystemPromptMessage
)
from core.workflow_generator.prompt.workflow_breakdown_prompts import (
    SYSTEM_PROMPT,
    PROMPT_TEMPLATE
)

logger = logging.getLogger(__name__)

class WorkflowBreakdownAgent(BaseWorkflowAgent):
    """
    Agent for breaking down requirements into a coarse workflow.
    
    This agent takes detailed requirement specifications and generates a coarse workflow
    with node information but without detailed node parameters.
    """
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the workflow breakdown agent.
        
        Returns:
            The system prompt as a string.
        """
        return SYSTEM_PROMPT
    
    def get_prompt_template(self) -> str:
        """
        Get the prompt template for the workflow breakdown agent.
        
        Returns:
            The prompt template as a string.
        """
        return PROMPT_TEMPLATE
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the detailed requirement and generate a coarse workflow.
        
        Args:
            input_data: The detailed requirement specification as a dictionary.
            
        Returns:
            A dictionary containing the coarse workflow structure.
        """
        # Convert input_data to a formatted string for the prompt
        detailed_requirement = json.dumps(input_data, indent=2)
        
        # Prepare the prompt with the detailed requirement
        prompt = self.get_prompt_template().format(detailed_requirement=detailed_requirement)
        
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
            "workflow_name": "Sample Workflow",
            "description": "A sample workflow based on the requirements",
            "nodes": [
                {
                    "id": "node_1",
                    "type": "llm",
                    "name": "Initial Processing",
                    "description": "Process the initial user input"
                },
                {
                    "id": "node_2",
                    "type": "conditional",
                    "name": "Input Validation",
                    "description": "Validate the user input"
                },
                {
                    "id": "node_3",
                    "type": "data_processing",
                    "name": "Data Transformation",
                    "description": "Transform the data for further processing"
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
                }
            ]
        }
        
        return result
    
    def parse_llm_response(self, response: str) -> Dict[str, Any]:
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
            logger.warning("Failed to parse LLM response as JSON, attempting to extract structured information")
            
            # Fallback parsing logic - extract key sections
            result = {
                "workflow_name": "",
                "description": "",
                "nodes": [],
                "connections": []
            }
            
            # Simple extraction based on section headers
            current_section = None
            nodes_data = []
            connections_data = []
            
            lines = response.split("\n")
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                if line.lower().startswith("workflow name:"):
                    result["workflow_name"] = line.split(":", 1)[1].strip()
                elif line.lower().startswith("description:"):
                    result["description"] = line.split(":", 1)[1].strip()
                elif line.lower() == "nodes:":
                    current_section = "nodes"
                elif line.lower() == "connections:":
                    current_section = "connections"
                elif current_section == "nodes" and line.startswith("- "):
                    # Start of a new node
                    node = {"id": "", "type": "", "name": "", "description": ""}
                    node_lines = []
                    j = i
                    while j < len(lines) and (lines[j].startswith("- ") or lines[j].startswith("  ")):
                        node_lines.append(lines[j].strip())
                        j += 1
                    
                    # Parse node data
                    for node_line in node_lines:
                        if node_line.startswith("- "):
                            continue
                        if ":" in node_line:
                            key, value = node_line.split(":", 1)
                            key = key.strip()
                            value = value.strip()
                            if key == "id":
                                node["id"] = value
                            elif key == "type":
                                node["type"] = value
                            elif key == "name":
                                node["name"] = value
                            elif key == "description":
                                node["description"] = value
                    
                    nodes_data.append(node)
                elif current_section == "connections" and line.startswith("- "):
                    # Start of a new connection
                    connection = {"source": "", "target": "", "condition": ""}
                    connection_lines = []
                    j = i
                    while j < len(lines) and (lines[j].startswith("- ") or lines[j].startswith("  ")):
                        connection_lines.append(lines[j].strip())
                        j += 1
                    
                    # Parse connection data
                    for conn_line in connection_lines:
                        if conn_line.startswith("- "):
                            continue
                        if ":" in conn_line:
                            key, value = conn_line.split(":", 1)
                            key = key.strip()
                            value = value.strip()
                            if key == "source":
                                connection["source"] = value
                            elif key == "target":
                                connection["target"] = value
                            elif key == "condition":
                                connection["condition"] = value
                    
                    # Only add condition if it's not empty
                    if not connection["condition"]:
                        del connection["condition"]
                    
                    connections_data.append(connection)
            
            result["nodes"] = nodes_data
            result["connections"] = connections_data
            
            return result
