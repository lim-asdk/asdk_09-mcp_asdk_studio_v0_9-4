# Project: lim_chat_v2_0
# Developer: LIMHWACHAN
# Version: Expert Edition 1.0

"""
🎯 Expert Validator - Enhanced Data Validation for Expert Edition

This module provides comprehensive validation for Expert Debate results:
- Input query validation
- Debate consistency checking (Bull vs Bear vs Judge)
- Data quality validation (reasoning count, confidence range)
- Response completeness verification
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("LimChat.Expert.Validator")


class ExpertValidator:
    """
    Enhanced validator for Expert Edition
    
    Provides Pro-level validation with additional checks for
    multi-AI debate consistency and quality.
    """
    
    def __init__(self):
        """Initialize Expert Validator"""
        self.min_reasoning_count = 3
        self.confidence_min = 0
        self.confidence_max = 100
        
        logger.info("ExpertValidator initialized")
    
    def validate_input(self, query: str) -> List[str]:
        """
        Validate user input query
        
        Args:
            query: User's question
        
        Returns:
            List of validation warnings (empty if valid)
        """
        warnings = []
        
        # Check if query is empty
        if not query or not query.strip():
            warnings.append("Query is empty")
            return warnings
        
        # Check minimum length
        if len(query.strip()) < 3:
            warnings.append("Query is too short (minimum 3 characters)")
        
        # Check maximum length
        if len(query) > 1000:
            warnings.append("Query is too long (maximum 1000 characters)")
        
        # Check for ticker symbol (optional warning)
        import re
        if not re.search(r'\b[A-Z]{2,5}\b', query):
            warnings.append("No ticker symbol detected in query")
        
        return warnings
    
    def validate_ai_response(
        self,
        response: Dict[str, Any],
        ai_name: str
    ) -> List[str]:
        """
        Validate individual AI response
        
        Args:
            response: AI response dictionary
            ai_name: Name of AI (for logging)
        
        Returns:
            List of validation warnings
        """
        warnings = []
        
        # Check required fields
        if "conclusion" not in response:
            warnings.append(f"{ai_name}: Missing 'conclusion' field")
        elif response["conclusion"] not in ["buy", "sell", "hold", "unknown"]:
            warnings.append(f"{ai_name}: Invalid conclusion '{response['conclusion']}'")
        
        if "reasoning" not in response:
            warnings.append(f"{ai_name}: Missing 'reasoning' field")
        elif not isinstance(response["reasoning"], list):
            warnings.append(f"{ai_name}: 'reasoning' must be a list")
        elif len(response["reasoning"]) < self.min_reasoning_count:
            warnings.append(
                f"{ai_name}: Insufficient reasoning "
                f"(got {len(response['reasoning'])}, minimum {self.min_reasoning_count})"
            )
        
        if "confidence" not in response:
            warnings.append(f"{ai_name}: Missing 'confidence' field")
        elif not isinstance(response["confidence"], (int, float)):
            warnings.append(f"{ai_name}: 'confidence' must be a number")
        elif not (self.confidence_min <= response["confidence"] <= self.confidence_max):
            warnings.append(
                f"{ai_name}: Confidence out of range "
                f"(got {response['confidence']}, valid range {self.confidence_min}-{self.confidence_max})"
            )
        
        # Check for parse errors
        if "parse_error" in response:
            warnings.append(f"{ai_name}: JSON parse error - {response['parse_error']}")
        
        return warnings
    
    def validate_debate_consistency(
        self,
        bull_opinion: Optional[Dict[str, Any]],
        bear_opinion: Optional[Dict[str, Any]],
        judge_verdict: Optional[Dict[str, Any]]
    ) -> List[str]:
        """
        Validate consistency across Bull, Bear, and Judge opinions
        
        Args:
            bull_opinion: Bull AI's opinion
            bear_opinion: Bear AI's opinion
            judge_verdict: Judge AI's verdict
        
        Returns:
            List of consistency warnings
        """
        warnings = []
        
        # Check if all opinions exist
        if not bull_opinion:
            warnings.append("Bull opinion is missing")
        if not bear_opinion:
            warnings.append("Bear opinion is missing")
        if not judge_verdict:
            warnings.append("Judge verdict is missing")
            return warnings  # Can't check consistency without judge
        
        # Check Bull vs Bear opposition
        if bull_opinion and bear_opinion:
            bull_conclusion = bull_opinion.get("conclusion", "unknown")
            bear_conclusion = bear_opinion.get("conclusion", "unknown")
            
            # Bull and Bear should have opposite views (ideally)
            if bull_conclusion == bear_conclusion and bull_conclusion != "unknown":
                warnings.append(
                    f"Bull and Bear have same conclusion '{bull_conclusion}' "
                    "(expected opposition for effective debate)"
                )
        
        # Check Judge consistency with Bull/Bear
        if judge_verdict:
            judge_final = judge_verdict.get("final_verdict", "unknown")
            
            # Judge should align with one of them
            if bull_opinion and bear_opinion:
                bull_conclusion = bull_opinion.get("conclusion", "unknown")
                bear_conclusion = bear_opinion.get("conclusion", "unknown")
                
                if judge_final not in [bull_conclusion, bear_conclusion, "hold", "unknown"]:
                    warnings.append(
                        f"Judge verdict '{judge_final}' doesn't align with "
                        f"Bull '{bull_conclusion}' or Bear '{bear_conclusion}'"
                    )
            
            # Check if Judge has scores
            if "bull_score" in judge_verdict and "bear_score" in judge_verdict:
                bull_score = judge_verdict["bull_score"]
                bear_score = judge_verdict["bear_score"]
                
                # Scores should be in valid range
                if not (0 <= bull_score <= 100):
                    warnings.append(f"Bull score out of range: {bull_score}")
                if not (0 <= bear_score <= 100):
                    warnings.append(f"Bear score out of range: {bear_score}")
                
                # Judge verdict should align with higher score
                if judge_final == "buy" and bull_score < bear_score:
                    warnings.append(
                        f"Judge says 'buy' but Bear score ({bear_score}) > Bull score ({bull_score})"
                    )
                elif judge_final == "sell" and bear_score < bull_score:
                    warnings.append(
                        f"Judge says 'sell' but Bull score ({bull_score}) > Bear score ({bear_score})"
                    )
        
        return warnings
    
    def validate_data_quality(
        self,
        response: Dict[str, Any],
        ai_name: str
    ) -> List[str]:
        """
        Validate data quality of AI response
        
        Args:
            response: AI response dictionary
            ai_name: Name of AI
        
        Returns:
            List of quality warnings
        """
        warnings = []
        
        # Check reasoning quality
        if "reasoning" in response and isinstance(response["reasoning"], list):
            for i, reason in enumerate(response["reasoning"]):
                if not reason or not reason.strip():
                    warnings.append(f"{ai_name}: Reasoning #{i+1} is empty")
                elif len(reason.strip()) < 10:
                    warnings.append(f"{ai_name}: Reasoning #{i+1} is too short")
        
        # Check for forbidden phrases (too neutral)
        if "reasoning" in response:
            reasoning_text = " ".join(response["reasoning"]).lower()
            
            forbidden_phrases = [
                "i cannot",
                "i don't have",
                "as an ai",
                "i'm not able to"
            ]
            
            for phrase in forbidden_phrases:
                if phrase in reasoning_text:
                    warnings.append(
                        f"{ai_name}: Contains forbidden phrase '{phrase}' "
                        "(AI should provide analysis, not disclaimers)"
                    )
        
        # Check confidence alignment with conclusion
        if "confidence" in response and "conclusion" in response:
            confidence = response["confidence"]
            conclusion = response["conclusion"]
            
            # Low confidence with strong conclusion is suspicious
            if conclusion in ["buy", "sell"] and confidence < 30:
                warnings.append(
                    f"{ai_name}: Low confidence ({confidence}) with strong conclusion '{conclusion}'"
                )
        
        return warnings
    
    def validate_full_debate(
        self,
        query: str,
        bull_opinion: Optional[Dict[str, Any]],
        bear_opinion: Optional[Dict[str, Any]],
        judge_verdict: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform full validation of Expert Debate
        
        Args:
            query: User's question
            bull_opinion: Bull AI's opinion
            bear_opinion: Bear AI's opinion
            judge_verdict: Judge AI's verdict
        
        Returns:
            Validation result dictionary with all warnings
        """
        all_warnings = []
        
        # 1. Validate input
        input_warnings = self.validate_input(query)
        all_warnings.extend(input_warnings)
        
        # 2. Validate individual responses
        if bull_opinion:
            bull_warnings = self.validate_ai_response(bull_opinion, "Bull AI")
            all_warnings.extend(bull_warnings)
            
            quality_warnings = self.validate_data_quality(bull_opinion, "Bull AI")
            all_warnings.extend(quality_warnings)
        
        if bear_opinion:
            bear_warnings = self.validate_ai_response(bear_opinion, "Bear AI")
            all_warnings.extend(bear_warnings)
            
            quality_warnings = self.validate_data_quality(bear_opinion, "Bear AI")
            all_warnings.extend(quality_warnings)
        
        if judge_verdict:
            judge_warnings = self.validate_ai_response(judge_verdict, "Judge AI")
            all_warnings.extend(judge_warnings)
        
        # 3. Validate debate consistency
        consistency_warnings = self.validate_debate_consistency(
            bull_opinion, bear_opinion, judge_verdict
        )
        all_warnings.extend(consistency_warnings)
        
        # Determine validation status
        critical_count = sum(1 for w in all_warnings if "Missing" in w or "parse error" in w)
        
        if critical_count > 0:
            status = "critical"
        elif len(all_warnings) > 5:
            status = "warning"
        elif len(all_warnings) > 0:
            status = "minor"
        else:
            status = "passed"
        
        logger.info(f"Validation completed: {status} ({len(all_warnings)} warnings)")
        
        return {
            "status": status,
            "warnings": all_warnings,
            "warning_count": len(all_warnings),
            "critical_count": critical_count
        }
