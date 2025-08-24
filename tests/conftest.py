import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from src.tool_caller.core.tool_registry import ToolRegistry
from src.tool_caller.tools.calculator_tool import CalculatorTool


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def tool_registry():
    """Create a test tool registry"""
    registry = ToolRegistry()
    
    # Register test tools
    calculator = CalculatorTool()
    registry.register_tool(calculator)
    
    return registry