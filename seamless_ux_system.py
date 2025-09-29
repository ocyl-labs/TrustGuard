# seamless_ux_system.py
"""
Seamless User Experience System
Creates an addictive, secure, and profitable experience for both buyers and sellers
Includes: Gamification, Security, Audio/Visual feedback, Arbitrage detection
"""

import json
import hashlib
import time
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio
import cv2
from PIL import Image
import logging

logger = logging.getLogger(__name__)

@dataclass
class UserJourney:
    """Track complete user journey from discovery to profit"""
    user_id: str
    journey_type: str  # 'buyer', 'seller', 'flipper'
    current_step: str
    progress_percent: float
    items_in_pipeline: List[Dict]
    total_profit_tracked: float
    success_rate: float
    engagement_score: float
    risk_alerts_avoided: int
    arbitrage_opportunities_found: int

@dataclass
class SecurityEvent:
    """Security event tracking for manipulation detection"""
    event_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    user_id: str
    details: Dict
    timestamp: datetime
    resolved: bool = False

@dataclass
class ArbitrageOpportunity:
    """Arbitrage opportunity with profit calculation"""
    source_platform: str
    target_platform: str
    item_title: str
    buy_price: float
    sell_price: float
    profit_margin: float
    confidence_score: float
    time_to_profit_days: int
    risk_level: str
    user_match_score: float  # How well this matches user's history

class GameifiedUXEngine:
    """Creates addictive, secure user experience with real-world value"""
    
    def __init__(self):
        # Gamification elements
        self.achievement_system = AchievementSystem()
        self.sound_engine = SoundFeedbackEngine()
        self.visual_engine = VisualFeedbackEngine()
        
        # Security systems
        self.security_monitor = SecurityMonitor()
        self.anti_manipulation = AntiManipulationSystem()
        
        # Arbitrage detection
        self.arbitrage_detector = ArbitrageDetector()
        
        # User behavior tracking
        self.user_patterns = defaultdict(lambda: {
            'favorite_categories': [],
            'price_range_preferences': {},
            'risk_tolerance': 0.5,
            'profit_targets': {},
            'time_patterns': [],
            'success_items': []
        })

class AchievementSystem:
    """Gamification system that makes money-making addictive"""
    
    def __init__(self):
        self.achievements = {
            # Buyer achievements
            'first_save': {
                'name': '💰 First Save',
                'description': 'Avoided your first bad deal',
                'reward': 'Unlock profit tracker',
                'sound': 'coin_collect.wav'
            },
            'bargain_hunter': {
                'name': '🎯 Bargain Hunter',
                'description': 'Found 10 items below market value',
                'reward': '$5 credit + Advanced insights',
                'sound': 'level_up.wav'
            },
            'scam_detective': {
                'name': '🕵️ Scam Detective', 
                'description': 'Avoided 5 high-risk listings',
                'reward': 'VIP status + Priority support',
                'sound': 'achievement_unlock.wav'
            },
            
            # Seller achievements
            'first_listing': {
                'name': '📝 First AI Listing',
                'description': 'Created your first optimized listing',
                'reward': 'Free photo enhancement',
                'sound': 'success_chime.wav'
            },
            'profit_master': {
                'name': '💎 Profit Master',
                'description': 'Made $1000 profit using our insights',
                'reward': 'Exclusive arbitrage alerts',
                'sound': 'cash_register.wav'
            },
            'speed_seller': {
                'name': '⚡ Speed Seller',
                'description': 'Sold item within predicted timeframe',
                'reward': 'Velocity bonus insights',
                'sound': 'speed_boost.wav'
            },
            
            # Arbitrage achievements
            'arbitrage_rookie': {
                'name': '🔄 Arbitrage Rookie',
                'description': 'Found your first cross-platform opportunity',
                'reward': 'Arbitrage dashboard access',
                'sound': 'discovery.wav'
            },
            'profit_streak': {
                'name': '🔥 Profit Streak',
                'description': '10 profitable flips in a row',
                'reward': 'Elite arbitrage alerts',
                'sound': 'streak_fire.wav'
            }
        }
        
        self.user_achievements = defaultdict(set)
        self.user_stats = defaultdict(lambda: {
            'items_saved_from': 0,
            'total_profit_made': 0,
            'scams_avoided': 0,
            'successful_flips': 0,
            'current_streak': 0,
            'arbitrage_found': 0
        })

    def check_achievements(self, user_id: str, action_type: str, action_data: Dict) -> List[Dict]:
        """Check if user unlocked new achievements"""
        new_achievements = []
        stats = self.user_stats[user_id]
        
        # Update stats based on action
        if action_type == 'avoided_bad_deal':
            stats['items_saved_from'] += 1
            stats['scams_avoided'] += 1
            
            # Check achievements
            if stats['items_saved_from'] == 1 and 'first_save' not in self.user_achievements[user_id]:
                new_achievements.append(self._unlock_achievement(user_id, 'first_save'))
                
            if stats['items_saved_from'] == 10 and 'bargain_hunter' not in self.user_achievements[user_id]:
                new_achievements.append(self._unlock_achievement(user_id, 'bargain_hunter'))
                
            if stats['scams_avoided'] == 5 and 'scam_detective' not in self.user_achievements[user_id]:
                new_achievements.append(self._unlock_achievement(user_id, 'scam_detective'))
        
        elif action_type == 'successful_flip':
            profit = action_data.get('profit', 0)
            stats['total_profit_made'] += profit
            stats['successful_flips'] += 1
            stats['current_streak'] += 1
            
            if stats['total_profit_made'] >= 1000 and 'profit_master' not in self.user_achievements[user_id]:
                new_achievements.append(self._unlock_achievement(user_id, 'profit_master'))
                
            if stats['current_streak'] == 10 and 'profit_streak' not in self.user_achievements[user_id]:
                new_achievements.append(self._unlock_achievement(user_id, 'profit_streak'))
        
        elif action_type == 'arbitrage_found':
            stats['arbitrage_found'] += 1
            
            if stats['arbitrage_found'] == 1 and 'arbitrage_rookie' not in self.user_achievements[user_id]:
                new_achievements.append(self._unlock_achievement(user_id, 'arbitrage_rookie'))
        
        return new_achievements
    
    def _unlock_achievement(self, user_id: str, achievement_key: str) -> Dict:
        """Unlock achievement and return celebration data"""
        self.user_achievements[user_id].add(achievement_key)
        achievement = self.achievements[achievement_key]
        
        return {
            'achievement': achievement,
            'timestamp': datetime.now().isoformat(),
            'celebration_type': 'popup_animation',
            'sound_effect': achievement['sound'],
            'visual_effect': 'gold_particle_explosion'
        }

class SoundFeedbackEngine:
    """Audio feedback system for different user actions"""
    
    def __init__(self):
        self.sound_library = {
            # Success sounds
            'verification_complete': {'file': 'scan_complete.wav', 'volume': 0.7},
            'good_deal_found': {'file': 'success_bell.wav', 'volume': 0.8},
            'profit_calculated': {'file': 'cash_counter.wav', 'volume': 0.6},
            
            # Warning sounds
            'risk_detected': {'file': 'alert_soft.wav', 'volume': 0.5},
            'high_risk_warning': {'file': 'warning_tone.wav', 'volume': 0.7},
            
            # Interactive sounds
            'button_hover': {'file': 'hover_soft.wav', 'volume': 0.3},
            'page_transition': {'file': 'swoosh.wav', 'volume': 0.4},
            'data_loading': {'file': 'processing_hum.wav', 'volume': 0.2},
            
            # Achievement sounds
            'level_up': {'file': 'level_up_fanfare.wav', 'volume': 0.9},
            'achievement_unlock': {'file': 'achievement_chime.wav', 'volume': 0.8},
            'streak_milestone': {'file': 'streak_celebration.wav', 'volume': 0.8}
        }
        
        self.user_sound_preferences = defaultdict(lambda: {
            'enabled': True,
            'master_volume': 0.7,
            'notification_sounds': True,
            'achievement_sounds': True,
            'interaction_sounds': True
        })
    
    def play_sound(self, user_id: str, sound_key: str, context: Dict = None) -> Dict:
        """Generate sound playback command for frontend"""
        prefs = self.user_sound_preferences[user_id]
        
        if not prefs['enabled']:
            return {'play_sound': False}
        
        sound_config = self.sound_library.get(sound_key, {})
        if not sound_config:
            return {'play_sound': False}
        
        return {
            'play_sound': True,
            'sound_file': sound_config['file'],
            'volume': sound_config['volume'] * prefs['master_volume'],
            'context': context or {}
        }

