import logging



from typing import Dict, Any, List, Optional
from ..tools.base import BaseTool,  ToolSchema



logger = logging.getLogger(__name__)



class ToolRegistry:
    """Registry for managing and executing tools."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._schemas: List[ToolSchema] = {}
        
    def register_tool(self, tool: BaseTool) -> None:
        """Register a new tool.
        
        Args:
            tool (BaseTool): Tool instance to register.
        
        Raises:
            ValueError: If a tool with the same name is already registered.
        """

        tool_name = tool.name
        if tool_name in self._tools:
            # I think there should be a stricter enforcement for overwriting tools. 
            # For example the available tools name and description should be prompted to the user and they should confirm the overwrite. Might do later
            logger.warning(f"Tool {tool_name} is already registered. Overwriting.")
            
        self._tools[tool_name] = tool
        self._schemas[tool_name] = tool.schema
        logger.info(f"Registered tool: {tool_name}")
    
    
    def unregister_tool(self, tool_name: str) -> None:
        """Unregister a tool by name.
        
        Args:
            tool_name (str): Name of the tool to unregister.
        
        Raises:
            KeyError: If the tool is not found.
        """
        if tool_name not in self._tools:
            logger.error(f"Tool {tool_name} not found for unregistration.")
            return
        del self._tools[tool_name]
        del self._schemas[tool_name]
        logger.info(f"Unregistered tool: {tool_name}")
        
        
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Retrieve a tool by name.
        
        Args:
            tool_name (str): Name of the tool to retrieve.
        
        Returns:
            Optional[BaseTool]: The tool instance or None if not found.
        """
        return self._tools.get(tool_name)

    def get_all_schemas(self) -> List[ToolSchema]:
        """Retrieve all tool schemas.
        
        Returns:
            List[ToolSchema]: A list of all tool schemas.
        """
        return list(self._schemas.values())

    def get_all_tools_verbose(self) -> List[BaseTool]:
        """Retrieve all registered tools with their details.
        
        Returns:
            List[BaseTool]: A list of all registered tools.
        """
        # I think this and get all schema function is doing the same thing. But I think there may be some cases or special cases when we need this . Will go over later
        return list(self._tools.values())   
    
    def get_all_tool_names(self) -> List[str]:
        """Retrieve the names of all registered tools.

        Returns:
            List[str]: A list of all tool names.
        """
        return list(self._tools.keys())

    def auto_register_tools(self, tool_directory: str ="tool_caller.tools") -> None:
        """Automatically register tools found in the specified directory.
        """
        # I will do it later
        pass
