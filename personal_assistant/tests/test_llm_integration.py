"""Tests for LLM Integration Module"""

import pytest
from unittest.mock import Mock, patch
from personal_assistant.modules.llm_integration.main import (
    ModelType,
    ModelConfig,
    LLMManager,
    OpenAIProvider,
    AnthropicProvider,
    OpenRouterProvider,
    GoogleProvider,
    SelfHostedProvider
)

def test_model_config():
    """Test model configuration"""
    config = ModelConfig(
        provider=ModelType.OPENAI,
        model_name="gpt-4",
        api_key="test-key",
        temperature=0.8,
        max_tokens=1024
    )
    assert config.provider == ModelType.OPENAI
    assert config.model_name == "gpt-4"
    assert config.api_key == "test-key"
    assert config.temperature == 0.8
    assert config.max_tokens == 1024

@patch('requests.post')
def test_openai_provider(mock_post):
    """Test OpenAI provider implementation"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Test response"}}],
        "usage": {"total_tokens": 10}
    }
    mock_post.return_value = mock_response

    config = ModelConfig(
        provider=ModelType.OPENAI,
        model_name="gpt-4",
        api_key="test-key"
    )
    provider = OpenAIProvider(config)
    result = provider.generate_text("Test prompt")

    assert result["success"] is True
    assert result["text"] == "Test response"
    assert "usage" in result

@patch('requests.post')
def test_anthropic_provider(mock_post):
    """Test Anthropic provider implementation"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "content": [{"text": "Test response"}],
        "usage": {"total_tokens": 10}
    }
    mock_post.return_value = mock_response

    config = ModelConfig(
        provider=ModelType.ANTHROPIC,
        model_name="claude-3",
        api_key="test-key"
    )
    provider = AnthropicProvider(config)
    result = provider.generate_text("Test prompt")

    assert result["success"] is True
    assert result["text"] == "Test response"
    assert "usage" in result

@patch('requests.post')
def test_openrouter_provider(mock_post):
    """Test OpenRouter provider implementation"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Test response"}}],
        "usage": {"total_tokens": 10}
    }
    mock_post.return_value = mock_response

    config = ModelConfig(
        provider=ModelType.OPENROUTER,
        model_name="openai/gpt-4",
        api_key="test-key"
    )
    provider = OpenRouterProvider(config)
    result = provider.generate_text("Test prompt")

    assert result["success"] is True
    assert result["text"] == "Test response"
    assert "usage" in result

@patch('requests.post')
def test_google_provider(mock_post):
    """Test Google provider implementation"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Test response"}]}}],
        "usage": {"total_tokens": 10}
    }
    mock_post.return_value = mock_response

    config = ModelConfig(
        provider=ModelType.GOOGLE,
        model_name="gemini-pro",
        api_key="test-key"
    )
    provider = GoogleProvider(config)
    result = provider.generate_text("Test prompt")

    assert result["success"] is True
    assert result["text"] == "Test response"
    assert "usage" in result

@patch('requests.post')
def test_self_hosted_provider(mock_post):
    """Test self-hosted provider implementation"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "text": "Test response",
        "usage": {"total_tokens": 10}
    }
    mock_post.return_value = mock_response

    config = ModelConfig(
        provider=ModelType.SELF_HOSTED,
        model_name="local-model",
        api_key="test-key",
        api_base="http://localhost:8000"
    )
    provider = SelfHostedProvider(config)
    result = provider.generate_text("Test prompt")

    assert result["success"] is True
    assert result["text"] == "Test response"
    assert "usage" in result

def test_llm_manager_provider_selection():
    """Test LLM manager provider selection"""
    providers = [
        (ModelType.OPENAI, OpenAIProvider),
        (ModelType.ANTHROPIC, AnthropicProvider),
        (ModelType.OPENROUTER, OpenRouterProvider),
        (ModelType.GOOGLE, GoogleProvider),
        (ModelType.SELF_HOSTED, SelfHostedProvider)
    ]

    for provider_type, provider_class in providers:
        config = ModelConfig(
            provider=provider_type,
            model_name="test-model",
            api_key="test-key"
        )
        manager = LLMManager(config)
        provider = manager._get_provider(config)
        assert isinstance(provider, provider_class)

def test_llm_manager_load_model():
    """Test LLM manager model loading"""
    config = ModelConfig(
        provider=ModelType.OPENAI,
        model_name="gpt-4",
        api_key="test-key"
    )
    
    manager = LLMManager()
    result = manager.load_model(config)
    
    assert result["success"] is True
    assert "model_info" in result
    assert manager.provider is not None

def test_llm_manager_generate_text():
    """Test LLM manager text generation"""
    config = ModelConfig(
        provider=ModelType.OPENAI,
        model_name="gpt-4",
        api_key="test-key"
    )
    
    manager = LLMManager(config)
    manager.load_model()
    
    result = manager.generate_text("Test prompt")
    assert result["success"] is True
    assert "text" in result

def test_invalid_provider():
    """Test handling of invalid provider"""
    with pytest.raises(ValueError):
        config = ModelConfig(
            provider=ModelType.OPENAI,
            model_name="test-model",
            api_key="test-key"
        )
        manager = LLMManager(config)
        # Attempt to use an invalid provider type
        invalid_config = ModelConfig(
            provider="invalid",  # type: ignore
            model_name="test-model",
            api_key="test-key"
        )
        manager._get_provider(invalid_config)