class VisualFeedbackEngine:
    """Visual feedback system with addictive animations and colors"""
    
    def __init__(self):
        # Color psychology for different states
        self.color_schemes = {
            'safe_deal': {
                'primary': '#10b981',    # Emerald green
                'secondary': '#ecfdf5',  # Light green bg
                'accent': '#047857',     # Dark green
                'glow': '#34d399'        # Bright green glow
            },
            'great_deal': {
                'primary': '#f59e0b',    # Amber
                'secondary': '#fffbeb',  # Light amber bg
                'accent': '#d97706',     # Dark amber
                'glow': '#fbbf24'        # Bright amber glow
            },
            'high_risk': {
                'primary': '#ef4444',    # Red
                'secondary': '#fef2f2',  # Light red bg
                'accent': '#dc2626',     # Dark red
                'glow': '#f87171'        # Bright red glow
            },
            'processing': {
                'primary': '#3b82f6',    # Blue
                'secondary': '#eff6ff',  # Light blue bg
                'accent': '#1d4ed8',     # Dark blue
                'glow': '#60a5fa'        # Bright blue glow
            },
            'arbitrage': {
                'primary': '#8b5cf6',    # Purple
                'secondary': '#f5f3ff',  # Light purple bg
                'accent': '#7c3aed',     # Dark purple
                'glow': '#a78bfa'        # Bright purple glow
            }
        }
        
        # Animation presets
        self.animations = {
            'trust_score_reveal': {
                'type': 'number_counter',
                'duration': 1500,
                'easing': 'ease_out_bounce',
                'particles': True
            },
            'risk_warning_pulse': {
                'type': 'pulse_glow',
                'duration': 2000,
                'intensity': 'high',
                'color': 'danger'
            },
            'profit_celebration': {
                'type': 'currency_rain',
                'duration': 3000,
                'particle_count': 50,
                'sound_sync': True
            },
            'achievement_unlock': {
                'type': 'badge_explosion',
                'duration': 4000,
                'glow_intensity': 'max',
                'confetti': True
            },
            'loading_scan': {
                'type': 'scanning_beam',
                'duration': 800,
                'color': 'processing',
                'progress_bar': True
            }
        }
    
    def create_visual_feedback(self, feedback_type: str, data: Dict) -> Dict:
        """Generate visual feedback configuration"""
        if feedback_type == 'trust_score_display':
            score = data.get('score', 50)
            
            if score >= 80:
                scheme = 'safe_deal'
                animation = 'trust_score_reveal'
                particles = 'success_sparkles'
            elif score >= 60:
                scheme = 'great_deal'
                animation = 'trust_score_reveal'
                particles = 'gentle_glow'
            else:
                scheme = 'high_risk'
                animation = 'risk_warning_pulse'
                particles = 'warning_indicators'
            
            return {
                'color_scheme': self.color_schemes[scheme],
                'animation': self.animations[animation],
                'particle_effect': particles,
                'display_duration': 5000
            }
        
        elif feedback_type == 'arbitrage_opportunity':
            return {
                'color_scheme': self.color_schemes['arbitrage'],
                'animation': self.animations['profit_celebration'],
                'special_effects': {
                    'profit_highlight': True,
                    'platform_badges': True,
                    'confidence_meter': True
                }
            }
        
        elif feedback_type == 'achievement_unlock':
            return {
                'color_scheme': self.color_schemes['great_deal'],
                'animation': self.animations['achievement_unlock'],
                'overlay': {
                    'type': 'full_screen_celebration',
                    'duration': 4000,
                    'dismissible': True
                }
            }
        
        return {'color_scheme': self.color_schemes['processing']}

class SecurityMonitor:
    """Advanced security monitoring to prevent manipulation"""
    
    def __init__(self):
        self.security_rules = {
            'rate_limiting': {
                'max_requests_per_minute': 100,
                'max_verifications_per_hour': 1000,
                'burst_threshold': 10
            },
            'behavior_analysis': {
                'suspicious_patterns': [
                    'rapid_fire_requests',
                    'identical_queries',
                    'price_manipulation_attempts',
                    'fake_feedback_patterns'
                ],
                'anomaly_threshold': 0.8
            },
            'data_integrity': {
                'checksum_validation': True,
                'timestamp_verification': True,
                'source_validation': True
            }
        }
        
        self.user_behavior_profiles = defaultdict(lambda: {
            'request_patterns': deque(maxlen=1000),
            'interaction_timing': deque(maxlen=100),
            'query_similarity_scores': deque(maxlen=50),
            'success_rate': 0.0,
            'risk_score': 0.0
        })
        
        self.security_events = deque(maxlen=10000)
    
    def monitor_request(self, user_id: str, request_data: Dict) -> Dict:
        """Monitor incoming request for security threats"""
        timestamp = datetime.now()
        profile = self.user_behavior_profiles[user_id]
        
        # Rate limiting check
        recent_requests = [
            t for t in profile['request_patterns'] 
            if (timestamp - t).seconds < 60
        ]
        
        if len(recent_requests) > self.security_rules['rate_limiting']['max_requests_per_minute']:
            return self._create_security_event(
                'rate_limit_exceeded',
                'medium',
                user_id,
                {'requests_in_minute': len(recent_requests)}
            )
        
        # Pattern analysis
        profile['request_patterns'].append(timestamp)
        
        # Check for suspicious patterns
        if self._detect_suspicious_patterns(user_id, request_data):
            return self._create_security_event(
                'suspicious_behavior',
                'high',
                user_id,
                {'pattern_detected': True}
            )
        
        # Data integrity validation
        if not self._validate_data_integrity(request_data):
            return self._create_security_event(
                'data_integrity_violation',
                'critical',
                user_id,
                {'validation_failed': True}
            )
        
        return {'status': 'secure', 'threat_level': 'none'}
    
    def _detect_suspicious_patterns(self, user_id: str, request_data: Dict) -> bool:
        """Detect suspicious behavior patterns"""
        profile = self.user_behavior_profiles[user_id]
        
        # Check for identical queries (possible automation)
        current_query_hash = hashlib.md5(
            json.dumps(request_data, sort_keys=True).encode()
        ).hexdigest()
        
        similarity_count = sum(
            1 for score in profile['query_similarity_scores'] 
            if score > 0.9
        )
        
        if similarity_count > 5:  # Too many similar queries
            return True
        
        # Check timing patterns (bot-like behavior)
        if len(profile['interaction_timing']) >= 5:
            timing_intervals = [
                (profile['interaction_timing'][i] - profile['interaction_timing'][i-1]).total_seconds()
                for i in range(1, len(profile['interaction_timing']))
            ]
            
            # If all intervals are too similar, it's likely automated
            if len(set([round(t, 1) for t in timing_intervals])) <= 2:
                return True
        
        return False
    
    def _validate_data_integrity(self, request_data: Dict) -> bool:
        """Validate data integrity and authenticity"""
        # Check for required fields
        required_fields = ['title', 'timestamp']
        if not all(field in request_data for field in required_fields):
            return False
        
        # Timestamp validation (not too old or in future)
        try:
            req_timestamp = datetime.fromisoformat(request_data['timestamp'].replace('Z', '+00:00'))
            now = datetime.now()
            
            # Request should be within last 5 minutes and not in future
            if (now - req_timestamp).total_seconds() > 300 or req_timestamp > now:
                return False
        except:
            return False
        
        # Check for injection attempts
        suspicious_strings = ['<script', 'javascript:', 'eval(', 'exec(']
        for value in str(request_data.values()).lower():
            if any(sus in value for sus in suspicious_strings):
                return False
        
        return True
    
    def _create_security_event(self, event_type: str, severity: str, 
                             user_id: str, details: Dict) -> Dict:
        """Create and log security event"""
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            details=details,
            timestamp=datetime.now()
        )
        
        self.security_events.append(event)
        
        # Log for monitoring
        logger.warning(f"Security Event: {event_type} | User: {user_id} | Severity: {severity}")
        
        return {
            'status': 'blocked',
            'threat_level': severity,
            'event_id': len(self.security_events),
            'message': f'Request blocked due to {event_type}'
        }

