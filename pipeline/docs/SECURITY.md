# Security Documentation - Gemini API

## Overview
This document outlines security practices for the Gemini API integration in the Ballistic Intel pipeline, following OWASP Top 10 guidelines and the S.A.F.E. D.R.Y. principles.

## API Key Security

### Storage Requirements

**✅ APPROVED:**
- Environment variables (`.env` file, not committed to git)
- Vercel/Railway secrets (production deployment)
- Encrypted credential stores (AWS Secrets Manager, if scaling)

**❌ FORBIDDEN:**
- Hardcoded in source code
- Committed to git repository
- Stored in plain text files tracked by version control
- Logged to console or log files
- Included in error messages shown to users

### Key Rotation Schedule

**Rotation Policy:**
- **Frequency:** Every 90 days
- **Emergency Rotation:** Within 24 hours if compromise suspected

**Rotation Process:**

1. **Generate New Key** (Day 0)
   ```bash
   # Visit https://aistudio.google.com/app/apikey
   # Create new key: "Ballistic Intel - 2025-Q1"
   # Copy to secure location
   ```

2. **Update Development** (Day 0)
   ```bash
   # Update local .env
   nano /pipeline/.env
   # Replace GEMINI_API_KEY=AIzaSy_OLD with GEMINI_API_KEY=AIzaSy_NEW
   
   # Test
   python -c "from clients.gemini_client import GeminiClient; c = GeminiClient(); print('✅ New key working')"
   ```

3. **Update Staging** (Day 1)
   ```bash
   # Railway/Render environment variables
   # Update GEMINI_API_KEY in dashboard
   # Redeploy staging environment
   ```

4. **Update Production** (Day 2)
   ```bash
   # Vercel secrets
   vercel secrets add gemini-api-key AIzaSy_NEW
   
   # Update production deployment
   vercel --prod
   ```

5. **Verify All Environments** (Day 3)
   ```bash
   # Test staging and production
   # Monitor error rates in Sentry
   # Check API quota usage
   ```

6. **Revoke Old Key** (Day 4 - 24hr grace period)
   ```bash
   # In Google AI Studio
   # Delete old key: "Ballistic Intel - 2024-Q4"
   ```

### Key Compromise Response

**If API key is exposed (e.g., accidentally committed to git):**

1. **Immediate** (< 1 hour):
   - Revoke compromised key in Google AI Studio
   - Generate new key
   - Update all environments

2. **Short-term** (< 24 hours):
   - Audit git history for exposure duration
   - Check API usage logs for unauthorized requests
   - Document incident in `log.md`

3. **Long-term** (< 1 week):
   - Review and strengthen git hooks (prevent future commits)
   - Add pre-commit checks for API key patterns
   - Update team security training

## Input Validation & Sanitization

### Validation Rules

The `GeminiClient` validates all inputs before API calls:

```python
# Implemented in clients/gemini_client.py
def _validate_input(self, prompt: str) -> None:
    # 1. Length check (max 10,000 chars)
    if len(prompt) > 10000:
        raise ValueError(f"Prompt too long: {len(prompt)} chars")
    
    # 2. Injection pattern detection
    banned_patterns = [
        "<script>", "DROP TABLE", "'; --",
        "UNION SELECT", "INSERT INTO"
    ]
    for pattern in banned_patterns:
        if pattern.lower() in prompt.lower():
            raise ValueError(f"Suspicious content: {pattern}")
```

### OWASP Top 10 Mitigations

#### 1. Injection (A03:2021)
**Risk:** Malicious prompts could manipulate AI outputs

**Mitigation:**
- ✅ Input length limits (10,000 chars)
- ✅ Banned pattern detection
- ✅ Output validation before database insertion
- ✅ Structured output format (JSON schema validation)

#### 2. Broken Authentication (A07:2021)
**Risk:** Unauthorized API access

**Mitigation:**
- ✅ API key format validation (`AIzaSy` prefix check)
- ✅ Environment-based key management
- ✅ No authentication bypass paths

#### 3. Sensitive Data Exposure (A02:2021)
**Risk:** API key leakage in logs/errors

**Mitigation:**
```python
# Never log full API key
print(f"Using key: {api_key[:10]}...")  # Only first 10 chars

# Exclude from error messages
try:
    client = GeminiClient(api_key=key)
except ValueError as e:
    # Error message does NOT contain the key
    print("Invalid API key format")
```

#### 4. Security Misconfiguration (A05:2021)
**Risk:** Insecure default settings

**Mitigation:**
- ✅ Validation enabled by default (`validate=True`)
- ✅ Conservative rate limits (15 RPM)
- ✅ Explicit error handling (no silent failures)

#### 5. Insufficient Logging & Monitoring (A09:2021)
**Risk:** Attacks go undetected

**Mitigation:**
```python
# Log validation failures (without sensitive data)
if validation_failed:
    log_to_file(f"Validation failed: prompt length {len(prompt)}")
    
# Monitor rate limit hits
if rate_limit_hit:
    log_to_file(f"Rate limit reached at {timestamp}")
```

## Rate Limiting & Abuse Prevention

### Implemented Controls

1. **Sliding Window Rate Limiting**
   ```python
   # Max 15 requests per 60-second window
   # Automatically enforced by GeminiClient
   ```

