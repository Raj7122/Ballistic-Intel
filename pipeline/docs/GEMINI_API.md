# Gemini API Integration

## Overview
Google Gemini 1.5 Flash integration for AI-powered extraction of funding data from cybersecurity newsletters and patent classification.

## Configuration

### Model Information
- **Model:** `gemini-2.5-flash` (stable version, June 2025 release)
- **Provider:** Google AI Studio
- **Rate Limit:** 15 requests per minute (RPM) - Free tier
- **Cost:** $0 (within free quota)
- **Token Limits:** 
  - Input: Up to 1 million tokens
  - Output: ~8k tokens
- **Alternative Models:** `gemini-flash-latest` (always points to latest stable)

### Environment Setup

Add to `/pipeline/.env`:
```bash
GEMINI_API_KEY=AIzaSy...your_key_here
```

Never commit the `.env` file to git. It should be listed in `.gitignore`.

### API Key Management

**Obtaining API Key:**
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create new API key for "Ballistic Intel" project
3. Copy key (format: `AIzaSy...`)
4. Add to `.env` file

**Security Requirements:**
- ✅ Store in environment variables only
- ✅ Never hardcode in source files
- ✅ Rotate every 90 days (see SECURITY.md)
- ✅ Restrict to specific IP ranges in production
- ✅ Monitor usage in [API Dashboard](https://aistudio.google.com)

## Usage Examples

### Basic Usage

```python
from clients.gemini_client import GeminiClient

# Initialize client
client = GeminiClient()

# Generate content
response = client.generate_content("Summarize this article...")
print(response)
```

### JSON Generation

```python
# Request structured JSON output
prompt = """
Extract funding data as JSON:
Article: "Company X raised $50M Series B..."

Return: {"company": "...", "amount": "...", "stage": "..."}
"""

data = client.generate_json(prompt)
print(data['company'])  # "Company X"
```

### Funding Extraction (High-Level)

```python
from utils.funding_extractor import FundingExtractor

extractor = FundingExtractor()

article = """
Wiz announced a $100 million Series B round led by Insight Partners...
"""

data = extractor.extract_funding_data(article)

if data:
    print(f"{data['company']} raised {data['amount']} in {data['stage']}")
    print(f"Lead investor: {data['lead_investor']}")
```

### Batch Processing

```python
articles = [
    {'text': 'Article 1...', 'url': 'http://...'},
    {'text': 'Article 2...', 'url': 'http://...'}
]

results = extractor.batch_extract(articles)

for result in results:
    if result:
        print(f"Found funding: {result['company']}")
```

## Rate Limiting

The client implements automatic rate limiting:

```python
client = GeminiClient()

# Make 20 requests - will automatically throttle after 15th
for i in range(20):
    response = client.generate_content(f"Request {i}")
    # After 15 requests, will sleep until rate limit window resets
```

**Rate Limit Behavior:**
- Tracks requests in sliding 60-second window
- Automatically sleeps when limit reached
- Displays warning: `⚠️ Rate limit reached (15 RPM). Sleeping 45.2s...`

**Monitoring:**
```python
# Check current request count
count = client.get_request_count()
print(f"Requests in last 60s: {count}/15")
```

## Error Handling

### Automatic Retry with Exponential Backoff

```python
# Retries up to 3 times with exponential backoff (1s, 2s, 4s)
response = client.generate_content(prompt, max_retries=3)
```

### Error Codes

| Code | Description | Handling |
|------|-------------|----------|
| `429` | Rate limit exceeded | Exponential backoff (automatic) |
| `401` | Invalid API key | Check `.env` file, verify key format |
| `400` | Invalid prompt | Validate input length/content |
| `500` | Server error | Retry with backoff |
| `503` | Service unavailable | Wait and retry |

### Input Validation Errors

```python
# Too long (>10,000 chars)
try:
    client.generate_content("A" * 10001)
except ValueError as e:
    print(e)  # "Prompt too long: 10001 characters"

# Injection attempt
try:
    client.generate_content("<script>alert('xss')</script>")
except ValueError as e:
    print(e)  # "Suspicious content detected: '<script>'"
```

## Security Features

### Input Validation
- **Max Length:** 10,000 characters
- **Banned Patterns:** SQL injection, XSS, script tags
- **Sanitization:** HTML tag removal, whitespace normalization

### API Key Protection
- ✅ Environment variable storage only
- ✅ Format validation (`AIzaSy` prefix)
- ✅ Never logged or printed
- ✅ Excluded from error messages

## Performance Optimization

### Caching Strategy

The `FundingExtractor` includes built-in caching:

```python
extractor = FundingExtractor()

# First call - hits API
data1 = extractor.extract_funding_data(article, url="http://example.com")

# Second call - returns cached result
data2 = extractor.extract_funding_data(article, url="http://example.com")

# Clear cache when needed
extractor.clear_cache()
```

**Cache Benefits:**
- Reduces API calls for duplicate articles
- Saves on rate limit quota
- Faster response times

### Token Optimization

**Tips to reduce token usage:**
1. Truncate long articles to 5000 chars (done automatically in `FundingExtractor`)
2. Use specific, concise prompts
3. Request JSON output (more compact than prose)
4. Remove HTML/formatting before sending

## Testing

### Run Unit Tests

```bash
cd /pipeline
source venv/bin/activate
pytest tests/test_gemini_client.py -v
```

### Test Coverage
- ✅ API key loading and validation
- ✅ Rate limiting enforcement
- ✅ Input validation and security
- ✅ JSON parsing with markdown code blocks
- ✅ Funding extraction accuracy (80%+ target)
- ✅ Error handling and retries

### Accuracy Testing

Test against 5 known funding announcements:

```bash
pytest tests/test_gemini_client.py::TestFundingExtraction::test_extraction_accuracy -v -s
```

**Success Criteria (Task 1.4):**
- 80%+ accuracy on test set
- All required fields extracted correctly
- Proper error handling for edge cases

## Monitoring & Quotas

### Check Usage

1. Visit [Google AI Studio Dashboard](https://aistudio.google.com/app/apikey)
2. View "API key usage" section
3. Monitor daily request count

**Free Tier Limits:**
- **RPM:** 15 requests/minute
- **Daily:** ~21,600 requests/day (theoretical max)
- **Recommended:** <1,000 requests/day for safety margin

### Alert Thresholds

Set up alerts when:
- 80% of daily quota used (800+ requests)
- Rate limit hit frequently (>5 times/hour)
- Error rate >5%

## Integration with Pipeline

### Agent P2 - Universal Relevance Filter
Uses Gemini to filter cybersecurity-relevant patents and articles.

### Agent P3 - Extraction & Classification
Uses `FundingExtractor` to extract structured data from articles.

**Example Pipeline Integration:**

```python
from utils.funding_extractor import FundingExtractor

def process_newsletter_articles(articles):
    extractor = FundingExtractor()
    
    for article in articles:
        # Extract funding data
        funding_data = extractor.extract_funding_data(article['content'])
        
        if funding_data:
            # Insert into database
            save_to_database(funding_data)
```

## Troubleshooting

### "API key not found" Error

```bash
# Check .env file exists
ls -la /pipeline/.env

# Verify GEMINI_API_KEY is set
cat /pipeline/.env | grep GEMINI_API_KEY

# Test loading
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GEMINI_API_KEY')[:10])"
```

### Rate Limit Issues

```python
# Reduce request rate
import time

for article in articles:
    data = extractor.extract_funding_data(article)
    time.sleep(4)  # 15 requests/min = 1 request per 4 seconds
```

### JSON Parsing Errors

If you encounter `JSONDecodeError`:

1. Check prompt formatting (request explicit JSON structure)
2. Use `generate_json()` method (handles markdown code blocks)
3. Add explicit instructions: "Return ONLY valid JSON, no other text"

## Best Practices

1. ✅ **Use `FundingExtractor`** for high-level operations
2. ✅ **Cache results** when processing duplicate content
3. ✅ **Validate outputs** before database insertion
4. ✅ **Monitor rate limits** in production
5. ✅ **Rotate API keys** every 90 days
6. ✅ **Test prompts** thoroughly before batch processing
7. ✅ **Log errors** to `log.md` for continuous improvement

## References

- [Google AI Studio](https://aistudio.google.com)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [Security Policy](./SECURITY.md)
- [Project Plan](../../plan.md)

---

**Last Updated:** Task 1.4 - October 3, 2025  
**Author:** S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System

