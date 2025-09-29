# strategic_decision_engine.py
"""
Strategic Decision Engine - The brain that makes buying decisions simple and trustworthy
This module provides:
- Clear BUY/AVOID/CAUTION recommendations with confidence scores
- Strategic weighting of multiple decision factors
- Cross-validation against multiple data sources
- Trust-building explanations that users can understand
- Learning from user outcomes and market feedback
"""

import numpy as np
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class Decision(Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    CAUTION = "CAUTION"
    AVOID = "AVOID"
    STRONG_AVOID = "STRONG_AVOID"

@dataclass
class TrustSignal:
    """Individual trust signal with weight and explanation"""
    name: str
    value: float  # -1 to 1 (negative = red flag, positive = green flag)
    weight: float  # 0 to 1 (importance)
    explanation: str
    confidence: float  # 0 to 1 (how sure we are about this signal)

@dataclass
class StrategicRecommendation:
    """Final strategic recommendation with all supporting data"""
    decision: Decision
    confidence: float  # 0 to 1
    profit_potential: float  # Expected profit in dollars
    risk_score: float  # 0 to 1 (higher = riskier)
    time_to_sell: int  # Expected days to sell
    market_strength: str  # "Strong", "Moderate", "Weak"
    primary_reason: str  # Main reason for recommendation
    trust_signals: List[TrustSignal]
    cross_validation_score: float  # 0 to 1 (how well our sources agree)
    quick_summary: str  # One-line summary for busy users

class StrategicDecisionEngine:
    """Strategic engine that makes trustworthy buy/sell decisions"""
    
    def __init__(self):
        # Strategic weights for different decision factors
        self.factor_weights = {
            'profit_margin': 0.25,      # Raw profit potential
            'market_liquidity': 0.20,   # How fast it sells
            'risk_assessment': 0.20,    # Safety/scam risk
            'price_validation': 0.15,   # Price accuracy vs market
            'seller_trust': 0.10,       # Seller reliability
            'market_trend': 0.10        # Category growth/decline
        }
        
        # Trust thresholds
        self.trust_thresholds = {
            'high_confidence': 0.8,
            'medium_confidence': 0.6,
            'low_confidence': 0.4
        }
        
        # Market strength indicators
        self.market_strength_thresholds = {
            'strong': {'sold_ratio': 0.7, 'avg_days': 14, 'price_stability': 0.8},
            'moderate': {'sold_ratio': 0.4, 'avg_days': 30, 'price_stability': 0.6},
            'weak': {'sold_ratio': 0.2, 'avg_days': 60, 'price_stability': 0.4}
        }
    
    def analyze_market_strength(self, sold_count: int, active_count: int, 
                              price_variance: float) -> Tuple[str, float]:
        """Analyze overall market strength for this item category"""
        total_listings = sold_count + active_count
        if total_listings == 0:
            return "Unknown", 0.0
        
        sold_ratio = sold_count / total_listings
        price_stability = max(0, 1 - price_variance)  # Lower variance = higher stability
        
        # Determine market strength
        if (sold_ratio >= self.market_strength_thresholds['strong']['sold_ratio'] and
            price_stability >= self.market_strength_thresholds['strong']['price_stability']):
            return "Strong", 0.85
        elif (sold_ratio >= self.market_strength_thresholds['moderate']['sold_ratio'] and
              price_stability >= self.market_strength_thresholds['moderate']['price_stability']):
            return "Moderate", 0.65
        else:
            return "Weak", 0.35
    
    def calculate_trust_signals(self, analysis_data: Dict) -> List[TrustSignal]:
        """Generate trust signals that users can understand and trust"""
        signals = []
        
        # Price Trust Signal
        price_vs_market = analysis_data.get('price_vs_market_pct', 1.0)
        if price_vs_market < 0.7:
            signals.append(TrustSignal(
                name="Price Alert",
                value=-0.8,
                weight=0.9,
                explanation=f"Price is {(1-price_vs_market)*100:.0f}% below market average - investigate why",
                confidence=0.9
            ))
        elif price_vs_market > 1.3:
            signals.append(TrustSignal(
                name="Price Warning",
                value=-0.5,
                weight=0.7,
                explanation=f"Price is {(price_vs_market-1)*100:.0f}% above market average",
                confidence=0.8
            ))
        else:
            signals.append(TrustSignal(
                name="Fair Price",
                value=0.6,
                weight=0.8,
                explanation="Price is within normal market range",
                confidence=0.7
            ))
        
        # Seller Trust Signal
        feedback_pct = analysis_data.get('seller_feedback_pct', 0.98)
        account_age = analysis_data.get('account_age_days_norm', 0.5)
        
        if feedback_pct >= 0.98 and account_age >= 0.7:
            signals.append(TrustSignal(
                name="Trusted Seller",
                value=0.8,
                weight=0.7,
                explanation="Seller has excellent feedback and established account",
                confidence=0.9
            ))
        elif feedback_pct < 0.85 or account_age < 0.2:
            signals.append(TrustSignal(
                name="Seller Risk",
                value=-0.7,
                weight=0.8,
                explanation="New seller or poor feedback history",
                confidence=0.8
            ))
        else:
            signals.append(TrustSignal(
                name="Average Seller",
                value=0.0,
                weight=0.5,
                explanation="Seller has reasonable feedback and account age",
                confidence=0.6
            ))
        
        # Market Liquidity Signal
        sold_count = analysis_data.get('sold_count', 0)
        active_count = analysis_data.get('active_count', 0)
        
        if sold_count > 100:
            signals.append(TrustSignal(
                name="High Demand",
                value=0.7,
                weight=0.8,
                explanation=f"{sold_count} recently sold - proven market demand",
                confidence=0.9
            ))
        elif sold_count < 10:
            signals.append(TrustSignal(
                name="Low Demand",
                value=-0.4,
                weight=0.6,
                explanation=f"Only {sold_count} recently sold - limited market",
                confidence=0.7
            ))
        else:
            signals.append(TrustSignal(
                name="Moderate Demand",
                value=0.2,
                weight=0.5,
                explanation=f"{sold_count} recently sold - decent market activity",
                confidence=0.6
            ))
        
        # Competition Analysis Signal
        competition_ratio = active_count / max(sold_count, 1)
        if competition_ratio > 3:
            signals.append(TrustSignal(
                name="High Competition",
                value=-0.6,
                weight=0.7,
                explanation=f"{active_count} active listings vs {sold_count} sold - saturated market",
                confidence=0.8
            ))
        elif competition_ratio < 0.5:
            signals.append(TrustSignal(
                name="Low Competition", 
                value=0.5,
                weight=0.6,
                explanation="Good supply/demand ratio - easier to sell",
                confidence=0.7
            ))
        
        # Description Quality Signal
        desc_quality = analysis_data.get('desc_length_norm', 0.0)
        uses_stock = analysis_data.get('uses_stock_images', 0.0)
        
        if uses_stock > 0.8 and desc_quality < 0.3:
            signals.append(TrustSignal(
                name="Poor Listing",
                value=-0.5,
                weight=0.6,
                explanation="Generic photos and minimal description - potential dropshipper",
                confidence=0.7
            ))
        elif desc_quality > 0.7:
            signals.append(TrustSignal(
                name="Detailed Listing",
                value=0.4,
                weight=0.5,
                explanation="Comprehensive description suggests legitimate seller",
                confidence=0.6
            ))
        
        return signals
    
    def cross_validate_recommendation(self, analysis_data: Dict, 
                                   external_data: Optional[Dict] = None) -> float:
        """Cross-validate our recommendation against external sources"""
        validation_score = 0.5  # Start neutral
        validation_count = 0
        
        # Validate price against multiple sources
        our_market_value = analysis_data.get('market_value', 0)
        if our_market_value > 0:
            validation_count += 1
            # TODO: Add additional price sources (Amazon, Google Shopping, etc.)
            # For now, use internal consistency
            price_consistency = 1.0 - abs(our_market_value - analysis_data.get('median_active', our_market_value)) / our_market_value
            validation_score += price_consistency * 0.3
        
        # Validate seller reputation
        if analysis_data.get('seller_feedback_pct'):
            validation_count += 1
            # Check if seller feedback makes sense with our risk assessment
            feedback_consistency = analysis_data.get('seller_feedback_pct', 0.5)
            validation_score += feedback_consistency * 0.2
        
        # Market activity validation
        sold_count = analysis_data.get('sold_count', 0)
        if sold_count > 0:
            validation_count += 1
            # Higher sold count increases confidence
            activity_score = min(sold_count / 100, 1.0)  # Cap at 100 sales
            validation_score += activity_score * 0.2
        
        # Normalize by number of validation checks
        if validation_count > 0:
            validation_score = min(validation_score / validation_count, 1.0)
        
        return validation_score
    
    def estimate_time_to_sell(self, sold_count: int, active_count: int, 
                            profit_margin: float) -> int:
        """Estimate how many days it will take to sell"""
        # Base time estimate on market activity
        total_market = sold_count + active_count
        if total_market == 0:
            return 90  # Unknown market
        
        # Calculate turnover rate (sold per day approximation)
        turnover_rate = sold_count / 30  # Assume 30-day window
        if turnover_rate == 0:
            return 90
        
        # Market saturation factor
        saturation = active_count / max(sold_count, 1)
        
        # Base days calculation
        base_days = min(active_count / max(turnover_rate, 0.1), 90)
        
        # Adjust for profit margin (higher margin = can price more aggressively)
        if profit_margin > 50:
            base_days *= 0.7  # Can price to sell faster
        elif profit_margin < 20:
            base_days *= 1.3  # Need to wait for right buyer
        
        return max(int(base_days), 3)  # Minimum 3 days
    
    def make_strategic_decision(self, analysis_data: Dict, 
                              user_preferences: Optional[Dict] = None) -> StrategicRecommendation:
        """Make the final strategic buy/avoid decision"""
        
        # Extract key metrics
        profit = analysis_data.get('profit', 0)
        profit_margin = analysis_data.get('profit_margin_percent', 0)
        market_value = analysis_data.get('market_value', 0)
        risk_score = analysis_data.get('risk_score', 0.5)
        sold_count = analysis_data.get('sold_count', 0)
        active_count = analysis_data.get('active_count', 0)
        
        # Calculate trust signals
        trust_signals = self.calculate_trust_signals(analysis_data)
        
        # Calculate market strength
        price_variance = 0.2  # TODO: Calculate actual price variance
        market_strength, market_confidence = self.analyze_market_strength(
            sold_count, active_count, price_variance
        )
        
        # Cross-validate our analysis
        cross_validation_score = self.cross_validate_recommendation(analysis_data)
        
        # Estimate time to sell
        time_to_sell = self.estimate_time_to_sell(sold_count, active_count, profit_margin)
        
        # Strategic decision logic
        decision_score = 0.0
        confidence_factors = []
        
        # Factor 1: Profit potential (weighted 25%)
        if profit_margin >= 100:
            decision_score += 0.9 * self.factor_weights['profit_margin']
            confidence_factors.append(0.9)
        elif profit_margin >= 50:
            decision_score += 0.7 * self.factor_weights['profit_margin']
            confidence_factors.append(0.8)
        elif profit_margin >= 20:
            decision_score += 0.4 * self.factor_weights['profit_margin']
            confidence_factors.append(0.6)
        elif profit_margin <= 0:
            decision_score -= 0.8 * self.factor_weights['profit_margin']
            confidence_factors.append(0.9)
        
        # Factor 2: Market liquidity (weighted 20%)
        if sold_count >= 100 and time_to_sell <= 14:
            decision_score += 0.8 * self.factor_weights['market_liquidity']
            confidence_factors.append(0.8)
        elif sold_count >= 20 and time_to_sell <= 30:
            decision_score += 0.5 * self.factor_weights['market_liquidity']
            confidence_factors.append(0.6)
        elif sold_count < 5:
            decision_score -= 0.6 * self.factor_weights['market_liquidity']
            confidence_factors.append(0.7)
        
        # Factor 3: Risk assessment (weighted 20%)
        if risk_score >= 0.8:
            decision_score -= 0.9 * self.factor_weights['risk_assessment']
            confidence_factors.append(0.9)
        elif risk_score >= 0.6:
            decision_score -= 0.5 * self.factor_weights['risk_assessment']
            confidence_factors.append(0.7)
        elif risk_score <= 0.3:
            decision_score += 0.6 * self.factor_weights['risk_assessment']
            confidence_factors.append(0.6)
        
        # Factor 4: Price validation (weighted 15%)
        price_trust = next((s for s in trust_signals if s.name in ["Fair Price", "Price Alert", "Price Warning"]), None)
        if price_trust:
            decision_score += price_trust.value * self.factor_weights['price_validation']
            confidence_factors.append(price_trust.confidence)
        
        # Factor 5: Seller trust (weighted 10%)
        seller_trust = next((s for s in trust_signals if "Seller" in s.name), None)
        if seller_trust:
            decision_score += seller_trust.value * self.factor_weights['seller_trust']
            confidence_factors.append(seller_trust.confidence)
        
        # Factor 6: Market trend (weighted 10%)
        decision_score += market_confidence * self.factor_weights['market_trend']
        confidence_factors.append(market_confidence)
        
        # Calculate overall confidence
        overall_confidence = statistics.mean(confidence_factors) if confidence_factors else 0.5
        overall_confidence *= cross_validation_score  # Reduce confidence if validation is low
        
        # Map decision score to recommendation
        if decision_score >= 0.7 and overall_confidence >= 0.8:
            decision = Decision.STRONG_BUY
            primary_reason = f"Excellent profit potential ({profit_margin:.0f}% margin) with high market confidence"
        elif decision_score >= 0.4 and overall_confidence >= 0.6:
            decision = Decision.BUY
            primary_reason = f"Good opportunity with {profit_margin:.0f}% margin and {market_strength.lower()} market"
        elif decision_score >= -0.2 or risk_score >= 0.6:
            decision = Decision.CAUTION
            primary_reason = f"Proceed carefully - {time_to_sell} day sell time, risk score {risk_score:.1f}"
        elif decision_score >= -0.5:
            decision = Decision.AVOID
            primary_reason = f"Poor profit potential or high risk (score: {risk_score:.1f})"
        else:
            decision = Decision.STRONG_AVOID
            primary_reason = "High risk with poor fundamentals - avoid"
        
        # Generate quick summary
        emoji_map = {
            Decision.STRONG_BUY: "🚀",
            Decision.BUY: "✅", 
            Decision.CAUTION: "⚠️",
            Decision.AVOID: "❌",
            Decision.STRONG_AVOID: "🚨"
        }
        
        quick_summary = f"{emoji_map[decision]} {decision.value}: ${profit:.0f} profit, {time_to_sell}d to sell, {overall_confidence*100:.0f}% confidence"
        
        return StrategicRecommendation(
            decision=decision,
            confidence=overall_confidence,
            profit_potential=profit,
            risk_score=risk_score,
            time_to_sell=time_to_sell,
            market_strength=market_strength,
            primary_reason=primary_reason,
            trust_signals=trust_signals,
            cross_validation_score=cross_validation_score,
            quick_summary=quick_summary
        )
    
    def explain_decision_for_user(self, recommendation: StrategicRecommendation) -> str:
        """Generate user-friendly explanation of the decision"""
        explanation = f"""
🎯 RECOMMENDATION: {recommendation.decision.value}
💰 Profit Potential: ${recommendation.profit_potential:.0f}
📈 Confidence: {recommendation.confidence*100:.0f}%
⏱️ Time to Sell: {recommendation.time_to_sell} days
🏪 Market: {recommendation.market_strength}

WHY: {recommendation.primary_reason}

KEY FACTORS:
"""
        
        # Add top trust signals
        for signal in sorted(recommendation.trust_signals, key=lambda x: abs(x.value * x.weight), reverse=True)[:3]:
            emoji = "✅" if signal.value > 0 else "⚠️" if signal.value > -0.5 else "❌"
            explanation += f"{emoji} {signal.name}: {signal.explanation}\n"
        
        explanation += f"\n🔍 Cross-validation Score: {recommendation.cross_validation_score*100:.0f}%"
        
        return explanation
