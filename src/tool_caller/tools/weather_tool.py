import aiohttp
import asyncio
import time
import logging
from typing import Dict, Any
from ..tools.base import BaseTool, ToolResponse, ToolSchema
from ..config.settings import get_settings

logger = logging.getLogger(__name__)

class WeatherTool(BaseTool):
    """Tool for fetching weather information"""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.weather_api_key
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
    
    @property
    def name(self) -> str:
        return "get_weather"
    
    @property
    def description(self) -> str:
        return "Get current weather information for a specific location"
    
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or city, country"
                    },
                    "units": {
                        "type": "string",
                        "enum": ["metric", "imperial", "kelvin"],
                        "description": "Temperature units",
                        "default": "metric"
                    }
                },
                "required": ["location"]
            }
        )
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate input parameters"""
        if "location" not in parameters:
            return False
        
        if not isinstance(parameters["location"], str):
            return False
        
        units = parameters.get("units", "metric")
        if units not in ["metric", "imperial", "kelvin"]:
            return False
        
        return True
    
    async def _run(self, **kwargs) -> Any:
        """Core logic for fetching weather data."""
        location = kwargs["location"]
        units = kwargs.get("units", "metric")
        
        params = {
            "q": location,
            "appid": self.api_key,
            "units": units
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "location": data["name"],
                        "country": data["sys"]["country"],
                        "temperature": data["main"]["temp"],
                        "feels_like": data["main"]["feels_like"],
                        "humidity": data["main"]["humidity"],
                        "description": data["weather"][0]["description"],
                        "units": units
                    }
                else:
                    error_data = await response.json()
                    logger.error(f"Weather API error: {error_data.get('message', 'Unknown error')}")
                    raise RuntimeError(f"Weather API error: {error_data.get('message', 'Unknown error')}")