class AntiManipulationSystem:
    """System to prevent manipulation of our AI and recommendations"""
    
    def __init__(self):
        self.manipulation_detectors = {
            'fake_data_injection': self._detect_fake_data,
            'coordinated_feedback': self._detect_coordinated_feedback,
            'price_manipulation': self._detect_price_manipulation,
            'review_bombing': self._detect_review_bombing
        }
        
        self.trusted_sources = {
            'ebay_official': True,
            'verified_sellers': True,
            'established_users': True
        }
    
    def validate_listing_data(self, listing_data: Dict, source_info: Dict) -> Dict:
        """Validate listing data for manipulation attempts"""
        validation_result = {
            'is_valid': True,
            'confidence': 1.0,
            'warnings': [],
            'blocked_reasons': []
        }
        
        for detector_name, detector_func in self.manipulation_detectors.items():
            try:
                result = detector_func(listing_data, source_info)
                
                if result['threat_level'] == 'high':
                    validation_result['is_valid'] = False
                    validation_result['blocked_reasons'].append(result['reason'])
                elif result['threat_level'] == 'medium':
                    validation_result['warnings'].append(result['reason'])
                    validation_result['confidence'] *= 0.8
                
            except Exception as e:
                logger.error(f"Manipulation detector {detector_name} failed: {e}")
        
        return validation_result
    
    def _detect_fake_data(self, listing_data: Dict, source_info: Dict) -> Dict:
        """Detect potentially fake or manipulated listing data"""
        threat_level = 'low'
        reasons = []
        
        # Check for impossible price combinations
        price = listing_data.get('price', 0)
        title = listing_data.get('title', '').lower()
        
        # Detect unrealistic prices for known high-value items
        high_value_keywords = ['iphone', 'macbook', 'rolex', 'louis vuitton', 'gold']
        if any(keyword in title for keyword in high_value_keywords) and price < 50:
            threat_level = 'high'
            reasons.append('Unrealistic price for high-value item')
        
        # Check for generic/stock descriptions
        description = listing_data.get('description', '')
        if len(description) < 20 and price > 100:
            threat_level = 'medium'
            reasons.append('Minimal description for high-value item')
        
        # Check seller information consistency
        seller_info = listing_data.get('seller_info', {})
        if seller_info.get('feedback_score', 0) > 10000 and seller_info.get('account_age_days', 0) < 365:
            threat_level = 'medium'
            reasons.append('Inconsistent seller metrics')
        
        return {
            'threat_level': threat_level,
            'reason': '; '.join(reasons) if reasons else 'No issues detected'
        }
    
    def _detect_coordinated_feedback(self, listing_data: Dict, source_info: Dict) -> Dict:
        """Detect coordinated feedback manipulation"""
        # This would analyze patterns in user feedback over time
        # For now, return basic check
        return {'threat_level': 'low', 'reason': 'No coordination detected'}
    
    def _detect_price_manipulation(self, listing_data: Dict, source_info: Dict) -> Dict:
        """Detect price manipulation attempts"""
        threat_level = 'low'
        reason = 'Price appears legitimate'
        
        # Check for price anchoring attempts
        price = listing_data.get('price', 0)
        original_price = listing_data.get('original_price', price)
        
        if original_price > 0 and (original_price - price) / original_price > 0.8:
            threat_level = 'medium'
            reason = 'Excessive discount may be misleading'
        
        return {'threat_level': threat_level, 'reason': reason}
    
    def _detect_review_bombing(self, listing_data: Dict, source_info: Dict) -> Dict:
        """Detect review bombing or fake reviews"""
        # This would analyze review patterns, timing, language similarity
        return {'threat_level': 'low', 'reason': 'Review patterns appear normal'}

class ArbitrageDetector:
    """Intelligent arbitrage opportunity detection system"""
    
    def __init__(self):
        self.platforms = {
            'ebay': {'fee_percent': 12.9, 'avg_shipping': 8.50},
            'amazon': {'fee_percent': 15.0, 'avg_shipping': 0.00},
            'facebook_marketplace': {'fee_percent': 5.0, 'avg_shipping': 0.00},
            'mercari': {'fee_percent': 10.0, 'avg_shipping': 4.99},
            'poshmark': {'fee_percent': 20.0, 'avg_shipping': 7.45}
        }
        
        self.user_arbitrage_history = defaultdict(list)
        self.cross_platform_cache = {}
    
    async def find_arbitrage_opportunities(self, user_id: str, 
                                         user_preferences: Dict) -> List[ArbitrageOpportunity]:
        """Find personalized arbitrage opportunities"""
        opportunities = []
        
        # Get user's preferred categories and price ranges
        categories = user_preferences.get('favorite_categories', ['electronics'])
        max_investment = user_preferences.get('max_investment', 500)
        min_profit_margin = user_preferences.get('min_profit_margin', 0.2)
        
        for category in categories:
            try:
                # Search across platforms for price discrepancies
                platform_data = await self._fetch_cross_platform_data(category, max_investment)
                
                # Analyze for arbitrage opportunities
                category_opportunities = self._analyze_arbitrage_potential(
                    platform_data, user_preferences, user_id
                )
                
                opportunities.extend(category_opportunities)
                
            except Exception as e:
                logger.error(f"Arbitrage detection error for category {category}: {e}")
        
        # Sort by profit potential and user match score
        opportunities.sort(
            key=lambda x: x.profit_margin * x.user_match_score, 
            reverse=True
        )
        
        return opportunities[:10]  # Return top 10 opportunities
    
    async def _fetch_cross_platform_data(self, category: str, max_price: float) -> Dict:
        """Fetch pricing data across multiple platforms"""
        # This would make actual API calls to different platforms
        # For now, return mock data structure
        return {
            'ebay': [
                {'title': 'iPhone 12', 'price': 400, 'condition': 'used', 'seller_rating': 98.5},
                {'title': 'MacBook Air', 'price': 800, 'condition': 'good', 'seller_rating': 99.1}
            ],
            'facebook_marketplace': [
                {'title': 'iPhone 12', 'price': 350, 'condition': 'used', 'location': 'local'},
                {'title': 'MacBook Air', 'price': 750, 'condition': 'good', 'location': 'local'}
            ],
            'amazon': [
                {'title': 'iPhone 12', 'price': 450, 'condition': 'renewed', 'prime': True},
                {'title': 'MacBook Air', 'price': 900, 'condition': 'renewed', 'prime': True}
            ]
        }
    
    def _analyze_arbitrage_potential(self, platform_data: Dict, 
                                   user_preferences: Dict, user_id: str) -> List[ArbitrageOpportunity]:
        """Analyze cross-platform data for arbitrage opportunities"""
        opportunities = []
        min_profit = user_preferences.get('min_profit_dollars', 50)
        
        # Create item matching across platforms
        item_matches = self._match_items_across_platforms(platform_data)
        
        for item_group in item_matches:
            best_buy_option = min(item_group, key=lambda x: x['total_cost'])
            best_sell_option = max(item_group, key=lambda x: x['sell_potential'])
            
            if best_buy_option['platform'] != best_sell_option['platform']:
                # Calculate profit after fees and costs
                buy_cost = best_buy_option['total_cost']
                sell_price = best_sell_option['sell_potential']
                fees = self._calculate_total_fees(best_sell_option['platform'], sell_price)
                
                net_profit = sell_price - buy_cost - fees
                profit_margin = net_profit / buy_cost if buy_cost > 0 else 0
                
                if net_profit >= min_profit and profit_margin >= 0.15:  # 15% minimum margin
                    opportunity = ArbitrageOpportunity(
                        source_platform=best_buy_option['platform'],
                        target_platform=best_sell_option['platform'],
                        item_title=best_buy_option['title'],
                        buy_price=buy_cost,
                        sell_price=sell_price,
                        profit_margin=profit_margin,
                        confidence_score=self._calculate_confidence(item_group),
                        time_to_profit_days=self._estimate_flip_time(best_sell_option),
                        risk_level=self._assess_arbitrage_risk(item_group),
                        user_match_score=self._calculate_user_match(item_group, user_id)
                    )
                    
                    opportunities.append(opportunity)
        
        return opportunities
    
    def _match_items_across_platforms(self, platform_data: Dict) -> List[List[Dict]]:
        """Match similar items across different platforms"""
        # Simplified matching - in production would use ML similarity matching
        matched_groups = []
        
        # Get all items with platform info
        all_items = []
        for platform, items in platform_data.items():
            for item in items:
                item['platform'] = platform
                item['total_cost'] = item['price'] + self.platforms[platform]['avg_shipping']
                item['sell_potential'] = item['price'] * 1.1  # Estimate 10% markup potential
                all_items.append(item)
        
        # Group by title similarity (simplified)
        title_groups = defaultdict(list)
        for item in all_items:
            # Extract key words for matching
            key_words = ' '.join(sorted(item['title'].lower().split()[:3]))  # First 3 words
            title_groups[key_words].append(item)
        
        # Only return groups with items from multiple platforms
        matched_groups = [
            group for group in title_groups.values() 
            if len(set(item['platform'] for item in group)) > 1
        ]
        
        return matched_groups
    
    def _calculate_total_fees(self, platform: str, sell_price: float) -> float:
        """Calculate total fees for selling on platform"""
        platform_info = self.platforms.get(platform, {'fee_percent': 10.0, 'avg_shipping': 5.0})
        
        platform_fee = sell_price * (platform_info['fee_percent'] / 100)
        shipping_cost = platform_info['avg_shipping']
        payment_processing = sell_price * 0.029 + 0.30  # Standard PayPal fees
        
        return platform_fee + shipping_cost + payment_processing
    
    def _calculate_confidence(self, item_group: List[Dict]) -> float:
        """Calculate confidence score for arbitrage opportunity"""
        # Factors: price consistency, seller ratings, market activity
        price_variance = np.var([item['price'] for item in item_group])
        avg_rating = np.mean([item.get('seller_rating', 95) for item in item_group])
        
        # Lower price variance and higher ratings = higher confidence
        confidence = min(1.0, (100 - price_variance) / 100 * (avg_rating / 100))
        return max(0.1, confidence)
    
    def _estimate_flip_time(self, sell_option: Dict) -> int:
        """Estimate days to sell on target platform"""
        platform_speed = {
            'ebay': 14,
            'amazon': 7,
            'facebook_marketplace': 5,
            'mercari': 10,
            'poshmark': 21
        }
        
        base_days = platform_speed.get(sell_option['platform'], 14)
        
        # Adjust based on item condition and price point
        if sell_option.get('condition') == 'new':
            base_days *= 0.7
        elif sell_option.get('condition') == 'poor':
            base_days *= 1.5
            
        return int(base_days)
    
    def _assess_arbitrage_risk(self, item_group: List[Dict]) -> str:
        """Assess risk level of arbitrage opportunity"""
        avg_price = np.mean([item['price'] for item in item_group])
        price_spread = max(item['price'] for item in item_group) - min(item['price'] for item in item_group)
        spread_ratio = price_spread / avg_price if avg_price > 0 else 0
        
        if spread_ratio > 0.5:
            return 'HIGH'
        elif spread_ratio > 0.3:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _calculate_user_match(self, item_group: List[Dict], user_id: str) -> float:
        """Calculate how well this opportunity matches user's patterns"""
        user_history = self.user_arbitrage_history.get(user_id, [])
        
        if not user_history:
            return 0.5  # Neutral for new users
        
        # Check category match
        item_title = item_group[0]['title'].lower()
        user_categories = [h.get('category', '') for h in user_history]
        
        # Simple keyword matching (in production would use ML)
        category_match = any(
            any(word in item_title for word in cat.split()) 
            for cat in user_categories
        )
        
        # Check price range preference
        avg_price = np.mean([item['price'] for item in item_group])
        user_price_ranges = [h.get('price_range', [0, 1000]) for h in user_history]
        avg_user_price = np.mean([np.mean(pr) for pr in user_price_ranges])
        
        price_similarity = 1 - min(1, abs(avg_price - avg_user_price) / max(avg_price, avg_user_price))
        
        # Combine factors
        match_score = (0.7 * (1.0 if category_match else 0.3)) + (0.3 * price_similarity)
        return min(1.0, max(0.1, match_score))

