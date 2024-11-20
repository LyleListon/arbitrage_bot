"""
Demo script showing how to use different LLM providers
"""

from personal_assistant.modules.llm_integration.main import (
    ModelType,
    ModelConfig,
    LLMManager
)

def demo_openai():
    """Demo OpenAI provider usage"""
    config = ModelConfig(
        provider=ModelType.OPENAI,
        model_name="gpt-4",
        api_key="your-openai-key",  # Replace with actual API key
        temperature=0.7
    )
    
    manager = LLMManager(config)
    result = manager.load_model()
    
    if result["success"]:
        print(f"Successfully loaded OpenAI model: {result['model_info']}")
        response = manager.generate_text("What is the capital of France?")
        if response["success"]:
            print(f"Response: {response['text']}")
        else:
            print(f"Error: {response['error']}")
    else:
        print(f"Error loading model: {result['error']}")

def demo_anthropic():
    """Demo Anthropic provider usage"""
    config = ModelConfig(
        provider=ModelType.ANTHROPIC,
        model_name="claude-3-opus-20240229",
        api_key="your-anthropic-key",  # Replace with actual API key
        temperature=0.7
    )
    
    manager = LLMManager(config)
    result = manager.load_model()
    
    if result["success"]:
        print(f"Successfully loaded Anthropic model: {result['model_info']}")
        response = manager.generate_text("Explain quantum computing in simple terms.")
        if response["success"]:
            print(f"Response: {response['text']}")
        else:
            print(f"Error: {response['error']}")
    else:
        print(f"Error loading model: {result['error']}")

def demo_openrouter():
    """Demo OpenRouter provider usage"""
    config = ModelConfig(
        provider=ModelType.OPENROUTER,
        model_name="anthropic/claude-3-opus",  # OpenRouter model identifier
        api_key="your-openrouter-key",  # Replace with actual API key
        temperature=0.7
    )
    
    manager = LLMManager(config)
    result = manager.load_model()
    
    if result["success"]:
        print(f"Successfully loaded OpenRouter model: {result['model_info']}")
        response = manager.generate_text("Write a short poem about coding.")
        if response["success"]:
            print(f"Response: {response['text']}")
        else:
            print(f"Error: {response['error']}")
    else:
        print(f"Error loading model: {result['error']}")

def demo_google():
    """Demo Google provider usage"""
    config = ModelConfig(
        provider=ModelType.GOOGLE,
        model_name="gemini-pro",
        api_key="your-google-key",  # Replace with actual API key
        temperature=0.7
    )
    
    manager = LLMManager(config)
    result = manager.load_model()
    
    if result["success"]:
        print(f"Successfully loaded Google model: {result['model_info']}")
        response = manager.generate_text("What are the benefits of renewable energy?")
        if response["success"]:
            print(f"Response: {response['text']}")
        else:
            print(f"Error: {response['error']}")
    else:
        print(f"Error loading model: {result['error']}")

def demo_self_hosted():
    """Demo self-hosted provider usage"""
    config = ModelConfig(
        provider=ModelType.SELF_HOSTED,
        model_name="local-model",
        api_key="optional-key",  # Optional for self-hosted models
        api_base="http://localhost:8000",  # Replace with your model's endpoint
        temperature=0.7,
        custom_params={
            "stream": True,  # Example custom parameter
            "stop_sequences": ["\n", "###"]
        }
    )
    
    manager = LLMManager(config)
    result = manager.load_model()
    
    if result["success"]:
        print(f"Successfully loaded self-hosted model: {result['model_info']}")
        response = manager.generate_text("Explain how to make a pizza.")
        if response["success"]:
            print(f"Response: {response['text']}")
        else:
            print(f"Error: {response['error']}")
    else:
        print(f"Error loading model: {result['error']}")

def main():
    """Run demos for different LLM providers"""
    print("\n=== OpenAI Demo ===")
    demo_openai()
    
    print("\n=== Anthropic Demo ===")
    demo_anthropic()
    
    print("\n=== OpenRouter Demo ===")
    demo_openrouter()
    
    print("\n=== Google Demo ===")
    demo_google()
    
    print("\n=== Self-hosted Demo ===")
    demo_self_hosted()

if __name__ == "__main__":
    main()
