"""LLM Integration Module
Handles integration with local and cloud language models
"""

from typing import Dict, Any, Optional, List, Union, Protocol, runtime_checkable
import json
import logging
import os
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import requests
from abc import ABC, abstractmethod

class ModelType(Enum):
    """Supported LLM providers and models"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    GOOGLE = "google"
    SELF_HOSTED = "self_hosted"

@dataclass
class ModelConfig:
    """Configuration for LLM model"""
    provider: ModelType
    model_name: str
    api_key: str
    api_base: Optional[str] = None
    context_length: int = 4096
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 512
    custom_params: Dict[str, Any] = field(default_factory=dict)

@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM providers"""
    config: ModelConfig
    logger: logging.Logger

    def generate_text(self, prompt: str) -> Dict[str, Any]:
        """Generate text using the provider's API"""
        ...

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        ...

class BaseLLMProvider:
    """Base class for LLM providers"""
    def __init__(self, config: ModelConfig):
        self.config = config
        self.logger = logging.getLogger(f"llm_provider_{config.provider.value}")

    def generate_text(self, prompt: str) -> Dict[str, Any]:
        """Base implementation - should be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement generate_text")

    def get_model_info(self) -> Dict[str, Any]:
        """Base implementation - should be overridden by subclasses"""
        raise NotImplementedError("Subclasses must implement get_model_info")

class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider implementation"""
    def generate_text(self, prompt: str) -> Dict[str, Any]:
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.config.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "top_p": self.config.top_p
            }

            api_base = self.config.api_base or "https://api.openai.com/v1"
            response = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "text": result["choices"][0]["message"]["content"],
                    "model": self.config.model_name,
                    "usage": result.get("usage", {})
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code} - {response.text}"
                }

        except Exception as e:
            self.logger.error(f"Error generating text: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_model_info(self) -> Dict[str, Any]:
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}"
            }
            
            api_base = self.config.api_base or "https://api.openai.com/v1"
            response = requests.get(
                f"{api_base}/models/{self.config.model_name}",
                headers=headers
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "model_info": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code} - {response.text}"
                }

        except Exception as e:
            self.logger.error(f"Error getting model info: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

class AnthropicProvider(BaseLLMProvider):
    """Anthropic API provider implementation"""
    def generate_text(self, prompt: str) -> Dict[str, Any]:
        try:
            headers = {
                "x-api-key": self.config.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            data = {
                "model": self.config.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "top_p": self.config.top_p
            }

            api_base = self.config.api_base or "https://api.anthropic.com/v1"
            response = requests.post(
                f"{api_base}/messages",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "text": result["content"][0]["text"],
                    "model": self.config.model_name,
                    "usage": result.get("usage", {})
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code} - {response.text}"
                }

        except Exception as e:
            self.logger.error(f"Error generating text: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "success": True,
            "model_info": {
                "name": self.config.model_name,
                "provider": "anthropic",
                "capabilities": ["chat", "completion"]
            }
        }

class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter API provider implementation"""
    def generate_text(self, prompt: str) -> Dict[str, Any]:
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.config.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "top_p": self.config.top_p
            }

            api_base = self.config.api_base or "https://openrouter.ai/api/v1"
            response = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "text": result["choices"][0]["message"]["content"],
                    "model": self.config.model_name,
                    "usage": result.get("usage", {})
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code} - {response.text}"
                }

        except Exception as e:
            self.logger.error(f"Error generating text: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_model_info(self) -> Dict[str, Any]:
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}"
            }
            
            api_base = self.config.api_base or "https://openrouter.ai/api/v1"
            response = requests.get(
                f"{api_base}/models",
                headers=headers
            )
            
            if response.status_code == 200:
                models = response.json()
                current_model = next(
                    (m for m in models if m["id"] == self.config.model_name),
                    None
                )
                return {
                    "success": True,
                    "model_info": current_model
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code} - {response.text}"
                }

        except Exception as e:
            self.logger.error(f"Error getting model info: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

class GoogleProvider(BaseLLMProvider):
    """Google API provider implementation"""
    def generate_text(self, prompt: str) -> Dict[str, Any]:
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.config.model_name,
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generation_config": {
                    "temperature": self.config.temperature,
                    "max_output_tokens": self.config.max_tokens,
                    "top_p": self.config.top_p
                }
            }

            api_base = self.config.api_base or "https://generativelanguage.googleapis.com/v1"
            response = requests.post(
                f"{api_base}/models/{self.config.model_name}:generateContent",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "text": result["candidates"][0]["content"]["parts"][0]["text"],
                    "model": self.config.model_name,
                    "usage": result.get("usage", {})
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code} - {response.text}"
                }

        except Exception as e:
            self.logger.error(f"Error generating text: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_model_info(self) -> Dict[str, Any]:
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}"
            }
            
            api_base = self.config.api_base or "https://generativelanguage.googleapis.com/v1"
            response = requests.get(
                f"{api_base}/models/{self.config.model_name}",
                headers=headers
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "model_info": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code} - {response.text}"
                }

        except Exception as e:
            self.logger.error(f"Error getting model info: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

class SelfHostedProvider(BaseLLMProvider):
    """Self-hosted model provider implementation"""
    def generate_text(self, prompt: str) -> Dict[str, Any]:
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            data = {
                "prompt": prompt,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "top_p": self.config.top_p,
                **self.config.custom_params
            }

            if not self.config.api_base:
                return {
                    "success": False,
                    "error": "API base URL is required for self-hosted models"
                }

            response = requests.post(
                f"{self.config.api_base}/generate",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "text": result["text"],
                    "model": self.config.model_name,
                    "usage": result.get("usage", {})
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code} - {response.text}"
                }

        except Exception as e:
            self.logger.error(f"Error generating text: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_model_info(self) -> Dict[str, Any]:
        try:
            headers = {}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            if not self.config.api_base:
                return {
                    "success": False,
                    "error": "API base URL is required for self-hosted models"
                }

            response = requests.get(
                f"{self.config.api_base}/model_info",
                headers=headers
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "model_info": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code} - {response.text}"
                }

        except Exception as e:
            self.logger.error(f"Error getting model info: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

class LLMManager:
    """Manager class for handling different LLM providers"""
    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config
        self.provider: Optional[LLMProvider] = None
        self.logger = logging.getLogger("llm_manager")
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging for LLM module"""
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.FileHandler("llm_manager.log")
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _get_provider(self, config: ModelConfig) -> LLMProvider:
        """Get the appropriate provider instance based on the configuration"""
        providers = {
            ModelType.OPENAI: OpenAIProvider,
            ModelType.ANTHROPIC: AnthropicProvider,
            ModelType.OPENROUTER: OpenRouterProvider,
            ModelType.GOOGLE: GoogleProvider,
            ModelType.SELF_HOSTED: SelfHostedProvider
        }
        
        provider_class = providers.get(config.provider)
        if not provider_class:
            raise ValueError(f"Unsupported provider: {config.provider}")
        
        return provider_class(config)

    def load_model(self, config: Optional[ModelConfig] = None) -> Dict[str, Any]:
        """Load a model with the specified configuration"""
        try:
            if config:
                self.config = config
            
            if not self.config:
                return {
                    "success": False,
                    "error": "No model configuration provided"
                }

            self.provider = self._get_provider(self.config)
            model_info = self.provider.get_model_info()
            
            if model_info["success"]:
                self.logger.info(f"Successfully loaded {self.config.model_name}")
                return {
                    "success": True,
                    "message": f"Successfully loaded {self.config.model_name}",
                    "model_info": model_info["model_info"]
                }
            else:
                return model_info

        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def generate_text(self, prompt: str) -> Dict[str, Any]:
        """Generate text using the loaded model"""
        try:
            if not self.provider:
                return {
                    "success": False,
                    "error": "No model loaded"
                }

            return self.provider.generate_text(prompt)

        except Exception as e:
            self.logger.error(f"Error generating text: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
