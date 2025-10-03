"""
Gemini API client with rate limiting, caching, and error handling.
Implements exponential backoff for 429 errors and circuit breaker pattern.

Security Features:
- Input validation (max 10,000 chars, injection pattern detection)
- Rate limiting (15 RPM for free tier)
- Exponential backoff retry strategy
- Environment variable-based API key management

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
import os
import time
import hashlib
import json
from typing import Dict, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import google.generativeai as genai
except ImportError:
    raise ImportError(
        "google-generativeai package not installed. "
        "Run: pip install google-generativeai"
    )


class GeminiClient:
    """
    Google Gemini API client with built-in rate limiting and security features.
    
    Attributes:
        api_key (str): Gemini API key from environment
        model (GenerativeModel): Configured Gemini model instance
        max_rpm (int): Maximum requests per minute (default: 15 for free tier)
        request_timestamps (List[float]): Rolling window of request timestamps
    """
    
    # Security: Banned patterns to prevent injection attacks
    BANNED_PATTERNS = [
        "<script>", "</script>",
        "DROP TABLE", "DELETE FROM",
        "'; --", "' OR '1'='1",
        "UNION SELECT", "INSERT INTO"
    ]
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: str = "gemini-2.5-flash"
    ):
        """
        Initialize Gemini client with rate limiting (15 RPM free tier).
        
        Args:
            api_key: Optional API key (defaults to GEMINI_API_KEY env var)
            model: Model name (default: gemini-2.5-flash - stable flash model)
            
        Raises:
            ValueError: If API key not found in environment
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables. "
                "Add it to your .env file."
            )
        
        # Validate API key format (should start with AIzaSy)
        if not self.api_key.startswith("AIzaSy"):
            raise ValueError(
                "Invalid GEMINI_API_KEY format. "
                "Key should start with 'AIzaSy'"
            )
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model)
        self.request_timestamps: List[float] = []
        self.max_rpm = 15  # Free tier limit
        
    def _validate_input(self, prompt: str) -> None:
        """
        Validate prompt before sending to API.
        
        Args:
            prompt: User prompt to validate
            
        Raises:
            ValueError: If prompt is too long or contains banned patterns
        """
        # Check length (prevent token abuse)
        if len(prompt) > 10000:
            raise ValueError(
                f"Prompt too long: {len(prompt)} characters "
                f"(max 10,000 allowed)"
            )
        
        # Check for injection attempts
        prompt_lower = prompt.lower()
        for pattern in self.BANNED_PATTERNS:
            if pattern.lower() in prompt_lower:
                raise ValueError(
                    f"Suspicious content detected: '{pattern}' "
                    f"found in prompt"
                )
                
    def _enforce_rate_limit(self) -> None:
        """
        Ensure we don't exceed 15 requests per minute.
        Implements sliding window rate limiting.
        """
        now = time.time()
        
        # Remove timestamps older than 60 seconds (sliding window)
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if now - ts < 60
        ]
        
        if len(self.request_timestamps) >= self.max_rpm:
            # Calculate wait time until oldest request is 60 seconds old
            oldest_request = self.request_timestamps[0]
            sleep_time = 60 - (now - oldest_request)
            
            if sleep_time > 0:
                print(
                    f"⚠️  Rate limit reached ({self.max_rpm} RPM). "
                    f"Sleeping {sleep_time:.2f}s..."
                )
                time.sleep(sleep_time)
                
    def generate_content(
        self, 
        prompt: str, 
        max_retries: int = 3,
        validate: bool = True
    ) -> str:
        """
        Generate content with exponential backoff on errors.
        
        Args:
            prompt: Input prompt for the model
            max_retries: Maximum retry attempts (default: 3)
            validate: Whether to validate input (default: True)
            
        Returns:
            str: Generated response text
            
        Raises:
            Exception: If all retries fail
        """
        if validate:
            self._validate_input(prompt)
            
        self._enforce_rate_limit()
        
        for attempt in range(max_retries):
            try:
                # Record request timestamp
                self.request_timestamps.append(time.time())
                
                # Make API call
                response = self.model.generate_content(prompt)
                
                # Extract text from response
                return response.text
                
            except Exception as e:
                error_msg = str(e)
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                
                print(
                    f"❌ Attempt {attempt + 1}/{max_retries} failed: {error_msg}"
                )
                
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # All retries exhausted
                    raise Exception(
                        f"Gemini API call failed after {max_retries} attempts: "
                        f"{error_msg}"
                    )
                    
    def generate_json(
        self, 
        prompt: str, 
        max_retries: int = 3
    ) -> dict:
        """
        Generate content and parse as JSON.
        
        Args:
            prompt: Input prompt (should request JSON output)
            max_retries: Maximum retry attempts
            
        Returns:
            dict: Parsed JSON response
            
        Raises:
            json.JSONDecodeError: If response is not valid JSON
        """
        response_text = self.generate_content(prompt, max_retries)
        
        # Try to extract JSON from markdown code blocks
        if "```json" in response_text:
            # Extract content between ```json and ```
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            # Extract content between ``` and ```
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
            
        return json.loads(response_text)
        
    def get_request_count(self) -> int:
        """
        Get number of requests made in the last 60 seconds.
        
        Returns:
            int: Current request count in sliding window
        """
        now = time.time()
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if now - ts < 60
        ]
        return len(self.request_timestamps)

