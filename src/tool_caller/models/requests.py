
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import uuid
import json

class ToolCallRequest(BaseModel):
    """Model for a single tool call request"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the tool call")
    name: str = Field(..., description="Name of the tool to call")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters to pass to the tool")
    
    @validator('name')
    def validate_tool_name(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Tool name must be a non-empty string")
        return v.strip()
    
    @validator('parameters')
    def validate_parameters(cls, v):
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("Parameters must be a dictionary")
        return v

class Message(BaseModel):
    """Model for a conversation message"""
    
    role: str = Field(..., description="Role of the message sender (user, model, system)")
    content: Optional[str] = Field(default=None, description="Text content of the message")
    tool_calls: Optional[List[ToolCallRequest]] = Field(default=None, description="Tool calls in this message")
    tool_call_id: Optional[str] = Field(default=None, description="ID of the tool call this message responds to")
    

    parts: Optional[List[Dict[str, Any]]] = Field(default=None, description="Gemini message parts")
    
    @validator('role')
    def validate_role(cls, v):
        # Gemini uses 'model' instead of 'assistant'
        valid_roles = {'user', 'model', 'system', 'function'}  # function for tool responses
        if v not in valid_roles:
            raise ValueError(f"Role must be one of: {valid_roles}")
        return v
    
    @validator('content')
    def validate_content(cls, v):
        # In Gemini, content can be None if parts are provided
        return v

class LLMRequest(BaseModel):
    """Main request model for LLM interactions - Gemini focused"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique request identifier")
    user_input: str = Field(..., description="Original user input")
    messages: List[Message] = Field(default_factory=list, description="Conversation history")
    available_tools: List[Dict[str, Any]] = Field(default_factory=list, description="Available tools for the LLM")
    
    # LLM Configuration - Gemini defaults
    model: str = Field(default="gemini-1.5-pro", description="Gemini model to use")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=2048, gt=0, description="Maximum tokens in response")
    
    # Gemini-specific configuration
    top_p: float = Field(default=0.95, ge=0.0, le=1.0, description="Top-p sampling parameter")
    top_k: int = Field(default=40, gt=0, description="Top-k sampling parameter")
    safety_settings: List[Dict[str, Any]] = Field(default_factory=list, description="Gemini safety settings")
    
    # Tool calling configuration
    tool_choice: Union[str, Dict[str, Any]] = Field(default="auto", description="Tool choice strategy")
    parallel_tool_calls: bool = Field(default=True, description="Allow parallel tool execution")
    
    # Request metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Request timestamp")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    
    @validator('user_input')
    def validate_user_input(cls, v):
        if not v or not v.strip():
            raise ValueError("User input cannot be empty")
        return v.strip()
    
    @validator('available_tools')
    def validate_available_tools(cls, v):
        if not isinstance(v, list):
            return []
        
        # Validate Gemini tool schema format
        for tool in v:
            if not isinstance(tool, dict):
                raise ValueError("Each tool must be a dictionary")
            
            # Gemini uses function_declarations format
            if 'function_declarations' in tool:
                for func_decl in tool['function_declarations']:
                    if 'name' not in func_decl:
                        raise ValueError("Tool function declaration must have a 'name'")
                    if 'description' not in func_decl:
                        raise ValueError("Tool function declaration must have a 'description'")
            else:
                # Also support OpenAI format for conversion
                if 'type' not in tool or tool['type'] != 'function':
                    raise ValueError("Each tool must have type 'function' or use function_declarations format")
                if 'function' not in tool:
                    raise ValueError("Each tool must have a 'function' key")
                
                function = tool['function']
                if 'name' not in function:
                    raise ValueError("Tool function must have a 'name'")
                if 'description' not in function:
                    raise ValueError("Tool function must have a 'description'")
        
        return v
    
    @validator('tool_choice')
    def validate_tool_choice(cls, v):
        if isinstance(v, str):
            valid_choices = {'auto', 'none', 'any'}  # Gemini uses 'any' instead of 'required'
            if v not in valid_choices:
                raise ValueError(f"Tool choice string must be one of: {valid_choices}")
        elif isinstance(v, dict):
            if 'function_calling_config' not in v:
                raise ValueError("Gemini tool choice dict must have 'function_calling_config' key")
        else:
            raise ValueError("Tool choice must be string or dict")
        
        return v
    
    @validator('safety_settings')
    def validate_safety_settings(cls, v):
        # Set default safety settings if none provided
        if not v:
            return [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH", 
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        return v
    
    def add_message(self, role: str, content: Optional[str] = None, tool_calls: Optional[List[ToolCallRequest]] = None, parts: Optional[List[Dict[str, Any]]] = None):
        """Add a message to the conversation history"""
        message = Message(role=role, content=content, tool_calls=tool_calls, parts=parts)
        self.messages.append(message)
    
    def add_user_message(self, content: str):
        """Add a user message"""
        self.add_message("user", content)
    
    def add_model_message(self, content: Optional[str] = None, tool_calls: Optional[List[ToolCallRequest]] = None):
        """Add a model (assistant) message"""
        self.add_message("model", content, tool_calls)
    
    def add_system_message(self, content: str):
        """Add a system message"""
        self.add_message("system", content)
    
    def add_function_response(self, tool_call_id: str, content: str):
        """Add a function response message"""
        message = Message(role="function", content=content, tool_call_id=tool_call_id)
        self.messages.append(message)
    
    def to_gemini_format(self) -> Dict[str, Any]:
        """Convert to Gemini API format"""
        # Convert messages to Gemini format
        gemini_contents = []
        
        for message in self.messages:
            if message.role == "system":
                # System messages are handled separately in Gemini
                continue
                
            content_parts = []
            
            # Add text content
            if message.content:
                content_parts.append({"text": message.content})
            
            # Add tool calls as function calls
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    content_parts.append({
                        "function_call": {
                            "name": tool_call.name,
                            "args": tool_call.parameters
                        }
                    })
            
            # Add function responses
            if message.role == "function" and message.tool_call_id:
                content_parts.append({
                    "function_response": {
                        "name": message.tool_call_id,  # Function name from tool call
                        "response": {"result": message.content}
                    }
                })
            
            # Add custom parts if provided
            if message.parts:
                content_parts.extend(message.parts)
            
            if content_parts:
                gemini_contents.append({
                    "role": message.role,
                    "parts": content_parts
                })
        
        # Add current user input if not already in messages
        if not gemini_contents or gemini_contents[-1]["role"] != "user":
            gemini_contents.append({
                "role": "user",
                "parts": [{"text": self.user_input}]
            })
        
        # Build the request
        request_data = {
            "contents": gemini_contents,
            "generation_config": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "max_output_tokens": self.max_tokens,
            },
            "safety_settings": self.safety_settings
        }
        
        # Add tools if available
        if self.available_tools:
            # Convert tools to Gemini format if needed
            gemini_tools = self._convert_tools_to_gemini_format(self.available_tools)
            request_data["tools"] = gemini_tools
            
            # Add tool config
            if self.tool_choice != "auto":
                if self.tool_choice == "none":
                    request_data["tool_config"] = {
                        "function_calling_config": {"mode": "NONE"}
                    }
                elif self.tool_choice == "any":
                    request_data["tool_config"] = {
                        "function_calling_config": {"mode": "ANY"}
                    }
        
        return request_data
    
    def _convert_tools_to_gemini_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert tools to Gemini format"""
        gemini_tools = []
        
        for tool in tools:
            if 'function_declarations' in tool:
                # Already in Gemini format
                gemini_tools.append(tool)
            else:
                # Convert from OpenAI format
                function = tool['function']
                gemini_tool = {
                    "function_declarations": [{
                        "name": function['name'],
                        "description": function['description'],
                        "parameters": function.get('parameters', {})
                    }]
                }
                gemini_tools.append(gemini_tool)
        
        return gemini_tools
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI API format for compatibility"""
        openai_messages = []
        
        for message in self.messages:
            openai_message = {
                "role": "assistant" if message.role == "model" else message.role,
                "content": message.content or ""
            }
            
            if message.tool_calls:
                openai_message["tool_calls"] = []
                for tool_call in message.tool_calls:
                    openai_message["tool_calls"].append({
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.name,
                            "arguments": json.dumps(tool_call.parameters) if tool_call.parameters else "{}"
                        }
                    })
            
            if message.tool_call_id:
                openai_message["tool_call_id"] = message.tool_call_id
            
            openai_messages.append(openai_message)
        
        # Add current user input if not already in messages
        if not openai_messages or openai_messages[-1]["role"] != "user":
            openai_messages.append({
                "role": "user",
                "content": self.user_input
            })
        
        # Convert tools to OpenAI format
        openai_tools = []
        for tool in self.available_tools:
            if 'function_declarations' in tool:
                for func_decl in tool['function_declarations']:
                    openai_tools.append({
                        "type": "function",
                        "function": func_decl
                    })
            else:
                openai_tools.append(tool)
        
        return {
            "model": self.model,
            "messages": openai_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "tools": openai_tools if openai_tools else None,
            "tool_choice": self.tool_choice if openai_tools else None,
            "parallel_tool_calls": self.parallel_tool_calls
        }
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