class RealWorldWorkflowEngine:
    """Manages complete real-world workflows for buyers and sellers"""
    
    def __init__(self):
        self.workflows = {
            'buyer_journey': BuyerWorkflow(),
            'seller_journey': SellerWorkflow(),
            'flipper_journey': FlipperWorkflow()
        }
        
        self.user_journeys = defaultdict(lambda: UserJourney(
            user_id='',
            journey_type='buyer',
            current_step='discovery',
            progress_percent=0.0,
            items_in_pipeline=[],
            total_profit_tracked=0.0,
            success_rate=0.0,
            engagement_score=0.0,
            risk_alerts_avoided=0,
            arbitrage_opportunities_found=0
        ))
    
    def process_user_action(self, user_id: str, action: str, data: Dict) -> Dict:
        """Process user action and advance their journey"""
        journey = self.user_journeys[user_id]
        journey.user_id = user_id
        
        workflow = self.workflows.get(journey.journey_type)
        if not workflow:
            return {'error': 'Unknown journey type'}
        
        # Process action through appropriate workflow
        result = workflow.handle_action(journey, action, data)
        
        # Update journey progress
        self._update_journey_progress(journey, result)
        
        return result
    
    def _update_journey_progress(self, journey: UserJourney, result: Dict):
        """Update journey progress based on action result"""
        if result.get('step_completed'):
            journey.progress_percent = min(100, journey.progress_percent + result.get('progress_increment', 10))
            journey.engagement_score += result.get('engagement_points', 1)
        
        if result.get('risk_avoided'):
            journey.risk_alerts_avoided += 1
        
        if result.get('arbitrage_found'):
            journey.arbitrage_opportunities_found += 1

