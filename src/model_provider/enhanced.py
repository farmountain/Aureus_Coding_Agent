"""
Enhanced Model Provider with Streaming, Token Counting, and Error Handling

Improvements:
- Accurate token counting using tiktoken
- Streaming with error recovery
- Retry logic with exponential backoff
- Better error handling and logging
"""

from typing import Iterator, Optional, Callable
import time
import re
from dataclasses import dataclass
from src.model_provider.base import ModelResponse, BaseModelProvider


@dataclass
class TokenCountEstimate:
    """Token count estimation result"""
    tokens: int
    method: str  # 'tiktoken', 'estimate', 'character_based'
    accurate: bool  # True if using tiktoken


class EnhancedTokenCounter:
    """
    Enhanced token counting with tiktoken support
    
    Falls back to estimation if tiktoken not available
    """
    
    def __init__(self, model: str = "gpt-4"):
        self.model = model
        self._tiktoken_available = False
        self._encoding = None
        
        # Try to import tiktoken
        try:
            import tiktoken
            self._encoding = tiktoken.encoding_for_model(model)
            self._tiktoken_available = True
        except (ImportError, KeyError):
            # tiktoken not available or model not supported
            pass
    
    def count_tokens(self, text: str) -> TokenCountEstimate:
        """
        Count tokens in text with accuracy indicator
        
        Args:
            text: Text to tokenize
            
        Returns:
            TokenCountEstimate with count and method
        """
        if self._tiktoken_available and self._encoding:
            # Accurate tiktoken count
            tokens = len(self._encoding.encode(text))
            return TokenCountEstimate(
                tokens=tokens,
                method='tiktoken',
                accurate=True
            )
        else:
            # Estimation fallback
            tokens = self._estimate_tokens(text)
            return TokenCountEstimate(
                tokens=tokens,
                method='estimate',
                accurate=False
            )
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count using heuristics
        
        Rule of thumb:
        - English: ~1 token per 4 characters
        - Code: ~1 token per 3 characters
        - Punctuation increases token count
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Base estimate: 1 token per 4 characters
        char_estimate = len(text) / 4
        
        # Adjust for code (more tokens)
        code_indicators = ['def ', 'class ', 'import ', '{', '}', '=>', '()']
        if any(indicator in text for indicator in code_indicators):
            char_estimate *= 1.2
        
        # Adjust for punctuation
        punctuation_count = sum(1 for c in text if c in '.,!?;:')
        punctuation_adjustment = punctuation_count * 0.3
        
        # Adjust for whitespace (each space/newline is often a token boundary)
        whitespace_count = sum(1 for c in text if c.isspace())
        whitespace_adjustment = whitespace_count * 0.1
        
        total = char_estimate + punctuation_adjustment + whitespace_adjustment
        return int(total)


class StreamingError(Exception):
    """Raised when streaming fails"""
    pass


class EnhancedStreamHandler:
    """
    Enhanced streaming with error recovery
    
    Features:
    - Chunk buffering
    - Error recovery
    - Timeout handling
    - Progress callbacks
    """
    
    def __init__(
        self,
        timeout: float = 30.0,
        buffer_size: int = 10,
        on_chunk: Optional[Callable[[str], None]] = None
    ):
        self.timeout = timeout
        self.buffer_size = buffer_size
        self.on_chunk = on_chunk
        self._buffer = []
    
    def stream_with_recovery(
        self,
        stream_func: Callable[[], Iterator[str]],
        max_retries: int = 3
    ) -> Iterator[str]:
        """
        Stream with automatic retry on failure
        
        Args:
            stream_func: Function that returns stream iterator
            max_retries: Maximum retry attempts
            
        Yields:
            Content chunks
            
        Raises:
            StreamingError: If all retries exhausted
        """
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                stream = stream_func()
                
                for chunk in stream:
                    # Buffer chunk
                    self._buffer.append(chunk)
                    
                    # Call progress callback
                    if self.on_chunk:
                        self.on_chunk(chunk)
                    
                    yield chunk
                
                # Success - clear buffer and return
                self._buffer.clear()
                return
                
            except Exception as e:
                retry_count += 1
                
                if retry_count >= max_retries:
                    raise StreamingError(
                        f"Streaming failed after {max_retries} retries: {e}"
                    )
                
                # Exponential backoff
                wait_time = 2 ** retry_count
                time.sleep(wait_time)
    
    def get_buffer(self) -> str:
        """Get buffered content"""
        return ''.join(self._buffer)


