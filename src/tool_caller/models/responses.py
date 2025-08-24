from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json
import uuid

class ToolCallResponse(BaseModel):
    """Model for a tool call response"""
    
    id: str = Field(..., description="Tool call identifier")
    name: str = Field(..., description="Name of the called tool")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments passed to the tool")
    
    @validator('arguments', pre=True)
    def parse_arguments(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v or {}
class SafetyRating(BaseModel):
    """Model for Gemini safety ratings"""
    
    category: str = Field(..., description="Safety category")
    probability: str = Field(..., description="Probability level")
    blocked: bool = Field(default=False, description="Whether content was blocked")

class CitationMetadata(BaseModel):
    """Model for Gemini citation metadata"""
    
    citation_sources: List[Dict[str, Any]] = Field(default_factory=list, description="Citation sources")

class LLMResponse(BaseModel):
    """Response model from LLM interactions"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Response identifier")
    request_id: Optional[str] = Field(default=None, description="Associated request ID")
    
    # Response content
    content: Optional[str] = Field(default=None, description="Text response from LLM")
    tool_calls: List[ToolCallResponse] = Field(default_factory=list, description="Tool calls requested by LLM")
    
    # Response metadata
    model: Optional[str] = Field(default=None, description="Model used for generation")
    finish_reason: Optional[str] = Field(default=None, description="Reason for completion")
    
    # Usage statistics
    prompt_tokens: Optional[int] = Field(default=None, description="Tokens in prompt")
    completion_tokens: Optional[int] = Field(default=None, description="Tokens in completion") 
    total_tokens: Optional[int] = Field(default=None, description="Total tokens used")
    
    # Timing information
    response_time: Optional[float] = Field(default=None, description="Response time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    # Status information
    success: bool = Field(default=True, description="Whether the request was successful")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    
    @validator('tool_calls', pre=True)
    def parse_tool_calls(cls, v):
        if not v:
            return []
        
        parsed_calls = []
        for call in v:
            if isinstance(call, dict):
                parsed_calls.append(ToolCallResponse(**call))
            elif isinstance(call, ToolCallResponse):
                parsed_calls.append(call)
        
        return parsed_calls
    
    @classmethod
    def from_openai_response(cls, response, request_id: Optional[str] = None, response_time: Optional[float] = None) -> "LLMResponse":
        """Create LLMResponse from OpenAI API response"""
        
        try:
            # Handle different response types
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                message = choice.message
                
                # Extract content
                content = message.content if hasattr(message, 'content') else None
                
                # Extract tool calls
                tool_calls = []
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_calls.append(ToolCallResponse(
                            id=tool_call.id,
                            name=tool_call.function.name,
                            arguments=tool_call.function.arguments
                        ))
                
                # Extract usage information
                usage = getattr(response, 'usage', None)
                prompt_tokens = getattr(usage, 'prompt_tokens', None) if usage else None
                completion_tokens = getattr(usage, 'completion_tokens', None) if usage else None
                total_tokens = getattr(usage, 'total_tokens', None) if usage else None
                
                # Extract model and finish reason
                model = getattr(response, 'model', None)
                finish_reason = getattr(choice, 'finish_reason', None)
                
                return cls(
                    request_id=request_id,
                    content=content,
                    tool_calls=tool_calls,
                    model=model,
                    finish_reason=finish_reason,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    response_time=response_time,
                    success=True
                )
            else:
                # Handle error response or unexpected format
                return cls(
                    request_id=request_id,
                    success=False,
                    error=f"Unexpected response format: {type(response)}",
                    response_time=response_time
                )
                
        except Exception as e:
            return cls(
                request_id=request_id,
                success=False,
                error=f"Failed to parse OpenAI response: {str(e)}",
                response_time=response_time
            )
    
    @classmethod
    def create_error_response(cls, error_message: str, request_id: Optional[str] = None, response_time: Optional[float] = None) -> "LLMResponse":
        """Create an error response"""
        return cls(
            request_id=request_id,
            success=False,
            error=error_message,
            response_time=response_time
        )
    
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls"""
        return bool(self.tool_calls)
    
    def get_tool_calls_dict(self) -> List[Dict[str, Any]]:
        """Get tool calls as dictionary format"""
        return [
            {
                "id": call.id,
                "name": call.name,
                "parameters": call.arguments
            }
            for call in self.tool_calls
        ]
    
    def is_successful(self) -> bool:
        """Check if the response was successful"""
        return self.success and self.error is None
    
    def get_usage_info(self) -> Dict[str, Any]:
        """Get usage information"""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "response_time": self.response_time
        }
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ExecutionResult(BaseModel):
    """Result of tool execution"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Execution result identifier")
    tool_call_id: Optional[str] = Field(default=None, description="Associated tool call ID")
    tool_name: str = Field(..., description="Name of executed tool")
    
    # Execution results
    success: bool = Field(..., description="Whether execution was successful")
    result: Any = Field(default=None, description="Tool execution result")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    
    # Timing and metadata
    execution_time: Optional[float] = Field(default=None, description="Execution time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional execution metadata")
    
    def is_successful(self) -> bool:
        """Check if execution was successful"""
        return self.success and self.error is None
    
    def get_result_for_llm(self) -> str:
        """Format result for LLM consumption"""
        if not self.success:
            return f"Tool execution failed: {self.error}"
        
        if isinstance(self.result, dict):
            return json.dumps(self.result, indent=2)
        elif isinstance(self.result, (list, tuple)):
            return json.dumps(self.result)
        else:
            return str(self.result)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ConversationState(BaseModel):
    """Model for tracking conversation state"""
    
    session_id: str = Field(..., description="Session identifier")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    
    # Conversation history
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="Message history")
    tool_executions: List[ExecutionResult] = Field(default_factory=list, description="Tool execution history")
    
    # State metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Conversation start time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    
    # Configuration
    context: Dict[str, Any] = Field(default_factory=dict, description="Conversation context")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Conversation settings")
    
    def add_message(self, role: str, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None):
        """Add a message to conversation history"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "tool_calls": tool_calls or []
        }
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
    
    def add_tool_execution(self, execution_result: ExecutionResult):
        """Add tool execution to history"""
        self.tool_executions.append(execution_result)
        self.updated_at = datetime.utcnow()
    
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages"""
        return self.messages[-count:] if self.messages else []
    
    def get_tool_usage_stats(self) -> Dict[str, Any]:
        """Get tool usage statistics"""
        tool_stats = {}
        for execution in self.tool_executions:
            tool_name = execution.tool_name
            if tool_name not in tool_stats:
                tool_stats[tool_name] = {
                    "total_calls": 0,
                    "successful_calls": 0,
                    "failed_calls": 0,
                    "avg_execution_time": 0.0
                }
            
            tool_stats[tool_name]["total_calls"] += 1
            if execution.success:
                tool_stats[tool_name]["successful_calls"] += 1
            else:
                tool_stats[tool_name]["failed_calls"] += 1
        
        # Calculate averages
        for tool_name, stats in tool_stats.items():
            executions = [e for e in self.tool_executions if e.tool_name == tool_name and e.execution_time]
            if executions:
                avg_time = sum(e.execution_time for e in executions) / len(executions)
                stats["avg_execution_time"] = round(avg_time, 4)
        
        return tool_stats
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }