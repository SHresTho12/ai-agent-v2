from ..core.tool_registry import ToolRegistry
from .calculator_tool import CalculatorTool
from .weather_tool import WeatherTool

def register_all_tools(registry: ToolRegistry) -> None:
    """Register all available tools"""
    

    
    # Register calculator tool
    calculator_tool = CalculatorTool()
    registry.register_tool(calculator_tool)

    # Register weather tool
    weather_tool = WeatherTool()
    registry.register_tool(weather_tool)