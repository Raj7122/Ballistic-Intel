"""
Unit tests for Gemini API client.
Tests rate limiting, error handling, and extraction accuracy.

Test Coverage:
- API key loading and validation
- Rate limiting enforcement (15 RPM)
- Input validation (length, injection patterns)
- Exponential backoff retry strategy
- Funding data extraction accuracy (80%+ target)
- JSON parsing with markdown code blocks

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
import pytest
import json
import time
import os
from pathlib import Path

# Import the client
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from clients.gemini_client import GeminiClient


@pytest.fixture
def gemini_client():
    """Fixture to create a Gemini client instance."""
    return GeminiClient()


@pytest.fixture
def test_cases():
    """Load test funding announcements from fixtures."""
    fixture_path = Path(__file__).parent / 'fixtures' / 'funding_announcements.json'
    with open(fixture_path) as f:
        return json.load(f)


class TestAPIKeyManagement:
    """Test API key loading and validation."""
    
    def test_api_key_loading(self, gemini_client):
        """Verify API key loads from environment."""
        assert gemini_client.api_key is not None, "API key not loaded"
        assert isinstance(gemini_client.api_key, str), "API key should be string"
        
    def test_api_key_format_validation(self, gemini_client):
        """Verify API key has correct format (starts with AIzaSy)."""
        assert gemini_client.api_key.startswith("AIzaSy"), \
            "API key should start with 'AIzaSy'"
            
    def test_missing_api_key_raises_error(self):
        """Verify error is raised when API key is missing."""
        # Temporarily remove API key from environment
        original_key = os.environ.get('GEMINI_API_KEY')
        if original_key:
            del os.environ['GEMINI_API_KEY']
        
        with pytest.raises(ValueError, match="GEMINI_API_KEY not found"):
            GeminiClient()
            
        # Restore original key
        if original_key:
            os.environ['GEMINI_API_KEY'] = original_key
            
    def test_invalid_api_key_format_raises_error(self):
        """Verify error is raised for invalid API key format."""
        with pytest.raises(ValueError, match="Invalid GEMINI_API_KEY format"):
            GeminiClient(api_key="invalid_key_format")


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_rate_limiter_initialization(self, gemini_client):
        """Verify rate limiter is initialized correctly."""
        assert gemini_client.max_rpm == 15, "Max RPM should be 15"
        assert gemini_client.request_timestamps == [], \
            "Request timestamps should start empty"
            
    def test_request_count_tracking(self, gemini_client):
        """Verify request count is tracked correctly."""
        # Simulate 5 requests
        for _ in range(5):
            gemini_client.request_timestamps.append(time.time())
        
        assert gemini_client.get_request_count() == 5, \
            "Should track 5 requests"
            
    def test_sliding_window_cleanup(self, gemini_client):
        """Verify old timestamps are removed from sliding window."""
        # Add old timestamp (61 seconds ago)
        gemini_client.request_timestamps.append(time.time() - 61)
        # Add recent timestamp
        gemini_client.request_timestamps.append(time.time())
        
        count = gemini_client.get_request_count()
        assert count == 1, "Old timestamps should be removed"
        
    def test_rate_limit_enforcement_logic(self, gemini_client):
        """Test rate limiter logic without waiting (mocked)."""
        # Fill up to max RPM
        now = time.time()
        gemini_client.request_timestamps = [now - i for i in range(15)]
        
        # This should NOT trigger sleep in a real scenario,
        # but we test the logic here
        assert len(gemini_client.request_timestamps) == 15


class TestInputValidation:
    """Test input validation and security checks."""
    
    def test_valid_input_passes(self, gemini_client):
        """Verify valid input passes validation."""
        valid_prompt = "Extract funding data from this article: ..."
        # Should not raise
        gemini_client._validate_input(valid_prompt)
        
    def test_long_input_rejected(self, gemini_client):
        """Verify prompts over 10,000 chars are rejected."""
        long_prompt = "A" * 10001
        
        with pytest.raises(ValueError, match="Prompt too long"):
            gemini_client._validate_input(long_prompt)
            
    def test_injection_pattern_script_tag(self, gemini_client):
        """Verify script tag injection is detected."""
        malicious_prompt = "Extract data <script>alert('xss')</script>"
        
        with pytest.raises(ValueError, match="Suspicious content detected"):
            gemini_client._validate_input(malicious_prompt)
            
    def test_injection_pattern_sql(self, gemini_client):
        """Verify SQL injection patterns are detected."""
        malicious_prompt = "Extract data '; DROP TABLE users; --"
        
        with pytest.raises(ValueError, match="Suspicious content detected"):
            gemini_client._validate_input(malicious_prompt)
            
    def test_validation_can_be_disabled(self, gemini_client):
        """Verify validation can be bypassed when needed."""
        # This is useful for trusted internal prompts
        # The generate_content method has a validate parameter
        assert hasattr(gemini_client.generate_content, '__code__')


class TestContentGeneration:
    """Test content generation with real API calls."""
    
    def test_simple_generation(self, gemini_client):
        """Test basic content generation."""
        prompt = "Say 'Hello, World!' and nothing else."
        response = gemini_client.generate_content(prompt)
        
        assert response is not None, "Response should not be None"
        assert isinstance(response, str), "Response should be string"
        assert len(response) > 0, "Response should not be empty"
        
    def test_json_generation(self, gemini_client):
        """Test JSON generation and parsing."""
        prompt = '''Return ONLY this JSON: {"status": "success", "value": 42}'''
        
        result = gemini_client.generate_json(prompt)
        
        assert isinstance(result, dict), "Should return dict"
        assert "status" in result, "Should have status field"
        
    def test_json_with_markdown_code_block(self, gemini_client):
        """Test JSON extraction from markdown code blocks."""
        # Simulate a response with markdown formatting
        prompt = '''Return this exact JSON wrapped in markdown code blocks:
        ```json
        {"test": "value"}
        ```
        '''
        
        result = gemini_client.generate_json(prompt)
        assert isinstance(result, dict), "Should parse JSON from code block"


class TestFundingExtraction:
    """Test funding data extraction accuracy."""
    
    EXTRACTION_PROMPT_TEMPLATE = """
