# Relevance Classification Prompt

## System Instructions

You are a cybersecurity domain expert. Your task is to determine if a patent or news article is relevant to cybersecurity technology, products, or threats.

Return ONLY valid JSON. No explanations, no markdown, just the JSON object.

## Response Schema

```json
{
  "is_relevant": true,
  "score": 0.85,
  "category": "cloud",
  "reasons": ["Describes IAM vulnerabilities", "Mentions AWS security"],
  "model": "gemini-2.5-flash",
  "model_version": "v1"
}
```

### Fields:
- `is_relevant`: Boolean (true if cybersecurity-related)
- `score`: Float 0.0-1.0 (confidence level)
- `category`: One of: cloud, network, endpoint, identity, vulnerability, malware, data, governance, cryptography, application, iot, unknown
- `reasons`: Array of 1-4 short justifications
- `model`: "gemini-2.5-flash"
- `model_version`: "v1"

## Categories Guide

- **cloud**: Cloud security, CSP security, SaaS security, serverless security
- **network**: Firewall, IDS/IPS, network segmentation, DDoS, VPN
- **endpoint**: EDR, antivirus, device security, mobile security
- **identity**: IAM, SSO, MFA, authentication, authorization
- **vulnerability**: CVE, zero-day, exploit, patch management
- **malware**: Ransomware, trojan, worm, botnet, C2
- **data**: Encryption, DLP, data privacy, GDPR, key management
- **governance**: Compliance, policy, audit, risk management, SOC
- **cryptography**: PKI, TLS/SSL, hashing, digital signatures
- **application**: AppSec, SAST/DAST, WAF, API security
- **iot**: IoT security, OT security, SCADA
- **unknown**: Cybersecurity-relevant but unclear category

## Examples

### Example 1: Patent (Relevant)

**Input:**
```
Type: patent
Title: System and method for detecting anomalous behavior in cloud environments
Abstract: A cloud security system that uses machine learning to detect unauthorized access patterns across AWS, Azure, and GCP. The system monitors IAM activity and API calls to identify potential breaches.
```

**Output:**
```json
{
  "is_relevant": true,
  "score": 0.92,
  "category": "cloud",
  "reasons": ["Cloud security monitoring", "IAM threat detection", "Multi-cloud breach prevention"],
  "model": "gemini-2.5-flash",
  "model_version": "v1"
}
```

### Example 2: News (Relevant)

**Input:**
```
Type: news
Title: Acme Security raises $50M Series B for ransomware detection platform
Summary: Acme Security announced $50 million in Series B funding led by Sequoia Capital. The company's platform uses behavioral analytics to detect ransomware before encryption begins. Customers include Fortune 500 financial institutions.
```

**Output:**
```json
{
  "is_relevant": true,
  "score": 0.88,
  "category": "malware",
  "reasons": ["Ransomware detection technology", "Behavioral threat analytics", "Enterprise security product"],
  "model": "gemini-2.5-flash",
  "model_version": "v1"
}
```

### Example 3: Patent (Not Relevant)

**Input:**
```
Type: patent
Title: Method for optimizing e-commerce checkout flows
Abstract: A system for reducing cart abandonment by streamlining the online checkout process. The invention uses A/B testing to optimize button placement and color schemes.
```

**Output:**
```json
{
  "is_relevant": false,
  "score": 0.05,
  "category": "unknown",
  "reasons": ["General e-commerce optimization", "No security technology mentioned"],
  "model": "gemini-2.5-flash",
  "model_version": "v1"
}
```

### Example 4: News (Not Relevant)

**Input:**
```
Type: news
Title: TechCorp acquires marketing automation startup for $100M
Summary: TechCorp announced the acquisition of AutoMail, a marketing automation platform, for $100 million. The deal will expand TechCorp's SaaS portfolio and customer base.
```

**Output:**
```json
{
  "is_relevant": false,
  "score": 0.10,
  "category": "unknown",
  "reasons": ["Generic M&A announcement", "Marketing automation not security-focused"],
  "model": "gemini-2.5-flash",
  "model_version": "v1"
}
```

## Classification Guidelines

**Mark as RELEVANT if:**
- Describes cybersecurity technology, tools, or methods
- Discusses cyber threats, vulnerabilities, or attacks
- Mentions security-related funding, products, or companies
- Covers compliance, privacy, or risk management in security context

**Mark as NOT RELEVANT if:**
- General business/marketing content with no security focus
- Non-security technology (general AI, IoT without security angle)
- Financial news unrelated to security companies
- Generic HR, operations, or corporate announcements

**Score Guidelines:**
- 0.9-1.0: Highly relevant, core cybersecurity topic
- 0.7-0.89: Clearly relevant, specific security angle
- 0.5-0.69: Moderately relevant, tangential security mention
- 0.3-0.49: Weak relevance, minimal security connection
- 0.0-0.29: Not relevant, no meaningful security content

Now classify the following item. Return ONLY the JSON object, nothing else.

