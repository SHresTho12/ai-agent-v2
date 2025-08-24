from ..core.tool_registry import ToolRegistry
from .calculator_tool import CalculatorTool

def register_all_tools(registry: ToolRegistry) -> None:
    """Register all available tools"""
    

    
    # Register calculator tool
    calculator_tool = CalculatorTool()
    registry.register_tool(calculator_tool)