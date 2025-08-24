from ..core.tool_registry import ToolRegistry
from .calculator_tool import CalculatorTool
from .weather_tool import WeatherTool
from .log_analysis_tool import LogAnalysisTool
from .system_info_tool import SystemInfoTool

def register_all_tools(registry: ToolRegistry) -> None:
    """Register all available tools"""
    

    
    # Register calculator tool
    calculator_tool = CalculatorTool()
    registry.register_tool(calculator_tool)

    # Register weather tool
    weather_tool = WeatherTool()
    registry.register_tool(weather_tool)

    # Register log analysis tool
    log_analysis_tool = LogAnalysisTool()
    registry.register_tool(log_analysis_tool)

    # Register system information tool
    system_info_tool = SystemInfoTool()
    registry.register_tool(system_info_tool)