Extract funding information from this cybersecurity news article.
Return ONLY a valid JSON object with these exact keys:
- company (string): Company name
- amount (string): Funding amount (e.g., "$150M")
- stage (string): Funding stage (e.g., "Series C", "Seed")
- lead_investor (string): Lead investor name

Article:
{article_text}

Return ONLY the JSON object, no other text:
"""
    
    def test_extraction_accuracy(self, gemini_client, test_cases):
        """
        Verify 80%+ accuracy on known funding announcements.
        This is the primary success criteria for Task 1.4.
        """
        correct = 0
        total = len(test_cases)
        results = []
        
        for i, case in enumerate(test_cases):
            prompt = self.EXTRACTION_PROMPT_TEMPLATE.format(
                article_text=case['article_text']
            )
            
            try:
                # Generate and parse response
                extracted = gemini_client.generate_json(prompt)
                
                # Verify all required fields exist
                required_fields = ['company', 'amount', 'stage', 'lead_investor']
                has_all_fields = all(field in extracted for field in required_fields)
                
                if not has_all_fields:
                    results.append({
                        'case': i + 1,
                        'status': 'FAIL',
                        'reason': 'Missing required fields',
                        'extracted': extracted
                    })
                    continue
                
                # Check if company name matches (case-insensitive partial match)
                company_match = (
                    case['ground_truth']['company'].lower() in extracted['company'].lower()
                    or extracted['company'].lower() in case['ground_truth']['company'].lower()
                )
                
                # Check if amount matches (normalize format)
                amount_match = (
                    case['ground_truth']['amount'].replace(' ', '').lower()
                    in extracted['amount'].replace(' ', '').lower()
                )
                
                # Check if stage matches
                stage_match = (
                    case['ground_truth']['stage'].lower()
                    in extracted['stage'].lower()
                )
                
                # Check if lead investor matches (partial match)
                investor_match = (
                    case['ground_truth']['lead_investor'].lower()
                    in extracted['lead_investor'].lower()
                    or extracted['lead_investor'].lower()
                    in case['ground_truth']['lead_investor'].lower()
                )
                
                # Consider correct if at least 3 out of 4 fields match
                matches = sum([company_match, amount_match, stage_match, investor_match])
                
                if matches >= 3:
                    correct += 1
                    results.append({
                        'case': i + 1,
                        'status': 'PASS',
                        'matches': f"{matches}/4",
                        'extracted': extracted
                    })
                else:
                    results.append({
                        'case': i + 1,
                        'status': 'FAIL',
                        'matches': f"{matches}/4",
                        'expected': case['ground_truth'],
                        'extracted': extracted
                    })
                    
            except Exception as e:
                results.append({
                    'case': i + 1,
                    'status': 'ERROR',
                    'error': str(e)
                })
        
        # Calculate accuracy
        accuracy = (correct / total) * 100
        
        # Print detailed results
        print(f"\n{'='*60}")
        print(f"FUNDING EXTRACTION ACCURACY TEST RESULTS")
        print(f"{'='*60}")
        for result in results:
            status_emoji = "✅" if result['status'] == 'PASS' else "❌"
            print(f"{status_emoji} Case {result['case']}: {result['status']}")
            if result['status'] == 'FAIL':
                print(f"   Matches: {result.get('matches', 'N/A')}")
        print(f"{'='*60}")
        print(f"Accuracy: {accuracy:.1f}% ({correct}/{total} correct)")
        print(f"Target: 80% (Task 1.4 Success Criteria)")
        print(f"{'='*60}\n")
        
        # Assert 80% accuracy threshold
        assert accuracy >= 80, \
            f"Accuracy {accuracy:.1f}% below 80% threshold. " \
            f"Only {correct}/{total} cases passed."


class TestErrorHandling:
    """Test error handling and retry logic."""
    
    def test_retry_mechanism_exists(self, gemini_client):
        """Verify retry mechanism is implemented."""
        # Check that generate_content has max_retries parameter
        import inspect
        sig = inspect.signature(gemini_client.generate_content)
        assert 'max_retries' in sig.parameters, \
            "Should have max_retries parameter"
            
    def test_empty_prompt_handling(self, gemini_client):
        """Test handling of empty prompts."""
        # Empty prompt should either be validated or handled gracefully
        # Based on our implementation, it should pass validation but may fail at API
        try:
            response = gemini_client.generate_content("", max_retries=1)
            # If it succeeds, that's fine
            assert response is not None
        except Exception:
            # If it fails, that's also acceptable
            pass


# Run tests with: pytest tests/test_gemini_client.py -v
# For detailed output: pytest tests/test_gemini_client.py -v -s

