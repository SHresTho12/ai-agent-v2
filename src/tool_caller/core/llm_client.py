# src/llm_tool_caller/core/llm_client.py
import logging
from typing import Dict, List, Any, Optional

from openai import AsyncOpenAI
import google.generativeai as genai
from google.generativeai import types
from google.generativeai.protos import FunctionDeclaration


from ..config.settings import get_settings
from ..models.requests import LLMRequest
from ..models.responses import LLMResponse

logger = logging.getLogger(__name__)

class LLMClient:
    """Handles LLM communication and tool calling decisions"""

    def __init__(self, provider: Optional[str] = None):
        
        self.settings = get_settings()
        self.provider = provider or self.settings.default_llm_provider
        llm_config = self.settings.llms.get(provider)

        if not llm_config:
            logger.error(f"LLM provider {provider} not configured")
            raise ValueError(f"LLM provider {provider} not configured")

        self.model = llm_config.model
        self.temperature = llm_config.temperature
        
        # Initialize the correct client based on the provider
        if self.provider == "openai":
            self.client = AsyncOpenAI(api_key=llm_config.api_key)
        elif self.provider == "gemini":
            genai.configure(api_key=llm_config.api_key)
            self.client = genai.GenerativeModel(
                model_name=self.model,
                generation_config=types.GenerationConfig(temperature=self.temperature)
            )
        else:
            logger.error(f"Unsupported LLM provider: {provider}")
            raise ValueError(f"Unsupported LLM provider: {provider}")

##This function should be more refactored factory pattern or abstract factory 

    async def process_user_input(
        self, 
        user_input: str, 
        available_tools: List[Dict[str, Any]]
    ) -> LLMResponse:
        """Process user input and determine tool calls"""
        try:
            if self.provider == "openai":
                messages = [
                    {"role": "system", "content": "You are a helpful assistant that can call tools."},
                    {"role": "user", "content": user_input}
                ]
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=available_tools,
                    tool_choice="auto",
                    temperature=self.temperature
                )
                return LLMResponse.from_openai_response(response)
            
            elif self.provider == "gemini":

                response = self._process_gemini(user_input, available_tools)

                # Placeholder for parsing Gemini's response for tool calls
                return self._parse_gemini_response(response)

        except Exception as e:
            logger.error(f"[{self.provider}] LLM processing error: {e}")
            raise

            
    
    
    
    
    
    async def _process_gemini(
        self,
        user_input: str,
        available_tools: List[Dict[str, Any]]
    ) -> LLMResponse:
        """ Process with Gemini"""
        
        try:                # Convert tools to Gemini's format
            tools_for_gemini = [
                FunctionDeclaration(
                    name=tool["function"]["name"],
                    description=tool["function"]["description"],
                    parameters=types.FunctionDeclaration.Schema(
                        type=types.FunctionDeclaration.Schema.Type.OBJECT,
                        properties={
                            k: types.FunctionDeclaration.Schema(
                                type=types.FunctionDeclaration.Schema.Type.STRING
                                # This is a simplified example, you'll need to map other types
                            ) for k in tool["function"]["parameters"]["properties"]
                        },
                        required=tool["function"]["parameters"]["required"]
                    )
                ) for tool in available_tools
            ]
        except Exception as e:
            logger.error(f"Error converting tools for Gemini: {e}")
            raise
        
        chat = self.client.start_chat(history=[])
        response = await chat.send_message_async(
            user_input,
            tools=tools_for_gemini,
            generation_config=genai.types.GenerationConfig(
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
            )
        )
        return response
    
            
            
            
            
    
    async def generate_final_response(
        self, 
        user_input: str, 
        tool_results: List[Dict[str, Any]]
    ) -> str:
        """Generate final response based on tool results"""
        if self.provider == "gemini":
            return await self._generate_final_response_gemini(user_input, tool_results)
        elif self.provider == "openai":
            return await self._generate_final_response_openai(user_input, tool_results)
        elif self.provider == "anthropic":
            return await self._generate_final_response_anthropic(user_input, tool_results)

    async def _generate_final_response_gemini(
        self, 
        user_input: str, 
        tool_results: List[Dict[str, Any]]
    ) -> str:
        """Generate final response using Gemini"""
        context = f"User asked: {user_input}\n"
        context += "Tool results:\n"
        for result in tool_results:
            context += f"- {result}\n"
        context += "\nProvide a helpful response based on this information."
        
        response = await self.client.generate_content_async(context)
        return response.text

    async def _generate_final_response_openai(
        self, 
        user_input: str, 
        tool_results: List[Dict[str, Any]]
    ) -> str:
        """Generate final response using OpenAI"""
        # Implementation for OpenAI final response
        pass

    async def _generate_final_response_anthropic(
        self, 
        user_input: str, 
        tool_results: List[Dict[str, Any]]
    ) -> str:
        """Generate final response using Anthropic"""
        # Implementation for Anthropic final response
        pass
