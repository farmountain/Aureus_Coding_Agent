"""
Anthropic Model Provider for AUREUS

Implements ModelProvider protocol using Anthropic API (Claude models)
"""

from typing import Iterator, Optional
import os
from src.model_provider.base import BaseModelProvider, ModelResponse


class AnthropicProvider(BaseModelProvider):
    """
    Anthropic API provider
    
    Supports Claude models (claude-3-opus, claude-3-sonnet, claude-3-haiku).
    Requires ANTHROPIC_API_KEY environment variable or api_key parameter.
    """
    
    def __init__(
        self,
        model_name: str = "claude-3-sonnet-20240229",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        """
        Initialize Anthropic provider
        
        Args:
            model_name: Claude model name (default: claude-3-sonnet-20240229)
            api_key: API key (defaults to ANTHROPIC_API_KEY env var)
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens in response
        """
        super().__init__(model_name, api_key or os.getenv("ANTHROPIC_API_KEY"))
        
        if not self.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.")
        
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Lazy import anthropic to avoid dependency if not used
        try:
            import anthropic
            self.anthropic = anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    def complete(self, prompt: str, **kwargs) -> ModelResponse:
        """
        Complete a prompt using Anthropic API
        
        Args:
            prompt: Input prompt
            **kwargs: Additional Anthropic parameters (temperature, max_tokens, etc.)
        
        Returns:
            ModelResponse with completion
        """
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract content from first content block
            content = response.content[0].text if response.content else ""
            finish_reason = response.stop_reason
            
            # Calculate tokens (Anthropic returns input/output tokens)
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            return ModelResponse(
                content=content,
                model=self.model_name,
                tokens_used=tokens_used,
                finish_reason=finish_reason,
                metadata={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            )
        
        except self.anthropic.RateLimitError as e:
            return ModelResponse(
                content="",
                model=self.model_name,
                tokens_used=0,
                finish_reason="error",
                metadata={"error": "rate_limit", "message": str(e)}
            )
        except self.anthropic.APIError as e:
            return ModelResponse(
                content="",
                model=self.model_name,
                tokens_used=0,
                finish_reason="error",
                metadata={"error": "api_error", "message": str(e)}
            )
        except Exception as e:
            return ModelResponse(
                content="",
                model=self.model_name,
                tokens_used=0,
                finish_reason="error",
                metadata={"error": "unknown", "message": str(e)}
            )
    
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """
        Stream completion chunks from Anthropic API
        
        Args:
            prompt: Input prompt
            **kwargs: Additional Anthropic parameters
        
        Yields:
            Content chunks as they arrive
        """
        try:
            with self.client.messages.stream(
                model=self.model_name,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for text in stream.text_stream:
                    yield text
        
        except Exception as e:
            yield f"[ERROR: {str(e)}]"
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text
        
        Note: Anthropic uses their own tokenizer. This is a rough estimation.
        For accurate counts, use the Anthropic API's token counting endpoint.
        
        Args:
            text: Text to tokenize
        
        Returns:
            Estimated token count
        """
        try:
            # Try to use anthropic's token counting if available
            response = self.client.messages.count_tokens(
                model=self.model_name,
                messages=[{"role": "user", "content": text}]
            )
            return response.input_tokens
        except:
            # Fallback: rough estimation (1 token ≈ 4 characters for English)
            # Claude uses a similar tokenization to GPT
            return len(text) // 4
