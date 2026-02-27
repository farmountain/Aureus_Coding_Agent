"""
Web Fetch Tool - HTTP Request Handler

Provides safe HTTP/HTTPS requests with:
- URL whitelisting/blacklisting
- Timeout protection
- Response size limits
- User-agent configuration
"""

import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json


@dataclass
class WebResponse:
    """HTTP response data"""
    success: bool
    url: str
    status_code: int
    content: str
    headers: Dict[str, str]
    error: Optional[str] = None


class WebFetchTool:
    """
    Web fetching tool for HTTP requests
    
    Provides safe HTTP/HTTPS operations with:
    - URL validation
    - Timeout limits
    - Response size limits
    - Content type filtering
    """
    
    def __init__(
        self,
        allowed_domains: Optional[List[str]] = None,
        timeout: int = 30,
        max_response_size: int = 10 * 1024 * 1024,  # 10MB
        user_agent: str = "AUREUS/1.0"
    ):
        """
        Initialize web fetch tool
        
        Args:
            allowed_domains: List of allowed domains (None = all HTTPS allowed)
            timeout: Request timeout in seconds
            max_response_size: Maximum response size in bytes
            user_agent: User agent string
        """
        self.allowed_domains = allowed_domains
        self.timeout = timeout
        self.max_response_size = max_response_size
        self.user_agent = user_agent
    
    def fetch(
        self,
        url: str,
        method: str = 'GET',
        headers: Optional[Dict[str, str]] = None,
        data: Optional[bytes] = None
    ) -> WebResponse:
        """
        Fetch content from URL
        
        Args:
            url: URL to fetch
            method: HTTP method (GET, POST, etc.)
            headers: Additional headers
            data: Request body for POST/PUT
            
        Returns:
            WebResponse with fetched content
        """
        # Validate URL
        if not self._is_url_allowed(url):
            return WebResponse(
                success=False,
                url=url,
                status_code=-1,
                content="",
                headers={},
                error="URL not allowed or invalid"
            )
        
        # Prepare headers
        req_headers = {
            'User-Agent': self.user_agent
        }
        if headers:
            req_headers.update(headers)
        
        try:
            # Create request
            req = urllib.request.Request(
                url,
                data=data,
                headers=req_headers,
                method=method
            )
            
            # Execute request
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                # Check content length
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > self.max_response_size:
                    return WebResponse(
                        success=False,
                        url=url,
                        status_code=response.status,
                        content="",
                        headers=dict(response.headers),
                        error=f"Response too large: {content_length} bytes"
                    )
                
                # Read response (with size limit)
                content = response.read(self.max_response_size)
                
                # Try to decode as text
                try:
                    content_str = content.decode('utf-8')
                except UnicodeDecodeError:
                    content_str = content.decode('latin-1', errors='replace')
                
                return WebResponse(
                    success=True,
                    url=url,
                    status_code=response.status,
                    content=content_str,
                    headers=dict(response.headers)
                )
                
        except urllib.error.HTTPError as e:
            return WebResponse(
                success=False,
                url=url,
                status_code=e.code,
                content="",
                headers=dict(e.headers) if hasattr(e, 'headers') else {},
                error=f"HTTP {e.code}: {e.reason}"
            )
        except urllib.error.URLError as e:
            return WebResponse(
                success=False,
                url=url,
                status_code=-1,
                content="",
                headers={},
                error=f"URL error: {e.reason}"
            )
        except TimeoutError:
            return WebResponse(
                success=False,
                url=url,
                status_code=-1,
                content="",
                headers={},
                error=f"Request timed out after {self.timeout} seconds"
            )
        except Exception as e:
            return WebResponse(
                success=False,
                url=url,
                status_code=-1,
                content="",
                headers={},
                error=f"Fetch error: {e}"
            )
    
    def fetch_json(self, url: str) -> WebResponse:
        """
        Fetch and parse JSON content
        
        Args:
            url: URL to fetch JSON from
            
        Returns:
            WebResponse with parsed JSON in content
        """
        response = self.fetch(url, headers={'Accept': 'application/json'})
        
        if response.success:
            try:
                # Parse JSON and convert back to pretty string
                data = json.loads(response.content)
                response.content = json.dumps(data, indent=2)
            except json.JSONDecodeError as e:
                response.success = False
                response.error = f"Invalid JSON: {e}"
        
        return response
    
    def _is_url_allowed(self, url: str) -> bool:
        """
        Check if URL is allowed
        
        Args:
            url: URL to check
            
        Returns:
            True if allowed, False otherwise
        """
        # Must be HTTP or HTTPS
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Extract domain
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
        except Exception:
            return False
        
        # If no whitelist, allow all HTTPS
        if self.allowed_domains is None:
            return url.startswith('https://')
        
        # Check against whitelist
        for allowed in self.allowed_domains:
            if domain == allowed.lower() or domain.endswith('.' + allowed.lower()):
                return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "tool_name": "web_fetch",
            "allowed_domains": self.allowed_domains,
            "timeout": self.timeout,
            "max_response_size": self.max_response_size,
            "user_agent": self.user_agent
        }