class BuyerWorkflow:
    """Complete buyer workflow from discovery to purchase decision"""
    
    def __init__(self):
        self.steps = {
            'discovery': self._handle_discovery,
            'verification': self._handle_verification,
            'decision': self._handle_decision,
            'purchase': self._handle_purchase,
            'feedback': self._handle_feedback
        }
    
    def handle_action(self, journey: UserJourney, action: str, data: Dict) -> Dict:
        """Handle buyer action in their journey"""
        handler = self.steps.get(journey.current_step)
        if not handler:
            return {'error': f'No handler for step: {journey.current_step}'}
        
        return handler(journey, action, data)
    
    def _handle_discovery(self, journey: UserJourney, action: str, data: Dict) -> Dict:
        """Handle item discovery phase"""
        if action == 'item_found':
            item_data = {
                'title': data.get('title'),
                'price': data.get('price'),
                'url': data.get('url'),
                'discovery_time': datetime.now().isoformat(),
                'source': data.get('source', 'manual')
            }
            
            journey.items_in_pipeline.append(item_data)
            journey.current_step = 'verification'
            
            return {
                'success': True,
                'message': '🔍 Item added to analysis pipeline',
                'next_step': 'verification',
                'step_completed': True,
                'progress_increment': 20,
                'engagement_points': 2,
                'visual_feedback': {
                    'type': 'item_added_animation',
                    'color_scheme': 'processing'
                },
                'sound_feedback': {
                    'type': 'item_scan_start',
                    'volume': 0.6
                }
            }
        
        return {'error': 'Invalid action for discovery phase'}
    
    def _handle_verification(self, journey: UserJourney, action: str, data: Dict) -> Dict:
        """Handle verification phase with engaging feedback"""
        if action == 'verify_item':
            # Simulate verification process with engaging UI
            verification_result = {
                'trust_score': data.get('trust_score', 75),
                'risk_level': data.get('risk_level', 'MEDIUM'),
                'profit_potential': data.get('profit_potential', 0),
                'time_to_sell': data.get('time_to_sell', 14)
            }
            
            # Update current item with verification results
            if journey.items_in_pipeline:
                journey.items_in_pipeline[-1]['verification'] = verification_result
            
            journey.current_step = 'decision'
            
            # Determine feedback based on results
            if verification_result['trust_score'] >= 80:
                feedback_type = 'excellent_find'
                message = '🎉 Excellent find! This looks like a safe purchase.'
                sound = 'success_celebration'
                color = 'safe_deal'
            elif verification_result['trust_score'] >= 60:
                feedback_type = 'good_opportunity'
                message = '👍 Good opportunity with manageable risk.'
                sound = 'positive_chime'
                color = 'great_deal'
            else:
                feedback_type = 'high_risk_warning'
                message = '⚠️ High risk detected! Proceed with caution.'
                sound = 'warning_alert'
                color = 'high_risk'
                journey.risk_alerts_avoided += 1
            
            return {
                'success': True,
                'verification_result': verification_result,
                'message': message,
                'next_step': 'decision',
                'step_completed': True,
                'progress_increment': 30,
                'engagement_points': 5,
                'risk_avoided': verification_result['trust_score'] < 50,
                'visual_feedback': {
                    'type': feedback_type,
                    'color_scheme': color,
                    'trust_score': verification_result['trust_score']
                },
                'sound_feedback': {
                    'type': sound,
                    'volume': 0.7
                }
            }
        
        return {'error': 'Invalid action for verification phase'}
    
    def _handle_decision(self, journey: UserJourney, action: str, data: Dict) -> Dict:
        """Handle purchase decision phase"""
        if action == 'make_decision':
            decision = data.get('decision')  # 'buy', 'skip', 'watch'
            
            if journey.items_in_pipeline:
                current_item = journey.items_in_pipeline[-1]
                current_item['decision'] = decision
                current_item['decision_time'] = datetime.now().isoformat()
            
            if decision == 'buy':
                journey.current_step = 'purchase'
                message = '💳 Great choice! Proceeding to purchase guidance.'
                sound = 'purchase_confirmed'
                progress = 20
            elif decision == 'skip':
                journey.current_step = 'discovery'  # Back to looking
                message = '👋 Smart to skip risky deals. Keep looking!'
                sound = 'wise_decision'
                progress = 10
                journey.risk_alerts_avoided += 1
            else:  # watch
                journey.current_step = 'discovery'
                message = '👀 Added to watchlist. We\'ll monitor for changes.'
                sound = 'watchlist_added'
                progress = 15
            
            return {
                'success': True,
                'decision': decision,
                'message': message,
                'step_completed': True,
                'progress_increment': progress,
                'engagement_points': 3,
                'risk_avoided': decision == 'skip',
                'visual_feedback': {
                    'type': 'decision_confirmation',
                    'decision': decision
                },
                'sound_feedback': {
                    'type': sound,
                    'volume': 0.6
                }
            }
        
        return {'error': 'Invalid action for decision phase'}
    
    def _handle_purchase(self, journey: UserJourney, action: str, data: Dict) -> Dict:
        """Handle purchase completion and guidance"""
        if action == 'purchase_completed':
            purchase_amount = data.get('amount', 0)
            
            if journey.items_in_pipeline:
                current_item = journey.items_in_pipeline[-1]
                current_item['purchased'] = True
                current_item['purchase_amount'] = purchase_amount
                current_item['purchase_time'] = datetime.now().isoformat()
            
            journey.current_step = 'feedback'
            
            return {
                'success': True,
                'message': f'🎯 Purchase completed! Amount: ${purchase_amount:.2f}',
                'next_step': 'feedback',
                'step_completed': True,
                'progress_increment': 25,
                'engagement_points': 10,
                'visual_feedback': {
                    'type': 'purchase_celebration',
                    'amount': purchase_amount
                },
                'sound_feedback': {
                    'type': 'purchase_success',
                    'volume': 0.8
                }
            }
        
        return {'error': 'Invalid action for purchase phase'}
    
    def _handle_feedback(self, journey: UserJourney, action: str, data: Dict) -> Dict:
        """Handle post-purchase feedback and learning"""
        if action == 'provide_feedback':
            feedback_data = {
                'satisfaction': data.get('satisfaction', 5),
                'accuracy': data.get('accuracy', True),
                'outcome': data.get('outcome', 'positive'),
                'feedback_time': datetime.now().isoformat()
            }
            
            if journey.items_in_pipeline:
                journey.items_in_pipeline[-1]['feedback'] = feedback_data
            
            # Calculate success rate
            completed_items = [item for item in journey.items_in_pipeline if item.get('feedback')]
            positive_outcomes = [item for item in completed_items 
                               if item.get('feedback', {}).get('outcome') == 'positive']
            
            journey.success_rate = len(positive_outcomes) / max(len(completed_items), 1)
            journey.current_step = 'discovery'  # Ready for next item
            
            # Reward points based on feedback quality
            reward_points = 5
            if feedback_data['satisfaction'] >= 4:
                reward_points += 5
            if feedback_data['accuracy']:
                reward_points += 3
            
            return {
                'success': True,
                'message': f'🙏 Thank you! +{reward_points} points earned.',
                'journey_complete': True,
                'step_completed': True,
                'progress_increment': 5,
                'engagement_points': reward_points,
                'success_rate': journey.success_rate,
                'visual_feedback': {
                    'type': 'feedback_appreciation',
                    'reward_points': reward_points
                },
                'sound_feedback': {
                    'type': 'feedback_thanks',
                    'volume': 0.5
                }
            }
        
        return {'error': 'Invalid action for feedback phase'}

