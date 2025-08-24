import pytest
from src.tool_caller.tools.calculator_tool import CalculatorTool

class TestCalculatorTool:
    
    @pytest.fixture
    def calculator(self):
        return CalculatorTool()
    
    def test_tool_properties(self, calculator):
        """Test tool basic properties"""
        assert calculator.name == "calculate"
        assert "mathematical calculations" in calculator.description.lower()
        assert calculator.schema.name == "calculate"
    
    def test_parameter_validation(self, calculator):
        """Test parameter validation"""
        # Valid parameters
        assert calculator.validate_parameters({"expression": "2 + 2"})
        assert calculator.validate_parameters({"expression": "2 + 2", "precision": 2})
        
        # Invalid parameters
        assert not calculator.validate_parameters({})
        assert not calculator.validate_parameters({"expression": 123})
        assert not calculator.validate_parameters({"expression": "2 + 2", "precision": "high"})
        