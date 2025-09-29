# monetization_engine.py - Complete Revenue System
"""
TrustGuard Monetization Architecture
- Freemium model with clear upgrade path
- Ad revenue (non-intrusive)
- SaaS tiers (Individual, Pro, Business, Enterprise)
- Usage-based billing
- Affiliate revenue
- Data licensing (B2B)
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid

# ============================================================================
# 1. PRICING TIERS & FEATURE GATES
# ============================================================================

class SubscriptionTier(Enum):
    """Subscription tier definitions"""
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class PricingEngine:
    """
    Complete pricing and feature gating system
    """
    
    # Tier definitions
    TIERS = {
        SubscriptionTier.FREE: {
            'name': 'Free Forever',
            'price_monthly': 0,
            'price_yearly': 0,
            'features': {
                # Core protection (limited)
                'scam_alerts': 'basic',  # green/yellow/red badge only
                'detailed_analysis_per_month': 10,
                'risk_factors_shown': 3,  # top 3 only
                'profit_calculator': False,
                'historical_data': False,
                'price_tracking': False,
                'safe_alternatives': False,
                'priority_support': False,
                'api_access': False,
                'team_seats': 1,
                'ad_free': False,  # See non-intrusive ads
                
                # Platforms
                'ebay_protection': True,
                'amazon_protection': True,  # basic only
                
                # Limits
                'max_watchlist': 10,
                'alerts_per_day': 50,
            },
            'upgrade_prompts': {
                'detailed_analysis': 'Upgrade to Pro to see all 47+ risk factors',
                'profit_calc': 'Pro users see profit potential on every listing',
                'alternatives': 'Get safe alternatives with Pro'
            }
        },
        
        SubscriptionTier.PRO: {
            'name': 'Pro',
            'price_monthly': 19.99,
            'price_yearly': 199.00,  # 2 months free
            'features': {
                # Full individual protection
                'scam_alerts': 'advanced',
                'detailed_analysis_per_month': 'unlimited',
                'risk_factors_shown': 'all',
                'profit_calculator': True,
                'historical_data': True,  # 90 days
                'price_tracking': True,
                'safe_alternatives': True,
                'priority_support': True,
                'api_access': False,
                'team_seats': 1,
                'ad_free': True,
                
                # Platforms
                'ebay_protection': True,
                'amazon_protection': True,
                'walmart_protection': True,
                'facebook_marketplace': True,
                
                # Advanced features
                'max_watchlist': 100,
                'alerts_per_day': 'unlimited',
                'price_drop_alerts': True,
                'arbitrage_opportunities': True,
                'browser_extension': True,
                'mobile_app': True,
                'export_data': True,
            },
            'popular': True  # Show "Most Popular" badge
        },
        
        SubscriptionTier.BUSINESS: {
            'name': 'Business',
            'price_monthly': 49.99,
            'price_yearly': 499.00,
            'features': {
                # Everything in Pro, plus:
                'scam_alerts': 'advanced',
                'detailed_analysis_per_month': 'unlimited',
                'risk_factors_shown': 'all',
                'profit_calculator': True,
                'historical_data': True,  # 365 days
                'price_tracking': True,
                'safe_alternatives': True,
                'priority_support': True,
                'api_access': 'basic',  # 1,000 calls/month
                'team_seats': 5,
                'ad_free': True,
                
                # Platforms (all)
                'ebay_protection': True,
                'amazon_protection': True,
                'walmart_protection': True,
                'facebook_marketplace': True,
                'craigslist_protection': True,
                'etsy_protection': True,
                
                # Business features
                'max_watchlist': 500,
                'alerts_per_day': 'unlimited',
                'price_drop_alerts': True,
                'arbitrage_opportunities': True,
                'browser_extension': True,
                'mobile_app': True,
                'export_data': True,
                'bulk_analysis': True,  # Analyze CSV of listings
                'custom_alerts': True,
                'team_dashboard': True,
                'monthly_reports': True,
            }
        },
        
        SubscriptionTier.ENTERPRISE: {
            'name': 'Enterprise',
            'price_monthly': 'custom',
            'price_yearly': 'custom',
            'features': {
                # Everything in Business, plus:
                'scam_alerts': 'custom',
                'detailed_analysis_per_month': 'unlimited',
                'risk_factors_shown': 'all',
                'profit_calculator': True,
                'historical_data': True,  # unlimited
                'price_tracking': True,
                'safe_alternatives': True,
                'priority_support': True,
                'dedicated_support': True,
                'api_access': 'unlimited',
                'team_seats': 'unlimited',
                'ad_free': True,
                
                # All platforms
                'all_platforms': True,
                
                # Enterprise features
                'max_watchlist': 'unlimited',
                'alerts_per_day': 'unlimited',
                'white_label': True,
                'custom_integration': True,
                'sla_guarantee': '99.9%',
                'custom_ml_models': True,
                'dedicated_account_manager': True,
                'on_premise_option': True,
                'custom_reporting': True,
                'sso_integration': True,
            },
            'contact_sales': True
        }
    }
    
    def get_tier_features(self, tier: SubscriptionTier) -> Dict[str, Any]:
        """Get features for a tier"""
        return self.TIERS[tier]['features']
    
    def check_feature_access(self, user_tier: SubscriptionTier, 
                           feature: str) -> bool:
        """Check if user has access to a feature"""
        features = self.get_tier_features(user_tier)
        return features.get(feature, False)
    
    def calculate_price(self, tier: SubscriptionTier, billing_cycle: str,
                       team_seats: int = 1, api_calls: int = 0) -> float:
        """
        Calculate price with usage-based components
        """
        tier_data = self.TIERS[tier]
        
        if tier == SubscriptionTier.FREE:
            return 0.0
        
        if tier == SubscriptionTier.ENTERPRISE:
            # Custom pricing, call sales
            return None
        
        # Base price
        if billing_cycle == 'monthly':
            base_price = tier_data['price_monthly']
        else:  # yearly
            base_price = tier_data['price_yearly']
        
        # Additional seats (Business/Enterprise)
        if tier == SubscriptionTier.BUSINESS and team_seats > 5:
            additional_seats = team_seats - 5
            base_price += additional_seats * 9.99  # $9.99 per extra seat
        
        # API overage (Business tier)
        if tier == SubscriptionTier.BUSINESS and api_calls > 1000:
            overage = api_calls - 1000
            base_price += (overage / 1000) * 10.00  # $10 per 1K calls
        
        return round(base_price, 2)
    
    def get_upgrade_upsell(self, current_tier: SubscriptionTier, 
                          blocked_feature: str) -> Dict[str, Any]:
        """
        Generate upsell message when user hits limit
        """
        current_features = self.get_tier_features(current_tier)
        
        # Find which tier has this feature
        target_tier = None
        for tier in [SubscriptionTier.PRO, SubscriptionTier.BUSINESS, 
                     SubscriptionTier.ENTERPRISE]:
            if self.check_feature_access(tier, blocked_feature):
                target_tier = tier
                break
        
        if not target_tier:
            return None
        
        return {
            'message': f"Upgrade to {self.TIERS[target_tier]['name']} to unlock {blocked_feature}",
            'current_tier': current_tier.value,
            'target_tier': target_tier.value,
            'price': self.TIERS[target_tier].get('price_monthly', 'custom'),
            'cta': 'Upgrade Now',
            'trial_available': True,
            'trial_days': 14
        }


# ============================================================================
# 2. AD REVENUE SYSTEM (Non-Intrusive)
# ============================================================================

class AdRevenueEngine:
    """
    Non-intrusive ad system for free tier users
    - Ethical ads only (no scams, no sketchy products)
    - Native ad format (blends with UI)
    - Performance-based (CPC/CPM)
    - User can upgrade to remove
    """
    
    def __init__(self):
        self.ad_networks = {
            'google_adsense': {
                'enabled': True,
                'revenue_share': 0.68,  # Google takes 32%
                'avg_cpm': 2.50,
                'avg_cpc': 0.35
            },
            'carbon_ads': {  # Tech-focused, ethical ads
                'enabled': True,
                'revenue_share': 0.70,
                'avg_cpm': 4.00,
                'avg_cpc': 0.50
            },
            'native_sponsors': {  # Direct sponsors (e.g., escrow services)
                'enabled': True,
                'revenue_share': 0.90,  # We control directly
                'avg_cpm': 8.00,
                'avg_cpc': 1.50
            }
        }
    
    def should_show_ad(self, user_tier: SubscriptionTier, 
                      page_context: str) -> bool:
        """Determine if ad should be shown"""
        # No ads for paid users
        if user_tier != SubscriptionTier.FREE:
            return False
        
        # Don't show on critical alerts (bad UX)
        if page_context == 'scam_alert_critical':
            return False
        
        # Show on safe listings or non-critical pages
        return True
    
    def get_ad_placement(self, context: str) -> Dict[str, Any]:
        """
        Get ad placement based on context
        Returns ad format and positioning
        """
        placements = {
            'listing_safe': {
                'format': 'native',
                'position': 'below_analysis',
                'headline': 'Recommended Services',
                'max_ads': 1,
                'revenue_type': 'cpc'
            },
            'dashboard': {
                'format': 'banner',
                'position': 'sidebar',
                'headline': None,
                'max_ads': 2,
                'revenue_type': 'cpm'
            },
            'search_results': {
                'format': 'native',
                'position': 'every_5_results',
                'headline': 'Sponsored',
                'max_ads': 3,
                'revenue_type': 'cpc'
            }
        }
        
        return placements.get(context, placements['dashboard'])
    
    def calculate_ad_revenue(self, impressions: int, clicks: int,
                            network: str = 'google_adsense') -> float:
        """Calculate estimated ad revenue"""
        network_data = self.ad_networks
