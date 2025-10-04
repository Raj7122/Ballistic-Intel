"""
Funding announcement detector using heuristic rules.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

import re
from typing import Tuple


class FundingDetector:
    """
    Detect funding announcements using high-precision heuristics.
    
    Strategy: Require multiple signals (≥2) to minimize false positives.
    Later, Agent P2/P3 will use Gemini for higher recall and precision.
    """
    
    # Funding action keywords
    ACTION_PATTERNS = [
        r'\braised\b',
        r'\bsecured\b',
        r'\bclosed\b',
        r'\bannounced\s+(?:a|the)\s+\$',
        r'\bcompleted\s+(?:a|the)\s+\$',
    ]
    
    # Money indicators
    MONEY_PATTERNS = [
        r'\$\d+(?:\.\d+)?\s*(?:million|billion|M|B)\b',
        r'\$\d+(?:\.\d+)?[MB]\b',
    ]
    
    # Funding stage keywords
    STAGE_PATTERNS = [
        r'\bseed\s+round\b',
        r'\bpre-seed\b',
        r'\bSeries\s+[A-F]\b',
        r'\bbridge\s+round\b',
    ]
    
    # Investor indicators
    INVESTOR_PATTERNS = [
        r'\bled\s+by\b',
        r'\bco-led\s+by\b',
        r'\binvestors?\s+include\b',
        r'\bparticipation\s+from\b',
        r'\bfrom\s+investors?\b',
    ]
    
    # Valuation indicators (bonus signal)
    VALUATION_PATTERNS = [
        r'\bvaluation\b',
        r'\bpost-money\b',
        r'\bvalued\s+at\b',
    ]
    
    def __init__(self, min_signals: int = 2):
        """
        Initialize funding detector.
        
        Args:
            min_signals: Minimum number of signals required (default: 2)
        """
        self.min_signals = min_signals
        
        # Compile patterns
        self.action_regex = re.compile('|'.join(self.ACTION_PATTERNS), re.IGNORECASE)
        self.money_regex = re.compile('|'.join(self.MONEY_PATTERNS), re.IGNORECASE)
        self.stage_regex = re.compile('|'.join(self.STAGE_PATTERNS), re.IGNORECASE)
        self.investor_regex = re.compile('|'.join(self.INVESTOR_PATTERNS), re.IGNORECASE)
        self.valuation_regex = re.compile('|'.join(self.VALUATION_PATTERNS), re.IGNORECASE)
    
    def detect(self, text: str) -> Tuple[bool, str]:
        """
        Detect if text contains a funding announcement.
        
        Args:
            text: Article text (title + summary + content)
            
        Returns:
            Tuple of (is_funding, reason)
        """
        if not text:
            return (False, "")
        
        # Normalize text
        text_lower = text.lower()
        
        # Remove HTML tags if any
        text_clean = re.sub(r'<[^>]+>', '', text_lower)
        
        # Check each signal
        signals = []
        
        if self.action_regex.search(text_clean):
            match = self.action_regex.search(text_clean)
            signals.append(f"action:{match.group()}")
        
        if self.money_regex.search(text_clean):
            match = self.money_regex.search(text_clean)
            signals.append(f"money:{match.group()}")
        
        if self.stage_regex.search(text_clean):
            match = self.stage_regex.search(text_clean)
            signals.append(f"stage:{match.group()}")
        
        if self.investor_regex.search(text_clean):
            match = self.investor_regex.search(text_clean)
            signals.append(f"investor:{match.group()}")
        
        if self.valuation_regex.search(text_clean):
            match = self.valuation_regex.search(text_clean)
            signals.append(f"valuation:{match.group()}")
        
        # Decision: require min_signals
        is_funding = len(signals) >= self.min_signals
        reason = "; ".join(signals) if signals else ""
        
        return (is_funding, reason)