2. **Request Throttling**
   - Sleep when limit reached (prevents quota exhaustion)
   - Exponential backoff on errors (1s, 2s, 4s)

3. **Quota Monitoring**
   - Track request count per minute
   - Alert at 80% of daily quota (see Monitoring section)

### DoS Prevention

**Scenario:** Malicious actor floods pipeline with requests

**Protection:**
1. Rate limiter prevents >15 requests/min
2. Input validation rejects oversized prompts
3. Circuit breaker pattern (after 3 consecutive failures, pause for 60s)

**Future Enhancement (Phase 2):**
- Implement Redis-based distributed rate limiting
- Add IP-based throttling (Upstash Rate Limit)

## Data Privacy & Compliance

### Data Sent to Gemini API

**What we send:**
- Article text (public news articles only)
- Patent abstracts (public USPTO data)
- Structured prompts (our templates)

**What we DON'T send:**
- User personal information (PII)
- Internal company data
- Credentials or secrets
- User behavior data

### GDPR Compliance

**Article 25 (Data Protection by Design):**
- ✅ Minimal data sent to third-party API
- ✅ No PII processed through Gemini
- ✅ Public data sources only (USPTO, news sites)

**Right to Erasure:**
- Cache can be cleared on demand (`extractor.clear_cache()`)
- No long-term storage of API requests/responses

## Audit & Logging

### Security Events to Log

Log these events to `/pipeline/logs/security.log`:

1. **API Key Events**
   - Key validation failures
   - Missing key errors
   - Key rotation completed

2. **Input Validation**
   - Rejected prompts (with reason, not content)
   - Injection attempt detected
   - Oversized input rejected

3. **Rate Limiting**
   - Rate limit hit (timestamp, request count)
   - Quota threshold warnings (80%, 90%, 95%)

4. **API Errors**
   - 401 Unauthorized (possible key compromise)
   - 429 Rate Limit (unexpected, since we enforce locally)
   - 5xx Server errors

### Log Format

```python
import logging

logging.basicConfig(
    filename='logs/security.log',
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO
)

# Example log entries
logging.warning("Rate limit reached: 15 requests in 60s")
logging.error("API key validation failed: invalid format")
logging.info("Input validation rejected: prompt length 12000 chars")
```

### Log Retention

- **Security logs:** 90 days
- **Error logs:** 30 days
- **Info logs:** 7 days

## Incident Response Plan

### Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| **Critical** | API key compromised, active exploitation | < 1 hour |
| **High** | Injection attempt detected, rate limit abuse | < 4 hours |
| **Medium** | Repeated validation failures, quota warnings | < 24 hours |
| **Low** | Normal rate limit hits, minor errors | < 1 week |

### Response Procedures

**Critical Incident (API Key Leak):**
1. Revoke key immediately
2. Generate and deploy new key
3. Audit API usage logs for suspicious activity
4. Document in `log.md`
5. Review and update security controls
6. Team post-mortem within 48 hours

**High Incident (Injection Attempt):**
1. Log attempt details (without PII)
2. Block pattern if novel
3. Review validation logic
4. Update banned patterns list
5. Test against attack vector

## Security Testing

### Automated Tests

Run security tests before each deployment:

```bash
# Input validation tests
pytest tests/test_gemini_client.py::TestInputValidation -v

# Rate limiting tests
pytest tests/test_gemini_client.py::TestRateLimiting -v

# API key management tests
pytest tests/test_gemini_client.py::TestAPIKeyManagement -v
```

### Manual Security Review Checklist

Before production deployment:

- [ ] `.env` files not committed to git
- [ ] API key format validation working
- [ ] Input validation blocking injection patterns
- [ ] Rate limiting enforcing 15 RPM
- [ ] Error messages don't leak sensitive data
- [ ] Logging captures security events
- [ ] Key rotation procedure documented
- [ ] Incident response plan understood by team

## CIS Benchmark Compliance

**CIS Docker Benchmark v1.5.0** (for Railway/Render containers)

Relevant controls for Gemini integration:

- ✅ **5.1** - Secrets not in container images (using env vars)
- ✅ **5.7** - No privileged access needed
- ✅ **5.15** - Health checks configured (API key validation)
- ✅ **5.28** - PID limits (prevent fork bombs in retry loops)

## Monitoring & Alerts

### Metrics to Monitor

1. **API Request Rate**
   - Threshold: >12 requests/min (80% of limit)
   - Alert: Slack notification

2. **Error Rate**
   - Threshold: >5% of requests failing
   - Alert: Email to dev team

3. **Quota Usage**
   - Threshold: >800 requests/day (80% of safe daily limit)
   - Alert: Dashboard warning

4. **Validation Rejections**
   - Threshold: >10 rejections/hour
   - Alert: Security team review

### Monitoring Tools

- **Production:** Sentry (error tracking)
- **Development:** Local logging
- **API Quota:** Google AI Studio dashboard

## References

- [OWASP Top 10 (2021)](https://owasp.org/Top10/)
- [CIS Benchmarks](https://downloads.cisecurity.org)
- [Google AI Studio Security](https://ai.google.dev/docs)
- [Project Security Model](../../plan.md#security--threat-model)

---

**Last Updated:** Task 1.4 - October 3, 2025  
**Next Review:** January 3, 2026 (90-day key rotation)  
**Security Contact:** [Project Lead]

