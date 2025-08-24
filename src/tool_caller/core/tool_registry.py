import logging



from typing import Dict, Any, List, Optional
from ..tools.base import BaseTool, ToolResponse, ToolSchema



logger = logging.getLogger(__name__)



class ToolRegistry:
    """Registry for managing and executing tools."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._schemas: List[ToolSchema] = {}
        
    def register_tool(self, tool: BaseTool):
        """Register a new tool.
        
        Args:
            tool (BaseTool): Tool instance to register.
        
        Raises:
            ValueError: If a tool with the same name is already registered.
        """

        tool_name = tool.name
        if tool_name in self._tools:
            logger.warning(f"Tool {tool_name} is already registered. Overwriting.")
        self._tools[tool_name] = tool
        self._schemas[tool_name] = tool.schema
        logger.info(f"Registered tool: {tool_name}")