class RetryConfig:
    """Configuration for retry logic"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt"""
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)


class EnhancedModelProvider(BaseModelProvider):
    """
    Enhanced model provider with advanced features
    
    Features:
    - Accurate token counting (tiktoken)
    - Streaming with retry
    - Error handling with exponential backoff
    - Request/response logging
    """
    
    def __init__(
        self,
        model_name: str,
        api_key: Optional[str] = None,
        retry_config: Optional[RetryConfig] = None
    ):
        super().__init__(model_name, api_key)
        self.token_counter = EnhancedTokenCounter(model_name)
        self.retry_config = retry_config or RetryConfig()
        self._request_log = []
    
    def complete_with_retry(
        self,
        prompt: str,
        **kwargs
    ) -> ModelResponse:
        """
        Complete prompt with automatic retry
        
        Args:
            prompt: Input prompt
            **kwargs: Provider-specific options
            
        Returns:
            ModelResponse
            
        Raises:
            Exception: If all retries exhausted
        """
        last_error = None
        
        for attempt in range(self.retry_config.max_retries):
            try:
                response = self.complete(prompt, **kwargs)
                
                # Log successful request
                self._log_request(prompt, response, attempt)
                
                return response
                
            except Exception as e:
                last_error = e
                
                if attempt < self.retry_config.max_retries - 1:
                    # Wait before retry
                    delay = self.retry_config.get_delay(attempt)
                    time.sleep(delay)
                else:
                    # Last attempt failed
                    raise last_error
        
        raise last_error
    
    def stream_with_recovery(
        self,
        prompt: str,
        on_chunk: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        Stream with automatic recovery
        
        Args:
            prompt: Input prompt
            on_chunk: Callback for each chunk
            **kwargs: Provider-specific options
            
        Yields:
            Content chunks
        """
        handler = EnhancedStreamHandler(on_chunk=on_chunk)
        
        def create_stream():
            return self.stream(prompt, **kwargs)
        
        yield from handler.stream_with_recovery(
            create_stream,
            max_retries=self.retry_config.max_retries
        )
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using enhanced counter"""
        estimate = self.token_counter.count_tokens(text)
        return estimate.tokens
    
    def get_token_estimate(self, text: str) -> TokenCountEstimate:
        """
        Get detailed token estimate
        
        Args:
            text: Text to estimate
            
        Returns:
            TokenCountEstimate with accuracy info
        """
        return self.token_counter.count_tokens(text)
    
    def _log_request(self, prompt: str, response: ModelResponse, attempt: int):
        """Log request for debugging"""
        self._request_log.append({
            'timestamp': time.time(),
            'prompt_length': len(prompt),
            'response_length': len(response.content),
            'tokens_used': response.tokens_used,
            'attempt': attempt,
            'model': self.model_name
        })
    
    def get_request_log(self) -> list:
        """Get request log for analysis"""
        return self._request_log.copy()
    
    def clear_log(self):
        """Clear request log"""
        self._request_log.clear()


class EnhancedMockProvider(EnhancedModelProvider):
    """
    Enhanced mock provider for testing
    
    Includes all enhanced features with deterministic responses
    """
    
    def __init__(
        self,
        model_name: str = "mock-enhanced",
        responses: Optional[dict] = None
    ):
        super().__init__(model_name)
        self.responses = responses or {"default": "Enhanced mock response"}
        self.call_count = 0
    
    def complete(self, prompt: str, **kwargs) -> ModelResponse:
        """Return canned response"""
        self.call_count += 1
        
        # Find matching response
        content = self.responses.get(
            prompt,
            self.responses.get("default", "Mock response")
        )
        
        # Use enhanced token counter
        token_estimate = self.token_counter.count_tokens(prompt + content)
        
        return ModelResponse(
            content=content,
            model=self.model_name,
            tokens_used=token_estimate.tokens,
            finish_reason="stop",
            metadata={
                "call_count": self.call_count,
                "token_method": token_estimate.method,
                "token_accurate": token_estimate.accurate
            }
        )
    
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Stream response word by word"""
        response = self.complete(prompt, **kwargs)
        words = response.content.split()
        
        for word in words:
            yield word + " "