class SellerWorkflow:
    """Complete seller workflow from item listing to profit tracking"""
    
    def __init__(self):
        self.steps = {
            'photo_capture': self._handle_photo_capture,
            'listing_generation': self._handle_listing_generation,
            'price_optimization': self._handle_price_optimization,
            'listing_publication': self._handle_listing_publication,
            'performance_tracking': self._handle_performance_tracking
        }
    
    def handle_action(self, journey: UserJourney, action: str, data: Dict) -> Dict:
        """Handle seller action in their journey"""
        handler = self.steps.get(journey.current_step)
        if not handler:
            return {'error': f'No handler for step: {journey.current_step}'}
        
        return handler(journey, action, data)
    
    def _handle_photo_capture(self, journey: UserJourney, action: str, data: Dict) -> Dict:
        """Handle photo capture and enhancement"""
        if action == 'photo_uploaded':
            photo_data = data.get('photo_base64')
            enhancement_options = data.get('enhancement_options', {})
            
            # Simulate AI photo analysis and enhancement
            analysis_result = {
                'detected_item': 'iPhone 13 Pro',
                'condition_estimate': 'Good',
                'quality_score': 0.85,
                'enhancement_applied': True,
                'background_removed': enhancement_options.get('remove_bg', False)
            }
            
            new_item = {
                'photos': [{'original': photo_data, 'enhanced': True}],
                'ai_analysis': analysis_result,
                'creation_time': datetime.now().isoformat()
            }
            
            journey.items_in_pipeline.append(new_item)
            journey.current_step = 'listing_generation'
            
            return {
                'success': True,
                'analysis_result': analysis_result,
                'message': f'📸 Photo enhanced! Detected: {analysis_result["detected_item"]}',
                'next_step': 'listing_generation',
                'step_completed': True,
                'progress_increment': 25,
                'engagement_points': 3,
                'visual_feedback': {
                    'type': 'photo_enhancement_complete',
                    'quality_score': analysis_result['quality_score']
                },
                'sound_feedback': {
                    'type': 'photo_processed',
                    'volume': 0.6
                }
            }
        
        return {'error': 'Invalid action for photo capture phase'}
    
    def _handle_listing_generation(self, journey: UserJourney, action: str, data: Dict) -> Dict:
        """Handle AI listing generation"""
        if action == 'generate_listing':
            user_input = data.get('user_input', {})
            
            # Simulate AI listing generation
            generated_listing = {
                'title': f"{user_input.get('brand', 'Apple')} {user_input.get('model', 'iPhone 13')} - {user_input.get('condition', 'Excellent')} Condition",
                'description': f"High-quality {user_input.get('brand', 'Apple')} device in {user_input.get('condition', 'excellent')} condition...",
                'keywords': ['smartphone', 'unlocked', 'apple', 'iphone'],
                'category_suggestions': ['Cell Phones & Accessories'],
                'seo_score': 0.92
            }
            
            if journey.items_in_pipeline:
                journey.items_in_pipeline[-1]['generated_listing'] = generated_listing
            
            journey.current_step = 'price_optimization'
            
            return {
                'success': True,
                'generated_listing': generated_listing,
                'message': f'✍️ Listing generated with {generated_listing["seo_score"]*100:.0f}% SEO score!',
                'next_step': 'price_optimization',
                'step_completed': True,
                'progress_increment': 25,
                'engagement_points': 5,
                'visual_feedback': {
                    'type': 'listing_generation_complete',
                    'seo_score': generated_listing['seo_score']
                },
                'sound_feedback': {
                    'type': 'content_generated',
                    'volume': 0.7
                }
            }
        
        return {'error': 'Invalid action for listing generation phase'}
    
    def _handle_price_optimization(self, journey: UserJourney, action: str, data: Dict) -> Dict:
        """Handle intelligent price optimization"""
        if action == 'optimize_price':
            market_data = data.get('market_data', {})
            
            # Simulate price optimization analysis
            price_analysis = {
                'suggested_price': 450.00,
                'price_range': {'min': 400.00, 'max': 500.00},
                'market_position': 'competitive',
                'expected_sell_time': 12,
                'confidence': 0.88
            }
            
            if journey.items_in_pipeline:
                journey.items_in_pipeline[-1]['price_analysis'] = price_analysis
            
            journey.current_step = 'listing_publication'
            
            return {
                'success': True,
                'price_analysis': price_analysis,
                'message': f'💰 Optimal price: ${price_analysis["suggested_price"]:.2f} (sells in ~{price_analysis["expected_sell_time"]} days)',
                'next_step': 'listing_publication',
                'step_completed': True,
                'progress_increment': 25,
                'engagement_points': 4,
                'visual_feedback': {
                    'type': 'price_optimization_complete',
                    'suggested_price': price_analysis['suggested_price'],
                    'confidence': price_analysis['confidence']
                },
                'sound_feedback': {
                    'type': 'price_calculated',
                    'volume': 0.6
                }
            }
        
        return {'error': 'Invalid action for price optimization phase'}
    
    def _handle_listing_publication(self, journey: UserJourney, action: str, data: Dict) -> Dict:
        """Handle listing publication to platforms"""
        if action == 'publish_listing':
            platforms = data.get('platforms', ['ebay'])
            
            publication_results = []
            for platform in platforms:
                publication_results.append({
                    'platform': platform,
                    'status': 'published',
                    'listing_id': f'{platform}_{int(time.time())}',
                    'url': f'https://{platform}.com/item/example'
                })
            
            if journey.items_in_pipeline:
                journey.items_in_pipeline[-1]['publications'] = publication_results
            
            journey.current_step = 'performance_tracking'
            
            return {
                'success': True,
                'publication_results': publication_results,
                'message': f'🚀 Listed on {len(platforms)} platform(s)! Tracking performance...',
                'next_step': 'performance_tracking',
                'step_completed': True,
                'progress_increment': 25,
                'engagement_points': 8,
                'visual_feedback': {
                    'type': 'listing_published',
                    'platform_count': len(platforms)
                },
                'sound_feedback': {
                    'type': 'listing_live',
                    'volume': 0.8
                }
            }
        
        return {'error': 'Invalid action for publication phase'}
    
    def _handle_performance_tracking(self, journey: UserJourney, action: str, data: Dict) -> Dict:
        """Handle listing performance tracking"""
        if action == 'track_performance':
            performance_data = {
                'views': data.get('views', 0),
                'watchers': data.get('watchers', 0),
                'messages': data.get('messages', 0),
                'days_active': data.get('days_active', 1),
                'predicted_sell_date': (datetime.now() + timedelta(days=12)).isoformat()
            }
            
            if journey.items_in_pipeline:
                journey.items_in_pipeline[-1]['performance'] = performance_data
            
            # Ready to start next item
            journey.current_step = 'photo_capture'
            
            return {
                'success': True,
                'performance_data': performance_data,
                'message': f'📊 Tracking: {performance_data["views"]} views, {performance_data["watchers"]} watchers',
                'journey_cycle_complete': True,
                'engagement_points': 2,
                'visual_feedback': {
                    'type': 'performance_dashboard',
                    'metrics': performance_data
                },
                'sound_feedback': {
                    'type': 'data_update',
                    'volume': 0.4
                }
            }
        
        return {'error': 'Invalid action for performance tracking phase'}

