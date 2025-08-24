from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional, Union
import logging
from datetime import datetime
import json
import uuid


logger = logging.getLogger(__name__)

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

class GeminiLLMResponse(BaseModel):
    """Response model from LLM interactions - Gemini focused"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Response identifier")
    request_id: Optional[str] = Field(default=None, description="Associated request ID")
    
    # Response content
    content: Optional[str] = Field(default=None, description="Text response from LLM")
    tool_calls: List[ToolCallResponse] = Field(default_factory=list, description="Tool calls requested by LLM")
    
    # Response metadata
    model: Optional[str] = Field(default="gemini-1.5-pro", description="Model used for generation")
    finish_reason: Optional[str] = Field(default=None, description="Reason for completion")
    
    # Gemini-specific fields
    safety_ratings: List[SafetyRating] = Field(default_factory=list, description="Gemini safety ratings")
    citation_metadata: Optional[CitationMetadata] = Field(default=None, description="Citation information")
    
    # # Usage statistics (Gemini format)
    # prompt_token_count: Optional[int] = Field(default=None, description="Tokens in prompt")
    # candidates_token_count: Optional[int] = Field(default=None, description="Tokens in candidates")
    # total_token_count: Optional[int] = Field(default=None, description="Total tokens used")
    

    
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
    
    @validator('safety_ratings', pre=True)
    def parse_safety_ratings(cls, v):
        if not v:
            return []
        
        parsed_ratings = []
        for rating in v:
            if isinstance(rating, dict):
                parsed_ratings.append(SafetyRating(**rating))
            elif isinstance(rating, SafetyRating):
                parsed_ratings.append(rating)
        
        return parsed_ratings
    
    @classmethod
    def from_gemini_response(cls, response, request_id: Optional[str] = None, response_time: Optional[float] = None) -> "GeminiLLMResponse":
        """Create GeminiLLMResponse from Gemini API response"""

        try:
            # Handle GenerateContentResponse or similar Gemini response
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
            
                content = None
                tool_calls = []
                if hasattr(candidate, 'content') and candidate.content:
                    content_parts = candidate.content.parts
                    text_parts = []
                    for part in content_parts:
                        # print("Processing part:", part)
                        # print("Part type:", type(part))
                        # print("part.function_call:", getattr(part, "function_call", None))
                        
                        # Check for function_call first, or make text check more specific
                        if hasattr(part, "function_call") and part.function_call:
                            func_call = part.function_call
                            arguments = {}
                            args = getattr(func_call, "args", None)
                            # print("Processing function call arguments...")
                            # print("args:", args)
                            if args:
                                try:
                                    # print("Trying to iterate as dict...")
                                    for k, v in args.items():
                                        print(f"Key: {k}, Value: {v}, Value type: {type(v)}")
                                        arguments[k] = v
                                except Exception as e:
                                    logger.error(f"Dict iteration failed: {e}")
                                    # print(f"Dict iteration failed: {e}")

                                    try:
                                        # print("Trying dict() conversion...")
                                        args_dict = dict(args)
                                        print("Converted args_dict:", args_dict)
                                        for k, v in args_dict.items():
                                            print(f"Key: {k}, Value: {v}")
                                            arguments[k] = v
                                    except Exception as e2:
                                        print(f"Dict conversion failed: {e2}")
                                        
                                        # Last resort - check what methods are available
                                        print("Available methods:", [method for method in dir(args) if not method.startswith('_')])

                            
                            # print("Extracted tool call arguments:", arguments)
                            tool_calls.append(ToolCallResponse(
                                id=str(uuid.uuid4()),
                                name=getattr(func_call, "name", ""),
                                arguments=arguments
                            ))
                        # If part has 'text' and it's not empty/None, treat as text response
                        elif getattr(part, "text", None) and part.text.strip():
                            text_parts.append(part.text)
                        # If part itself is a function_call (protobuf style)
                        elif getattr(part, "name", None) and getattr(part, "args", None):
                            arguments = {}
                            args = getattr(part, "args", None)
                            if args and hasattr(args, "fields"):
                                for k, v in args.fields.items():
                                    if hasattr(v, "string_value"):
                                        arguments[k] = v.string_value
                                    elif hasattr(v, "number_value"):
                                        arguments[k] = v.number_value
                                    elif hasattr(v, "bool_value"):
                                        arguments[k] = v.bool_value
                                    else:
                                        arguments[k] = str(v)
                                tool_calls.append(ToolCallResponse(
                            id=str(uuid.uuid4()),
                            name=part.name,
                            arguments=arguments
                            ))
                    content = '\n'.join(text_parts) if text_parts else None
                    print("Extracted tool calls:", tool_calls)
                
                # Extract safety ratings
                safety_ratings = []
                if hasattr(candidate, 'safety_ratings'):
                    for rating in candidate.safety_ratings:
                        safety_ratings.append(SafetyRating(
                            category=rating.category.name if hasattr(rating.category, 'name') else str(rating.category),
                            probability=rating.probability.name if hasattr(rating.probability, 'name') else str(rating.probability),
                            blocked=getattr(rating, 'blocked', False)
                        ))
                
                # Extract citation metadata
                citation_metadata = None
                if hasattr(candidate, 'citation_metadata') and candidate.citation_metadata:
                    citation_sources = []
                    if hasattr(candidate.citation_metadata, 'citation_sources'):
                        citation_sources = [dict(source) for source in candidate.citation_metadata.citation_sources]
                    citation_metadata = CitationMetadata(citation_sources=citation_sources)
                
                # Extract usage information
                usage_metadata = getattr(response, 'usage_metadata', None)
                prompt_token_count = getattr(usage_metadata, 'prompt_token_count', None) if usage_metadata else None
                candidates_token_count = getattr(usage_metadata, 'candidates_token_count', None) if usage_metadata else None
                total_token_count = getattr(usage_metadata, 'total_token_count', None) if usage_metadata else None
                
                # Extract finish reason
                finish_reason = None
                if hasattr(candidate, 'finish_reason'):
                    finish_reason = candidate.finish_reason.name if hasattr(candidate.finish_reason, 'name') else str(candidate.finish_reason)
       
                return cls(
                    request_id=request_id,
                    content=content,
                    tool_calls=tool_calls,
                    model="gemini-1.5-pro",  # Default Gemini model
                    finish_reason=finish_reason,
                    safety_ratings=safety_ratings,
                    citation_metadata=citation_metadata,
                    prompt_token_count=prompt_token_count,
                    candidates_token_count=candidates_token_count,
                    total_token_count=total_token_count,
                    # Set legacy fields for compatibility
                    prompt_tokens=prompt_token_count,
                    completion_tokens=candidates_token_count,
                    total_tokens=total_token_count,
                    response_time=response_time,
                    success=True
                )
            else:
                # Handle error response or unexpected format
                return cls(
                    request_id=request_id,
                    success=False,
                    error=f"Unexpected Gemini response format: {type(response)}",
                    response_time=response_time
                )
                
        except Exception as e:
            return cls(
                request_id=request_id,
                success=False,
                error=f"Failed to parse Gemini response: {str(e)}",
                response_time=response_time
            )
    

    @classmethod
    def create_error_response(cls, error_message: str, request_id: Optional[str] = None, response_time: Optional[float] = None) -> "GeminiLLMResponse":
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
    
    def is_blocked_by_safety(self) -> bool:
        """Check if response was blocked by Gemini safety filters"""
        return any(rating.blocked for rating in self.safety_ratings)
    
    def get_usage_info(self) -> Dict[str, Any]:
        """Get usage information (Gemini format)"""
        return {
            "prompt_token_count": self.prompt_token_count,
            "candidates_token_count": self.candidates_token_count,
            "total_token_count": self.total_token_count,
            "response_time": self.response_time,
            # Legacy compatibility
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens
        }
    
    def get_safety_info(self) -> Dict[str, Any]:
        """Get safety rating information"""
        return {
            "safety_ratings": [
                {
                    "category": rating.category,
                    "probability": rating.probability,
                    "blocked": rating.blocked
                }
                for rating in self.safety_ratings
            ],
            "blocked_by_safety": self.is_blocked_by_safety()
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
    
    def to_gemini_function_response(self) -> Dict[str, Any]:
        """Convert to Gemini function response format"""
        return {
            "function_response": {
                "name": self.tool_name,
                "response": {
                    "success": self.success,
                    "result": self.result if self.success else None,
                    "error": self.error if not self.success else None,
                    "execution_time": self.execution_time
                }
            }
        }
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ConversationState(BaseModel):
    """Model for tracking conversation state - Gemini focused"""
    
    session_id: str = Field(..., description="Session identifier")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    
    # Conversation history (Gemini format)
    contents: List[Dict[str, Any]] = Field(default_factory=list, description="Gemini conversation contents")
    tool_executions: List[ExecutionResult] = Field(default_factory=list, description="Tool execution history")
    
    # Legacy message format for compatibility
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="Legacy message history")
    
    # State metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Conversation start time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    
    # Configuration
    context: Dict[str, Any] = Field(default_factory=dict, description="Conversation context")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Conversation settings")
    
    # Gemini-specific state
    safety_settings: List[Dict[str, Any]] = Field(default_factory=list, description="Gemini safety settings")
    system_instruction: Optional[str] = Field(default=None, description="Gemini system instruction")
    
    def add_content(self, role: str, parts: List[Dict[str, Any]]):
        """Add content to Gemini conversation history"""
        content = {
            "role": role,
            "parts": parts,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.contents.append(content)
        self.updated_at = datetime.utcnow()
    
    def add_user_message(self, text: str):
        """Add user message"""
        self.add_content("user", [{"text": text}])
        
        # Also add to legacy format
        self.add_message("user", text)
    
    def add_model_message(self, text: Optional[str] = None, function_calls: Optional[List[Dict[str, Any]]] = None):
        """Add model message"""
        parts = []
        if text:
            parts.append({"text": text})
        if function_calls:
            parts.extend(function_calls)
        
        self.add_content("model", parts)
        
        # Also add to legacy format
        self.add_message("model", text or "", tool_calls=function_calls)
    
    def add_function_responses(self, function_responses: List[Dict[str, Any]]):
        """Add function responses"""
        self.add_content("function", function_responses)
    
    def add_message(self, role: str, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None):
        """Add a message to legacy conversation history"""
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
    
    def get_recent_contents(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent Gemini contents"""
        return self.contents[-count:] if self.contents else []
    
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages (legacy format)"""
        return self.messages[-count:] if self.messages else []
    
    def to_gemini_history(self) -> List[Dict[str, Any]]:
        """Convert to Gemini conversation history format"""
        return [
            {
                "role": content["role"],
                "parts": content["parts"]
            }
            for content in self.contents
        ]
    
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
    
    def get_safety_summary(self) -> Dict[str, Any]:
        """Get safety-related summary for the conversation"""
        return {
            "safety_settings": self.safety_settings,
            "system_instruction": self.system_instruction,
            "total_messages": len(self.contents),
            "tool_executions_count": len(self.tool_executions)
        }
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }