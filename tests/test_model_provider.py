"""
Tests for Model Provider interface

Tests MockProvider functionality and ProviderRegistry
Phase 2 will add Claude and OpenAI adapter tests
"""

import pytest
from src.model_provider import (
    MockProvider,
    ProviderRegistry,
    ModelResponse
)


class TestMockProvider:
    """Test the mock provider for testing"""
    
    def test_complete_with_default_response(self):
        """Test completion with default canned response"""
        provider = MockProvider()
        
        response = provider.complete("Test prompt")
        
        assert isinstance(response, ModelResponse)
        assert len(response.content) > 0
        assert response.model == "mock-model"
        assert response.tokens_used > 0
        assert response.finish_reason == "stop"
    
    def test_complete_with_custom_responses(self):
        """Test completion with custom canned responses"""
        custom_responses = {
            "What is 2+2?": "4",
            "hello": "Hello! How can I help you?",
            "default": "I don't understand"
        }
        
        provider = MockProvider(responses=custom_responses)
        
        # Exact match
        response = provider.complete("What is 2+2?")
        assert response.content == "4"
        
        # Keyword match
        response = provider.complete("Say hello to me")
        assert "Hello!" in response.content
        
        # Default fallback
        response = provider.complete("Unknown query")
        assert response.content == "I don't understand"
    
    def test_complete_tracks_call_count(self):
        """Test that provider tracks number of calls"""
        provider = MockProvider()
        
        assert provider.call_count == 0
        
        provider.complete("First call")
        assert provider.call_count == 1
        
        provider.complete("Second call")
        assert provider.call_count == 2
        
        response = provider.complete("Third call")
        assert response.metadata["call_count"] == 3
    
    def test_stream_returns_words(self):
        """Test streaming response word by word"""
        provider = MockProvider(responses={
            "test": "This is a test response"
        })
        
        chunks = list(provider.stream("test"))
        
        # Should split into words
        assert len(chunks) > 1
        assert all(isinstance(chunk, str) for chunk in chunks)
        
        # Reconstruct should match original
        reconstructed = "".join(chunks).strip()
        assert reconstructed == "This is a test response"
    
    def test_count_tokens_estimation(self):
        """Test token counting (rough estimation)"""
        provider = MockProvider()
        
        # Short text
        tokens = provider.count_tokens("Hello")
        assert tokens == 1  # 5 chars / 4 = 1
        
        # Longer text (100 characters = ~25 tokens)
        text = "This is a longer text that should use approximately twenty-five tokens when counted by the model"
        tokens = provider.count_tokens(text)
        assert tokens >= 20 and tokens <= 30
    
    def test_custom_model_name(self):
        """Test provider with custom model name"""
        provider = MockProvider(model_name="gpt-4-test")
        
        response = provider.complete("test")
        assert response.model == "gpt-4-test"


class TestProviderRegistry:
    """Test the provider registry"""
    
    def test_register_and_get_provider(self):
        """Test registering and retrieving providers"""
        registry = ProviderRegistry()
        mock = MockProvider(model_name="mock-1")
        
        registry.register("mock", mock)
        
        retrieved = registry.get("mock")
        assert retrieved is mock
    
    def test_register_sets_default(self):
        """Test that first registered provider becomes default"""
        registry = ProviderRegistry()
        mock = MockProvider()
        
        registry.register("mock", mock)
        
        # Should get default provider
        default = registry.get()
        assert default is mock
    
    def test_register_multiple_providers(self):
        """Test registering multiple providers"""
        registry = ProviderRegistry()
        mock1 = MockProvider(model_name="model-1")
        mock2 = MockProvider(model_name="model-2")
        
        registry.register("mock1", mock1)
        registry.register("mock2", mock2)
        
        assert registry.get("mock1").model_name == "model-1"
        assert registry.get("mock2").model_name == "model-2"
    
    def test_set_default_provider(self):
        """Test explicitly setting default provider"""
        registry = ProviderRegistry()
        mock1 = MockProvider(model_name="model-1")
        mock2 = MockProvider(model_name="model-2")
        
        registry.register("mock1", mock1)
        registry.register("mock2", mock2)
        
        # mock1 is default (registered first)
        assert registry.get().model_name == "model-1"
        
        # Change default to mock2
        registry.set_default("mock2")
        assert registry.get().model_name == "model-2"
    
    def test_list_providers(self):
        """Test listing all registered providers"""
        registry = ProviderRegistry()
        mock1 = MockProvider()
        mock2 = MockProvider()
        
        registry.register("mock1", mock1)
        registry.register("mock2", mock2)
        
        providers = registry.list_providers()
        assert "mock1" in providers
        assert "mock2" in providers
        assert len(providers) == 2
    
    def test_get_nonexistent_provider_raises_error(self):
        """Test that getting nonexistent provider raises error"""
        registry = ProviderRegistry()
        
        with pytest.raises(KeyError):
            registry.get("nonexistent")
    
    def test_set_default_nonexistent_raises_error(self):
        """Test that setting nonexistent default raises error"""
        registry = ProviderRegistry()
        
        with pytest.raises(KeyError):
            registry.set_default("nonexistent")
    
    def test_get_default_when_none_registered_raises_error(self):
        """Test that getting default with no providers raises error"""
        registry = ProviderRegistry()
        
        with pytest.raises(ValueError):
            registry.get()
