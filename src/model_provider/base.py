"""
Model Provider Abstraction - AUREUS Phase 1

Provides pluggable model provider interface supporting:
- Anthropic (Claude)
- OpenAI (GPT-4, o1)
- Google (Gemini)
- Local LLMs (Ollama, LM Studio)

Phase 1: MockProvider for testing
Phase 2: Claude and OpenAI adapters
"""

from typing import Protocol, Iterator, Dict, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ModelResponse:
    """Response from model provider"""
    content: str
    model: str
    tokens_used: int
    finish_reason: str = "stop"  # stop | length | error
    metadata: Dict[str, Any] = field(default_factory=dict)


class ModelProvider(Protocol):
    """
    Protocol for model providers (pluggable LLM backends)
    
    All providers must implement these methods to be compatible
    with AUREUS agents.
    """
    
    def complete(self, prompt: str, **kwargs) -> ModelResponse:
        """
        Complete a prompt and return full response
        
        Args:
            prompt: Input text to complete
            **kwargs: Provider-specific options (temperature, max_tokens, etc.)
        
        Returns:
            ModelResponse with content and metadata
        """
        ...
    
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """
        Stream completion chunks (for interactive use)
        
        Args:
            prompt: Input text to complete
            **kwargs: Provider-specific options
        
        Yields:
            Content chunks as they arrive
        """
        ...
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text (for cost estimation)
        
        Args:
            text: Text to tokenize
        
        Returns:
            Token count
        """
        ...


class BaseModelProvider(ABC):
    """
    Abstract base class for model providers
    
    Provides common functionality for all providers
    """
    
    def __init__(self, model_name: str, api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key
    
    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> ModelResponse:
        """Implement completion logic"""
        pass
    
    @abstractmethod
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Implement streaming logic"""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Implement token counting"""
        pass


class MockProvider(BaseModelProvider):
    """
    Mock provider for testing (Phase 1)
    
    Returns deterministic canned responses for testing.
    No actual LLM calls made.
    """
    
    def __init__(self, model_name: str = "mock-model", responses: Optional[Dict[str, str]] = None):
        super().__init__(model_name)
        self.responses = responses or {
            "default": "Mock response from test provider"
        }
        self.call_count = 0
    
    def complete(self, prompt: str, **kwargs) -> ModelResponse:
        """Return canned response based on prompt"""
        self.call_count += 1
        
        # Check for exact match
        if prompt in self.responses:
            content = self.responses[prompt]
        # Check for keyword match
        else:
            content = self._find_matching_response(prompt)
        
        # Simulate token usage (rough estimate: 1 token per 4 characters)
        tokens_used = len(prompt + content) // 4
        
        return ModelResponse(
            content=content,
            model=self.model_name,
            tokens_used=tokens_used,
            finish_reason="stop",
            metadata={"call_count": self.call_count}
        )
    
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Stream canned response word by word"""
        response = self.complete(prompt, **kwargs)
        words = response.content.split()
        
        for word in words:
            yield word + " "
    
    def count_tokens(self, text: str) -> int:
        """Estimate tokens (1 token per 4 characters)"""
        return len(text) // 4
    
    def _find_matching_response(self, prompt: str) -> str:
        """Find response with matching keyword"""
        prompt_lower = prompt.lower()
        
        for key, response in self.responses.items():
            if key.lower() in prompt_lower:
                return response
        
        # Default response
        return self.responses.get("default", "Mock response")


class ProviderRegistry:
    """
    Registry for model providers
    
    Allows runtime selection and swapping of providers
    """
    
    def __init__(self):
        self._providers: Dict[str, ModelProvider] = {}
        self._default_provider: Optional[str] = None
    
    def register(self, name: str, provider: ModelProvider, set_default: bool = False):
        """
        Register a provider
        
        Args:
            name: Provider identifier
            provider: Provider instance
            set_default: Make this the default provider
        """
        self._providers[name] = provider
        
        if set_default or self._default_provider is None:
            self._default_provider = name
    
    def get(self, name: Optional[str] = None) -> ModelProvider:
        """
        Get provider by name, or default provider
        
        Args:
            name: Provider name (None for default)
        
        Returns:
            Provider instance
        
        Raises:
            KeyError: If provider not found
        """
        if name is None:
            name = self._default_provider
        
        if name is None:
            raise ValueError("No default provider set")
        
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' not registered")
        
        return self._providers[name]
    
    def list_providers(self) -> list[str]:
        """List all registered provider names"""
        return list(self._providers.keys())
    
    def set_default(self, name: str):
        """Set default provider"""
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' not registered")
        self._default_provider = name
