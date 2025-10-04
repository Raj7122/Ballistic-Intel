"""
Heuristic fallback for relevance classification when LLM is unavailable.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

import hashlib
import re
from typing import Tuple, List

from models import Patent, NewsArticle, RelevanceResult


class RelevanceHeuristics:
    """
    Heuristic-based relevance classifier for patents and news articles.
    
    Strategy:
    - Patents: CPC code mapping + keyword matching
    - News: Multi-signal keyword detection with weights
    - High precision, may have lower recall than LLM
    """
    
    # Cybersecurity CPC codes (patents)
    SECURITY_CPC_PATTERNS = {
        'H04L9': 'cryptography',       # Cryptographic mechanisms
        'H04L63': 'network',            # Network security
        'H04W12': 'network',            # Wireless security
        'G06F21': 'endpoint',           # Security arrangements for computing
        'H04L12/26': 'network',         # Monitoring network arrangements
        'G06F11/30': 'vulnerability',   # Monitoring/testing
        'H04K': 'cryptography',         # Secret communication
        'G09C': 'cryptography',         # Ciphering or deciphering apparatus
    }
    
    # High-confidence cybersecurity keywords (stemmed/lowercased)
    HIGH_CONFIDENCE_KEYWORDS = {
        'malware', 'ransomware', 'trojan', 'botnet', 'exploit',
        'vulnerability', 'cve-', 'zero-day', 'zero day',
        'firewall', 'intrusion detection', 'intrusion prevention',
        'encryption', 'decrypt', 'cryptograph', 'cipher',
        'authentication', 'authorization', 'iam', 'sso', 'mfa',
        'endpoint protection', 'edr', 'xdr', 'siem', 'soar',
        'penetration test', 'red team', 'blue team',
        'threat intelligence', 'apt', 'advanced persistent',
        'ddos', 'denial of service', 'dos attack',
        'phishing', 'spear phishing', 'social engineering',
        'data breach', 'security breach', 'cyber attack',
        'ransomware attack', 'malicious code',
    }
    
    # Medium-confidence keywords
    MEDIUM_CONFIDENCE_KEYWORDS = {
        'security', 'cybersecurity', 'cyber security',
        'breach', 'attack', 'threat', 'risk',
        'compliance', 'gdpr', 'hipaa', 'pci', 'sox',
        'access control', 'privilege', 'permission',
        'audit', 'monitoring', 'detection',
        'vulnerability assessment', 'security audit',
        'incident response', 'forensic',
    }
    
    # Category keywords for classification
    CATEGORY_KEYWORDS = {
        'cloud': ['cloud security', 'aws security', 'azure security', 'gcp security', 'saas security', 'serverless'],
        'network': ['firewall', 'ids', 'ips', 'ddos', 'vpn', 'network security', 'perimeter'],
        'endpoint': ['edr', 'endpoint', 'antivirus', 'anti-virus', 'device security', 'mobile security'],
        'identity': ['iam', 'identity', 'authentication', 'authorization', 'sso', 'mfa', 'access management'],
        'vulnerability': ['vulnerability', 'cve', 'exploit', 'patch', 'zero-day', 'zero day'],
        'malware': ['malware', 'ransomware', 'trojan', 'worm', 'virus', 'botnet', 'c2', 'command and control'],
        'data': ['encryption', 'dlp', 'data loss', 'privacy', 'gdpr', 'key management', 'data protection'],
        'governance': ['compliance', 'audit', 'policy', 'risk', 'sox', 'hipaa', 'pci'],
        'cryptography': ['cryptograph', 'encryption', 'decrypt', 'cipher', 'pki', 'tls', 'ssl', 'hash'],
        'application': ['appsec', 'application security', 'sast', 'dast', 'waf', 'api security'],
    }
    
    # Negative keywords (reduce score)
    NEGATIVE_KEYWORDS = {
        'marketing', 'sales', 'hr', 'human resources',
        'e-commerce', 'retail', 'fashion', 'food',
        'entertainment', 'gaming', 'social media',
    }
    
    def __init__(self, min_score: float = 0.5):
        """
        Initialize heuristics classifier.
        
        Args:
            min_score: Minimum score threshold for relevance
        """
        self.min_score = min_score
    
    def classify_patent(self, patent: Patent) -> RelevanceResult:
        """
        Classify patent using CPC codes and keywords.
        
        Args:
            patent: Patent object
            
        Returns:
            RelevanceResult
        """
        score = 0.0
        reasons: List[str] = []
        category = 'unknown'
        
        # Check CPC codes
        for cpc in patent.cpc_codes:
            for pattern, cat in self.SECURITY_CPC_PATTERNS.items():
                if cpc.startswith(pattern):
                    score += 0.4
                    reasons.append(f"Security CPC code: {cpc}")
                    category = cat
                    break
        
        # Combine text for keyword analysis
        text = f"{patent.title} {patent.abstract}".lower()
        content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        
        # High-confidence keywords
        for keyword in self.HIGH_CONFIDENCE_KEYWORDS:
            if keyword in text:
                score += 0.3
                reasons.append(f"High-confidence keyword: {keyword}")
                if score > 1.0:
                    break
        
        # Medium-confidence keywords
        for keyword in self.MEDIUM_CONFIDENCE_KEYWORDS:
            if keyword in text:
                score += 0.1
                reasons.append(f"Security keyword: {keyword}")
                if score > 1.0:
                    break
        
        # Detect category if not set by CPC
        if category == 'unknown':
            category = self._detect_category(text)
        
        # Negative keywords penalty
        for keyword in self.NEGATIVE_KEYWORDS:
            if keyword in text:
                score -= 0.2
                break
        
        # Clamp score
        score = max(0.0, min(1.0, score))
        is_relevant = score >= self.min_score
        
        return RelevanceResult.create_heuristic(
            item_id=patent.publication_number,
            source_type='patent',
            is_relevant=is_relevant,
            score=score,
            category=category,
            reasons=reasons[:4],  # Limit to 4 reasons
            content_hash=content_hash
        )
    
    def classify_news(self, article: NewsArticle) -> RelevanceResult:
        """
        Classify news article using keyword analysis.
        
        Args:
            article: NewsArticle object
            
        Returns:
            RelevanceResult
        """
        score = 0.0
        reasons: List[str] = []
        
        # Combine text
        text = article.get_text_for_analysis().lower()
        content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        
        # High-confidence keywords
        high_conf_count = 0
        for keyword in self.HIGH_CONFIDENCE_KEYWORDS:
            if keyword in text:
                high_conf_count += 1
                reasons.append(f"Security keyword: {keyword}")
        
        if high_conf_count > 0:
            score += min(0.6, high_conf_count * 0.2)
        
        # Medium-confidence keywords
        med_conf_count = 0
        for keyword in self.MEDIUM_CONFIDENCE_KEYWORDS:
            if keyword in text:
                med_conf_count += 1
        
        if med_conf_count > 0:
            score += min(0.3, med_conf_count * 0.1)
        
        # Detect category
        category = self._detect_category(text)
        
        # Negative keywords penalty
        for keyword in self.NEGATIVE_KEYWORDS:
            if keyword in text:
                score -= 0.3
                reasons.append(f"Non-security context: {keyword}")
                break
        
        # Clamp score
        score = max(0.0, min(1.0, score))
        is_relevant = score >= self.min_score
        
        # Add generic reason if no specific reasons found
        if not reasons:
            reasons = ["No strong cybersecurity signals detected"]
        
        return RelevanceResult.create_heuristic(
            item_id=article.id,
            source_type='news',
            is_relevant=is_relevant,
            score=score,
            category=category,
            reasons=reasons[:4],
            content_hash=content_hash
        )
    
    def _detect_category(self, text: str) -> str:
        """
        Detect category based on keyword matching.
        
        Args:
            text: Lowercased text
            
        Returns:
            Category name
        """
        category_scores = {}
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return 'unknown'

