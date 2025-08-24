import math
import time
import logging
import ast
import operator
from typing import Dict, Any
from ..tools.base import BaseTool, ToolResponse, ToolSchema


logger = logging.getLogger(__name__)

class CalculatorTool(BaseTool):
    """Tool for performing mathematical calculations"""
    
    # Safe operators for evaluation
    SAFE_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }
    
    # Safe functions
    SAFE_FUNCTIONS = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'log': math.log,
        'log10': math.log10,
        'exp': math.exp,
        'pi': math.pi,
        'e': math.e
    }
    
    @property
    def name(self) -> str:
        return "calculate"
    
    @property
    def description(self) -> str:
        return "Perform mathematical calculations safely"
    
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    },
                    "precision": {
                        "type": "integer",
                        "description": "Number of decimal places for result",
                        "default": 4
                    }
                },
                "required": ["expression"]
            }
        )
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate input parameters"""
        if "expression" not in parameters:
            return False
        
        if not isinstance(parameters["expression"], str):
            return False
        
        precision = parameters.get("precision", 4)
        if not isinstance(precision, int) or precision < 0:
            return False
        
        return True
    
    def _safe_eval(self, expression: str) -> float:
        """Safely evaluate mathematical expression"""
        try:
            # Parse the expression
            tree = ast.parse(expression, mode='eval')
            
            # Evaluate the AST safely
            return self._eval_node(tree.body)
        
        except Exception as e:
            logger.error(f"Error evaluating expression '{expression}': {str(e)}")
            raise ValueError(f"Invalid expression: {str(e)}")
    
    def _eval_node(self, node):
        """Recursively evaluate AST nodes"""
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op = self.SAFE_OPERATORS.get(type(node.op))
            if op:
                return op(left, right)
            else:
                logger.error(f"Unsupported operator: {type(node.op)}")
                raise ValueError(f"Unsupported operator: {type(node.op)}")
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op = self.SAFE_OPERATORS.get(type(node.op))
            if op:
                return op(operand)
            else:
                logger.error(f"Unsupported unary operator: {type(node.op)}")
                raise ValueError(f"Unsupported unary operator: {type(node.op)}")
        elif isinstance(node, ast.Call):
            func_name = node.func.id
            if func_name in self.SAFE_FUNCTIONS:
                args = [self._eval_node(arg) for arg in node.args]
                return self.SAFE_FUNCTIONS[func_name](*args)
            else:
                logger.error(f"Unsupported function: {func_name}")
                raise ValueError(f"Unsupported function: {func_name}")
        elif isinstance(node, ast.Name):
            if node.id in self.SAFE_FUNCTIONS:
                return self.SAFE_FUNCTIONS[node.id]
            else:
                logger.error(f"Unsupported name: {node.id}")
                raise ValueError(f"Unsupported name: {node.id}")
        else:
            logger.error(f"Unsupported node type: {type(node)}")
            raise ValueError(f"Unsupported node type: {type(node)}")

    async def _run(self, **kwargs) -> Any:
        """Core calculation logic."""
        expression = kwargs["expression"]
        precision = kwargs.get("precision", 4)
        result = self._safe_eval(expression)
        if isinstance(result, float):
            result = round(result, precision)
        return {
            "expression": expression,
            "result": result,
            "precision": precision
        }