class FlipperWorkflow:
    """Advanced workflow for profit-focused flippers with arbitrage detection"""
    
    def __init__(self):
        self.steps = {
            'opportunity_scan': self._handle_opportunity_scan,
            'profit_analysis': self._handle_profit_analysis,
            'acquisition': self._handle_acquisition,
            'optimization': self._handle_optimization,
            'profit_realization': self._handle_profit_realization
        }
    
    def handle_action(self, journey: UserJourney, action: str, data: Dict) -> Dict:
        """Handle flipper action in their journey"""
        handler = self.steps.get(journey.current_step)
        if not handler:
            return {'error': f'No handler for step: {journey.current_step}'}
        
        return handler(journey, action, data)
    
    def _handle_opportunity_scan(self, journey: UserJourney, action: str, data: Dict) -> Dict:
        """Handle automated opportunity scanning"""
        if action == 'scan_opportunities':
            # Simulate finding arbitrage opportunities
            opportunities = [
                {
                    'item': 'MacBook Air M1',
                    'buy_price': 750.00,
                    'sell_price': 900.00,
                    'profit_potential': 120.00,  # After fees
                    'confidence': 0.92,
                    'platform_buy': 'Facebook Marketplace',
                    'platform_sell': 'eBay',
                    'risk_level': 'LOW'
                },
                {
                    'item': 'PlayStation 5',
                    'buy_price': 400.00,
                    'sell_price': 520.00,
                    'profit_potential': 85.00,
                    'confidence': 0.85,
                    'platform_buy': 'Craigslist',
                    'platform_sell': 'Amazon',
                    'risk_level': 'MEDIUM'
                }
            ]
            
            journey.arbitrage_opportunities_found += len(opportunities)
            journey.current_step = 'profit_analysis'
            
            return {
                'success': True,
                'opportunities': opportunities,
                'message': f'🔍 Found {len(opportunities)} profit opportunities!',
                'next_step': 'profit_analysis',
                'step_completed': True,
                'progress_increment': 20,
                'engagement_points': 10,
                'arbitrage_found': True,
                'visual_feedback': {
                    'type': 'opportunities_discovered',
                    'opportunity_count': len(opportunities)
                },
                'sound_feedback': {
                    'type': 'opportunity_alert',
                    'volume': 0.7
                }
            }
        
        return {'error': 'Invalid action for opportunity scan phase'}
    
    def _handle_profit_analysis(self, journey: UserJourney, action: str, data: Dict) -> Dict:
        """Handle detailed profit analysis"""
        if action == 'analyze_profit':
            selected_opportunity = data.get('selected_opportunity', {})
            
            # Deep profit analysis
            profit_breakdown = {
                'buy_price': selected_opportunity.get('buy_price', 0),
                'estimated_sell_price': selected_opportunity.get('sell_price', 0),
                'platform_fees': selected_opportunity.get('sell_price', 0) * 0.129,  # eBay fees
                'shipping_costs': 12.50,
                'time_investment_hours': 3,
                'net_profit': 0,
                'roi_percent': 0,
                'profit_per_hour': 0
            }
            
            profit_breakdown['net_profit'] = (
                profit_breakdown['estimated_sell_price'] - 
                profit_breakdown['buy_price'] - 
                profit_breakdown['platform_fees'] - 
                profit_breakdown['shipping_costs']
            )
            
            profit_breakdown['roi_percent'] = (
                profit_breakdown['net_profit'] / profit_breakdown['buy_price'] * 100
            )
            
            profit_breakdown['profit_per_hour'] = (
                profit_breakdown['net_profit'] / profit_breakdown['time_investment_hours']
            )
            
            journey.current_step = 'acquisition'
            
            return {
                'success': True,
                'profit_breakdown': profit_breakdown,
                'message': f'💎 Net profit: ${profit_breakdown["net_profit"]:.2f} ({profit_breakdown["roi_percent"]:.1f}% ROI)',
                'next_step': 'acquisition',
                'step_completed': True,
                'progress_increment': 25,
                'engagement_points': 5,
                'visual_feedback': {
                    'type': 'profit_analysis_complete',
                    'profit_breakdown': profit_breakdown
                },
                'sound_feedback': {
                    'type': 'profit_calculated',
                    'volume': 0.8
                }
            }
        
        return {'error': 'Invalid action for profit analysis phase'}
    
    def _handle_acquisition(self, journey: UserJourney, action: str, data: Dict) -> Dict:
        """Handle item acquisition"""
        if action == 'acquire_item':
            acquisition_data = {
                'purchase_price': data.get('actual_price', 0),
                'acquisition_date': datetime.now().isoformat(),
                'condition': data.get('condition', 'good'),
                'acquisition_platform': data.get('platform', 'unknown')
            }
            
            item_data = {
                'acquisition': acquisition_data,
                'target_profit': data.get('target_profit', 0)
            }
            
            journey.items_in_pipeline.append(item_data)
            journey.current_step = 'optimization'
            
            return {
                'success': True,
                'acquisition_data': acquisition_data,
                'message': f'✅ Item acquired for ${acquisition_data["purchase_price"]:.2f}!',
                'next_step': 'optimization',
                'step_completed': True,
                'progress_increment': 25,
                'engagement_points': 8,
                'visual_feedback': {
                    'type': 'item_acquired',
                    'purchase_price': acquisition_data['purchase_price']
                },
                'sound_feedback': {
                    'type': 'acquisition_success',
                    'volume': 0.7
                }
            }
        
        return {'error': 'Invalid action for acquisition phase'}
    
    def _handle_optimization(self, journey: UserJourney, action: str, data: Dict) -> Dict:
        """Handle item optimization for maximum profit"""
        if action == 'optimize_item':
            optimization_actions = data.get('actions', [])
            
            # Simulate optimization results
            optimization_results = {
                'photos_enhanced': 'photos' in optimization_actions,
                'listing_optimized': 'listing' in optimization_actions,
                'price_adjusted': 'pricing' in optimization_actions,
                'cross_posted': 'cross_post' in optimization_actions,
                'estimated_value_increase': 0
            }
            
            # Calculate value increase from optimizations
            base_increase = 0
            if optimization_results['photos_enhanced']:
                base_increase += 15  # 15% increase from better photos
            if optimization_results['listing_optimized']:
                base_increase += 10  # 10% increase from SEO optimization
            if optimization_results['price_adjusted']:
                base_increase += 8   # 8% increase from optimal pricing
            if optimization_results['cross_posted']:
                base_increase += 12  # 12% increase from more exposure
            
            optimization_results['estimated_value_increase'] = base_increase
            
            if journey.items_in_pipeline:
                journey.items_in_pipeline[-1]['optimization'] = optimization_results
            
            journey.current_step = 'profit_realization'
            
            return {
                'success': True,
                'optimization_results': optimization_results,
                'message': f'🚀 Optimization complete! +{base_increase}% estimated value increase',
                'next_step': 'profit_realization',
                'step_completed': True,
                'progress_increment': 20,
                'engagement_points': 6,
                'visual_feedback': {
                    'type': 'optimization_complete',
                    'value_increase': base_increase
                },
                'sound_feedback': {
                    'type': 'optimization_success',
                    'volume': 0.6
                }
            }
        
        return {'error': 'Invalid action for optimization phase'}
    
    def _handle_profit_realization(self, journey: UserJourney, action: str, data: Dict) -> Dict:
        """Handle final profit realization and tracking"""
        if action == 'item_sold':
            sale_data = {
                'sell_price': data.get('sell_price', 0),
                'sell_date': datetime.now().isoformat(),
                'sell_platform': data.get('platform', 'ebay'),
                'days_to_sell': data.get('days_to_sell', 14)
            }
            
            # Calculate actual profit
            if journey.items_in_pipeline:
                current_item = journey.items_in_pipeline[-1]
                acquisition_price = current_item.get('acquisition', {}).get('purchase_price', 0)
                
                # Calculate fees and costs
                platform_fees = sale_data['sell_price'] * 0.129  # eBay fees
                shipping_costs = 12.50
                actual_profit = sale_data['sell_price'] - acquisition_price - platform_fees - shipping_costs
                
                sale_data['actual_profit'] = actual_profit
                sale_data['roi_percent'] = (actual_profit / acquisition_price * 100) if acquisition_price > 0 else 0
                
                current_item['sale'] = sale_data
                journey.total_profit_tracked += actual_profit
            
            # Ready for next opportunity
            journey.current_step = 'opportunity_scan'
            
            # Celebration level based on profit
            if sale_data.get('actual_profit', 0) > 100:
                celebration_level = 'major_win'
                sound = 'big_profit_celebration'
            elif sale_data.get('actual_profit', 0) > 50:
                celebration_level = 'good_profit'
                sound = 'profit_success'
            else:
                celebration_level = 'small_win'
                sound = 'sale_complete'
            
            return {
                'success': True,
                'sale_data': sale_data,
                'total_profit': journey.total_profit_tracked,
                'message': f'💰 SOLD! Profit: ${sale_data.get("actual_profit", 0):.2f} | Total: ${journey.total_profit_tracked:.2f}',
                'journey_cycle_complete': True,
                'progress_increment': 10,
                'engagement_points': 15,
                'visual_feedback': {
                    'type': celebration_level,
                    'profit_amount': sale_data.get('actual_profit', 0),
                    'total_profit': journey.total_profit_tracked
                },
                'sound_feedback': {
                    'type': sound,
                    'volume': 0.9
                }
            }
        
        return {'error': 'Invalid action for profit realization phase'}

