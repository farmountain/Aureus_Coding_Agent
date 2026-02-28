"""Simple OpenAI API wrapper"""

from typing import Optional
import os
import openai


class ModelResponse:
    def __init__(self, content: str, model: str, tokens_used: int):
        self.content = content
        self.model = model
        self.tokens_used = tokens_used


class OpenAIProvider:
    def __init__(self, model_name: str = "gpt-4o-mini", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY required")
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def complete(self, prompt: str, **kwargs) -> ModelResponse:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens
        
        return ModelResponse(
            content=content,
            model=self.model_name,
            tokens_used=tokens
        )
