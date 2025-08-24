from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel,ValidationError



class ToolSchema(BaseModel):
    """Schema for tool metadata"""
    name: str
    description: str
    parameters: Dict[str, Any]

class ToolResponse(BaseModel):
    """Standardized response from tool execution."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None

    

class BaseTool(ABC):
    """Abstract base class for all tools
        
    Provides:
      - Automatic parameter validation
      - Error handling
      - Logging hooks
      - Execution timing
    """
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the tool"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Brief description of the tool's purpose"""
        pass

    @property
    @abstractmethod
    def schema(self) -> ToolSchema:
        """Tool schema for LLM"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResponse:
        """
        Execute the tool with given parameters.
        
        Args:
            kwargs: Arbitrary keyword arguments matching tool schema.

        Returns:
            ToolResponse: Standardized success/error response.
        """
        pass
    
    @property
    def parameters_model(self) -> Optional[BaseModel]:
        """
        Override to provide structured parameter validation via Pydantic.
        If None, parameters will not be strictly validated.
        """
        return None 
