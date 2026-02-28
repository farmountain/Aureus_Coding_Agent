"""Model Provider package - Pluggable LLM backends for AUREUS"""

from src.model_provider.base import (
    ModelProvider,
    BaseModelProvider,
    MockProvider,
    ProviderRegistry,
    ModelResponse
)

# Import real providers (lazy load to handle missing dependencies)
try:
    from src.model_provider.openai_provider import OpenAIProvider
except ImportError:
    OpenAIProvider = None

try:
    from src.model_provider.anthropic_provider import AnthropicProvider
except ImportError:
    AnthropicProvider = None

__all__ = [
    "ModelProvider",
    "BaseModelProvider",
    "MockProvider",
    "ProviderRegistry",
    "ModelResponse",
    "OpenAIProvider",
    "AnthropicProvider"
]
