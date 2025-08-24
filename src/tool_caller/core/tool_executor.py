import asyncio
import logging
from typing import List, Dict, Any
from .tool_registry import ToolRegistry
from ..models.responses import ExecutionResult


logger = logging.getLogger(__name__)

class ToolExecutor:
    '''Executes tool based on LLM decisions'''

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    async def execute_tool_calls(
        self, 
        tool_calls: List[Dict[str, Any]]
    ) -> List[ExecutionResult]:
        """Execute multiple tool calls concurrently"""

        if not tool_calls:
            return []

        tasks = []
        for tool_call in tool_calls:

            logger.info(f"Scheduling tool call: {tool_call}")
            task = self._execute_single_tool(tool_call)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        execution_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                execution_results.append(
                    ExecutionResult(
                        tool_name=tool_calls[i].name,
                        success=False,
                        error=str(result)
                    )
                )
            else:
                execution_results.append(result)
        
        return execution_results
    
    
    async def _execute_single_tool(self, tool_call: Dict[str, Any]) -> ExecutionResult:
        """Execute a single tool call"""
        # print("Executing tool call:", tool_call)
        # print("Type:", type(tool_call))
        
 
        tool_name = tool_call.name
        parameters = tool_call.arguments  
        
        #logger.info(f"Executing tool: {tool_name} with params: {parameters}")
        
        tool = self.registry.get_tool(tool_name)
        if not tool:
            logger.error(f"Tool {tool_name} not found in registry")
            raise ValueError(f"Tool {tool_name} not found")
        
        # Validate parameters
        if not tool.validate_parameters(parameters):
            logger.error(f"Invalid parameters for tool {tool_name}: {parameters}")
            raise ValueError(f"Invalid parameters for tool {tool_name}")
        
        # Execute tool
        result = await tool.execute(**parameters)
        
        return ExecutionResult(
            tool_name=tool_name,
            success=result.success,
            result=result.result,
            error=result.error,
            execution_time=result.execution_time
        )