class ComprehensiveUXOrchestrator:
    """Main orchestrator that brings everything together"""
    
    def __init__(self):
        self.ux_engine = GameifiedUXEngine()
        self.workflow_engine = RealWorldWorkflowEngine()
        self.security_monitor = SecurityMonitor()
        self.anti_manipulation = AntiManipulationSystem()
        self.arbitrage_detector = ArbitrageDetector()
        
        # User session management
        self.active_sessions = {}
        
        # Real-time notifications
        self.notification_queue = defaultdict(list)
    
    async def process_user_interaction(self, user_id: str, interaction_type: str, 
                                     interaction_data: Dict) -> Dict:
        """Process any user interaction through the complete UX system"""
        
        # Security check first
        security_result = self.security_monitor.monitor_request(user_id, {
            'interaction_type': interaction_type,
            'data': interaction_data,
            'timestamp': datetime.now().isoformat()
        })
        
        if security_result.get('status') != 'secure':
            return {
                'success': False,
                'error': 'Security check failed',
                'details': security_result,
                'visual_feedback': {
                    'type': 'security_block',
                    'color_scheme': 'high_risk'
                }
            }
        
        # Anti-manipulation check
        manipulation_check = self.anti_manipulation.validate_listing_data(
            interaction_data, {'user_id': user_id}
        )
        
        if not manipulation_check['is_valid']:
            return {
                'success': False,
                'error': 'Data validation failed',
                'details': manipulation_check,
                'visual_feedback': {
                    'type': 'manipulation_detected',
                    'color_scheme': 'high_risk'
                }
            }
        
        # Process through workflow engine
        workflow_result = self.workflow_engine.process_user_action(
            user_id, interaction_type, interaction_data
        )
        
        # Check for achievements
        achievements = self.ux_engine.achievement_system.check_achievements(
            user_id, interaction_type, interaction_data
        )
        
        # Generate sound feedback
        sound_feedback = self.ux_engine.sound_engine.play_sound(
            user_id, 
            workflow_result.get('sound_feedback', {}).get('type', 'interaction'),
            workflow_result.get('sound_feedback', {})
        )
        
        # Generate visual feedback
        visual_feedback = self.ux_engine.visual_engine.create_visual_feedback(
            workflow_result.get('visual_feedback', {}).get('type', 'default'),
            workflow_result.get('visual_feedback', {})
        )
        
        # Check for arbitrage opportunities if user is interested
        arbitrage_opportunities = []
        user_journey = self.workflow_engine.user_journeys[user_id]
        if user_journey.journey_type in ['flipper', 'seller'] and interaction_type == 'scan_opportunities':
            try:
                arbitrage_opportunities = await self.arbitrage_detector.find_arbitrage_opportunities(
                    user_id,
                    interaction_data.get('user_preferences', {})
                )
            except Exception as e:
                logger.error(f"Arbitrage detection failed: {e}")
        
        # Compile comprehensive response
        response = {
            'success': True,
            'workflow_result': workflow_result,
            'achievements': achievements,
            'sound_feedback': sound_feedback,
            'visual_feedback': visual_feedback,
            'arbitrage_opportunities': arbitrage_opportunities,
            'user_journey': {
                'current_step': user_journey.current_step,
                'progress_percent': user_journey.progress_percent,
                'engagement_score': user_journey.engagement_score,
                'total_profit': user_journey.total_profit_tracked,
                'success_rate': user_journey.success_rate,
                'risk_alerts_avoided': user_journey.risk_alerts_avoided
            },
            'security_status': security_result,
            'manipulation_score': manipulation_check['confidence'],
            'session_id': self._get_or_create_session(user_id)
        }
        
        # Queue any notifications
        if achievements:
            for achievement in achievements:
                self.notification_queue[user_id].append({
                    'type': 'achievement',
                    'data': achievement,
                    'timestamp': datetime.now().isoformat()
                })
        
        if arbitrage_opportunities:
            self.notification_queue[user_id].append({
                'type': 'arbitrage_alert',
                'data': {'count': len(arbitrage_opportunities)},
                'timestamp': datetime.now().isoformat()
            })
        
        return response
    
    def get_real_time_dashboard(self, user_id: str) -> Dict:
        """Get real-time dashboard with all user metrics and opportunities"""
        user_journey = self.workflow_engine.user_journeys[user_id]
        
        # Calculate streak information
        recent_items = user_journey.items_in_pipeline[-10:] if user_journey.items_in_pipeline else []
        current_streak = 0
        for item in reversed(recent_items):
            if item.get('feedback', {}).get('outcome') == 'positive':
                current_streak += 1
            else:
                break
        
        # Get pending notifications
        notifications = self.notification_queue.get(user_id, [])
        
        # Calculate daily/weekly stats
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        
        daily_profit = sum(
            item.get('sale', {}).get('actual_profit', 0)
            for item in user_journey.items_in_pipeline
            if item.get('sale', {}).get('sell_date', '') >= today_start.isoformat()
        )
        
        weekly_profit = sum(
            item.get('sale', {}).get('actual_profit', 0)
            for item in user_journey.items_in_pipeline
            if item.get('sale', {}).get('sell_date', '') >= week_start.isoformat()
        )
        
        return {
            'user_stats': {
                'journey_type': user_journey.journey_type,
                'current_step': user_journey.current_step,
                'progress_percent': user_journey.progress_percent,
                'engagement_score': user_journey.engagement_score,
                'current_streak': current_streak,
                'total_profit': user_journey.total_profit_tracked,
                'daily_profit': daily_profit,
                'weekly_profit': weekly_profit,
                'success_rate': user_journey.success_rate,
                'risk_alerts_avoided': user_journey.risk_alerts_avoided,
                'arbitrage_found': user_journey.arbitrage_opportunities_found
            },
            'active_items': [
                item for item in user_journey.items_in_pipeline
                if not item.get('sale')  # Not yet sold
            ],
            'recent_sales': [
                item for item in user_journey.items_in_pipeline
                if item.get('sale')  # Already sold
            ][-5:],  # Last 5 sales
            'notifications': notifications,
            'achievement_progress': self._get_achievement_progress(user_id),
            'next_milestones': self._get_next_milestones(user_id),
            'personalized_tips': self._get_personalized_tips(user_id)
        }
    
    def _get_or_create_session(self, user_id: str) -> str:
        """Get or create user session"""
        session_id = f"{user_id}_{int(time.time())}"
        if user_id not in self.active_sessions:
            self.active_sessions[user_id] = {
                'session_id': session_id,
                'start_time': datetime.now().isoformat(),
                'interactions': 0
            }
        
        self.active_sessions[user_id]['interactions'] += 1
        return self.active_sessions[user_id]['session_id']
    
    def _get_achievement_progress(self, user_id: str) -> Dict:
        """Get progress toward next achievements"""
        stats = self.ux_engine.achievement_system.user_stats[user_id]
        unlocked = self.ux_engine.achievement_system.user_achievements[user_id]
        
        progress = {}
        
        # Bargain hunter progress (need 10 items saved from)
        if 'bargain_hunter' not in unlocked:
            progress['bargain_hunter'] = {
                'current': stats['items_saved_from'],
                'target': 10,
                'percent': min(100, stats['items_saved_from'] / 10 * 100)
            }
        
        # Profit master progress (need $1000 profit)
        if 'profit_master' not in unlocked:
            progress['profit_master'] = {
                'current': stats['total_profit_made'],
                'target': 1000,
                'percent': min(100, stats['total_profit_made'] / 1000 * 100)
            }
        
        return progress
    
    def _get_next_milestones(self, user_id: str) -> List[Dict]:
        """Get next milestones user can achieve"""
        stats = self.ux_engine.achievement_system.user_stats[user_id]
        
        milestones = []
        
        # Profit milestones
        profit_levels = [100, 500, 1000, 5000, 10000]
        for level in profit_levels:
            if stats['total_profit_made'] < level:
                remaining = level - stats['total_profit_made']
                milestones.append({
                    'type': 'profit',
                    'target': level,
                    'remaining': remaining,
                    'reward': f'${level} Profit Club membership'
                })
                break
        
        # Streak milestones
        if stats['current_streak'] < 10:
            milestones.append({
                'type': 'streak',
                'target': 10,
                'remaining': 10 - stats['current_streak'],
                'reward': 'Streak Master badge + bonus features'
            })
        
        return milestones[:3]  # Top 3 next milestones
    
    def _get_personalized_tips(self, user_id: str) -> List[str]:
        """Get personalized tips based on user behavior"""
        user_journey = self.workflow_engine.user_journeys[user_id]
        tips = []
        
        # Journey-specific tips
        if user_journey.journey_type == 'buyer':
            if user_journey.risk_alerts_avoided < 3:
                tips.append("💡 Tip: Trust our risk alerts - they've saved other users thousands!")
            
            if user_journey.success_rate < 0.8:
                tips.append("🎯 Tip: Follow our BUY recommendations more closely for better outcomes")
        
        elif user_journey.journey_type == 'seller':
            tips.append("📸 Tip: Enhanced photos increase sales by 40% on average")
            tips.append("✍️ Tip: AI-generated listings get 25% more views")
        
        elif user_journey.journey_type == 'flipper':
            if user_journey.arbitrage_opportunities_found < 5:
                tips.append("🔄 Tip: Check arbitrage scanner daily for the best opportunities")
            
            tips.append(f"💰 Tip: Your average profit per flip: ${user_journey.total_profit_tracked / max(len(user_journey.items_in_pipeline), 1):.2f}")
        
        # Engagement tips
        if user_journey.engagement_score < 20:
            tips.append("⭐ Tip: Complete your profile to unlock premium features")
        
        return tips[:3]  # Top 3 tips

# Example usage and testing
async def demo_comprehensive_ux():
    """Demonstrate the comprehensive UX system"""
    orchestrator = ComprehensiveUXOrchestrator()
    
    # Simulate buyer journey
    print("=== BUYER JOURNEY DEMO ===")
    
    # User finds an item
    result1 = await orchestrator.process_user_interaction(
        'buyer_123',
        'item_found',
        {
            'title': 'iPhone 13 Pro Max 256GB Unlocked',
            'price': 800,
            'url': 'https://ebay.com/item/example'
        }
    )
    print(f"Step 1: {result1['workflow_result']['message']}")
    
    # User verifies the item
    result2 = await orchestrator.process_user_interaction(
        'buyer_123',
        'verify_item',
        {
            'trust_score': 85,
            'risk_level': 'LOW',
            'profit_potential': 150
        }
    )
    print(f"Step 2: {result2['workflow_result']['message']}")
    
    # User makes decision
    result3 = await orchestrator.process_user_interaction(
        'buyer_123',
        'make_decision',
        {'decision': 'buy'}
    )
    print(f"Step 3: {result3['workflow_result']['message']}")
    
    # Show dashboard
    dashboard = orchestrator.get_real_time_dashboard('buyer_123')
    print(f"\nDashboard: Progress {dashboard['user_stats']['progress_percent']}%")
    print(f"Engagement Score: {dashboard['user_stats']['engagement_score']}")
    
    print("\n=== FLIPPER JOURNEY DEMO ===")
    
    # Flipper scans for opportunities
    result4 = await orchestrator.process_user_interaction(
        'flipper_456',
        'scan_opportunities',
        {
            'user_preferences': {
                'favorite_categories': ['electronics'],
                'max_investment': 1000,
                'min_profit_margin': 0.2
            }
        }
    )
    print(f"Arbitrage scan: {result4['workflow_result']['message']}")
    print(f"Found {len(result4['arbitrage_opportunities'])} opportunities")
    
    return orchestrator

if __name__ == "__main__":
    # Run the demo
    import asyncio
    orchestrator = asyncio.run(demo_comprehensive_ux())
