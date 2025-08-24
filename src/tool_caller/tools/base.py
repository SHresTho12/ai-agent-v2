
import time
import logging

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel,ValidationError





logger = logging.getLogger(__name__)



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
    async def _run(self, **kwargs) -> Any:
        """
        Core logic of the tool. Must be implemented by subclasses.
        
        Args:
            kwargs: Arbitrary keyword arguments matching tool schema.

        Returns:
            Any: Result of the tool execution.
        """
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
        start_time = time.time()
        try:
            logger.debug(f"Executing tool {self.name} with params: {kwargs}")
            if self.parameters_model:
                try:
                    kwargs = self.parameters_model(**kwargs).dict()
                except ValidationError as ve:
                    logger.error(f"{self.name} Parameter validation error: {ve}")
                    return ToolResponse(success=False, error=f"Parameter validation error: {ve}", execution_time=time.time() - start_time)
            
            result = await self._run(**kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Tool {self.name} executed successfully in {execution_time:.4f}s")
            
            return ToolResponse(success=True, result=result, execution_time=execution_time)
        except Exception as e:
            execution_time = time.time() - start_time
            logger.exception(f"Tool {self.name} execution failed: {e} after {execution_time:.4f}s")
            return ToolResponse(success=False, error=str(e), execution_time=execution_time)

    @property
    def parameters_model(self) -> Optional[BaseModel]:
        """
        Override to provide structured parameter validation via Pydantic.
        If None, parameters will not be strictly validated.
        """
        return None 
