# app_production.py
"""
Production-Ready Strategic eBay Intelligence Platform
Integrates all components: real-time verification, strategic decisions, 
learning systems, multi-revenue streams, and SaaS infrastructure
"""

import os
import asyncio
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
import aiohttp
import logging
from dataclasses import asdict

# Import our strategic components
from realtime_verification_engine import RealTimeVerificationEngine, FastVerificationService
from strategic_decision_engine import StrategicDecisionEngine, Decision
from server_model import EnhancedServerModel, FEATURE_KEYS
from config import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(APP_LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=["chrome-extension://*", "https://*.ebay.com", "http://localhost:*"])

# Rate limiting with Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per hour"],
    storage_uri="redis://localhost:6379"
)

# Global components
verification_engine = None
strategic_engine = None
ml_model = None

# Performance monitoring
performance_stats = {
    'requests_processed': 0,
    'avg_response_time': 0,
    'accuracy_score': 0,
    'user_satisfaction': 0,
    'uptime_start': datetime.now()
}

@app.before_first_request
def initialize_services():
    """Initialize all services on startup"""
    global verification_engine, strategic_engine, ml_model
    
    logger.info("🚀 Initializing Strategic eBay Intelligence Platform...")
    
    # Initialize ML model
    ml_model = EnhancedServerModel(
        model_path=MODEL_PATH,
        backup_interval=MODEL_BACKUP_INTERVAL
    )
    logger.info(f"✅ ML Model loaded: version {ml_model.model_version}")
    
    # Initialize strategic decision engine
    strategic_engine = StrategicDecisionEngine()
    logger.info("✅ Strategic Decision Engine initialized")
    
    # Initialize verification engine (async will be handled per request)
    logger.info("✅ Real-Time Verification Engine ready")
    
    # Validate configuration
    config_issues = validate_config()
    if config_issues:
        for issue in config_issues:
            logger.warning(issue)
    
    logger.info("🎯 Platform ready - serving next-generation eBay intelligence")

@app.before_request
def before_request():
    """Track request timing and user context"""
    g.start_time = time.time()
    g.user_id = request.headers.get('X-User-ID', 'anonymous')
    g.subscription_tier = request.headers.get('X-Subscription-Tier', 'free')
    
    # Request logging for analytics
    logger.info(f"Request: {request.method} {request.path} | User: {g.user_id} | Tier: {g.subscription_tier}")

@app.after_request
def after_request(response):
    """Track performance metrics and user satisfaction"""
    if hasattr(g, 'start_time'):
        response_time = (time.time() - g.start_time) * 1000
        
        # Update global stats
        performance_stats['requests_processed'] += 1
        performance_stats['avg_response_time'] = (
            (performance_stats['avg_response_time'] * (performance_stats['requests_processed'] - 1) + response_time) 
            / performance_stats['requests_processed']
        )
        
        # Add performance headers
        response.headers['X-Response-Time'] = f"{response_time:.0f}ms"
        response.headers['X-Server-Version'] = "2.1.1-strategic"
        
        logger.info(f"Response: {response.status_code} | Time: {response_time:.0f}ms | User: {g.user_id}")
    
    return response

# ===============================
# CORE VERIFICATION ENDPOINTS
# ===============================

@app.route("/verify-instant", methods=["POST"])
@limiter.limit("100 per minute")
async def verify_instant():
    """
    Ultra-fast verification with strategic decision making
    This is the main endpoint that combines all our intelligence
    """
    start_time = time.time()
    
    try:
        data = request.get_json() or {}
        
        # Validate subscription limits
        if not validate_subscription_limits(g.subscription_tier, g.user_id):
            return jsonify({
                "error": "Subscription limit exceeded",
                "upgrade_url": "/pricing",
                "limits": get_subscription_limits(g.subscription_tier)
            }), 429
        
        # Extract listing data
        listing_data = {
            'title': data.get('title', '').strip(),
            'price': data.get('price', data.get('buy_price', 0)),
            'listing_price': data.get('listing_price', data.get('price', 0)),
            'seller_info': data.get('seller_info', {}),
            'description': data.get('description', ''),
            'category': data.get('category', ''),
            'photos': data.get('photos', []),
            'shipping_info': data.get('shipping_info', {}),
            'return_policy': data.get('return_policy', {}),
            'item_specifics': data.get('item_specifics', {})
        }
        
        if not listing_data['title']:
            return jsonify({"error": "Title is required"}), 400
        
        # Perform instant verification using our real-time engine
        async with FastVerificationService(EBAY_APP_ID) as verifier:
            verification_result = await verifier.verify_listing_instantly(listing_data)
        
        # Extract market data for strategic analysis
        market_analysis = {
            'market_value': data.get('market_value', 0),
            'profit': data.get('profit', 0),
            'profit_margin_percent': data.get('profit_margin_percent', 0),
            'sold_count': verification_result.similar_items_found,
            'active_count': verification_result.similar_items_found,
            'risk_score': verification_result.trust_score / 100,
            'features': extract_features_for_ml(listing_data, verification_result)
        }
        
        # Make strategic recommendation
        strategic_recommendation = strategic_engine.make_strategic_decision(
            market_analysis, 
            user_preferences=get_user_preferences(g.user_id)
        )
        
        # Combine results into comprehensive response
        response_data = {
            # Core verification results
            "trust_score": verification_result.trust_score,
            "decision": verification_result.decision,
            "risk_level": verification_result.risk_level,
            "confidence": verification_result.confidence,
            "processing_time_ms": int((time.time() - start_time) * 1000),
            
            # Strategic insights
            "strategic_decision": strategic_recommendation.decision.value,
            "profit_potential": strategic_recommendation.profit_potential,
            "time_to_sell": strategic_recommendation.time_to_sell,
            "market_strength": strategic_recommendation.market_strength,
            "primary_reason": strategic_recommendation.primary_reason,
            "quick_summary": strategic_recommendation.quick_summary,
            
            # Trust signals for UI
            "trust_signals": [asdict(signal) for signal in strategic_recommendation.trust_signals],
            "visual_indicators": {
                "market_activity": verification_result.market_velocity,
                "seller_quality": get_seller_tier(listing_data.get('seller_info', {})),
                "listing_quality": assess_listing_quality(listing_data)
            },
            
            # Advanced analytics (for paid tiers)
            "advanced_analytics": get_advanced_analytics(listing_data, g.subscription_tier),
            
            # Learning feedback
            "similar_items_analyzed": verification_result.similar_items_found,
            "template_match_score": verification_result.template_match,
            "cross_validation_score": strategic_recommendation.cross_validation_score,
            
            # Subscription info
            "subscription_tier": g.subscription_tier,
            "remaining_verifications": get_remaining_verifications(g.user_id, g.subscription_tier)
        }
        
        # Track usage for billing
        track_usage(g.user_id, 'verification', g.subscription_tier)
        
        # Log successful verification for analytics
        log_verification_success(listing_data, response_data, g.user_id)
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Verification error: {e}", exc_info=True)
        return jsonify({
            "error": "Verification failed",
            "message": str(e),
            "processing_time_ms": int((time.time() - start_time) * 1000),
            "fallback_recommendation": "CAUTION - Unable to verify, proceed carefully"
        }), 500

@app.route("/verify-batch", methods=["POST"])
@limiter.limit("10 per minute")
async def verify_batch():
    """Batch verification for power users"""
    if g.subscription_tier == 'free':
        return jsonify({"error": "Batch verification requires Pro subscription"}), 403
    
    data = request.get_json() or {}
    items = data.get('items', [])
    
    if len(items) > 50:
        return jsonify({"error": "Maximum 50 items per batch"}), 400
    
    results = []
    
    async with FastVerificationService(EBAY_APP_ID) as verifier:
        for item in items:
            try:
                result = await verifier.verify_listing_instantly(item)
                results.append({
                    "item_id": item.get('id', ''),
                    "title": item.get('title', ''),
                    "verification": asdict(result),
                    "status": "success"
                })
            except Exception as e:
                results.append({
                    "item_id": item.get('id', ''),
                    "title": item.get('title', ''),
                    "error": str(e),
                    "status": "failed"
                })
    
    # Track batch usage
    track_usage(g.user_id, 'batch_verification', g.subscription_tier, quantity=len(items))
    
    return jsonify({
        "results": results,
        "processed": len(results),
        "successful": len([r for r in results if r['status'] == 'success']),
        "failed": len([r for r in results if r['status'] == 'failed'])
    })

# ===============================
# SELLER TOOLS ENDPOINTS
# ===============================

@app.route("/generate-listing", methods=["POST"])
@limiter.limit("50 per hour")
async def generate_listing():
    """AI-powered listing generation for sellers"""
    if g.subscription_tier == 'free':
        return jsonify({"error": "Listing generation requires Seller subscription"}), 403
    
    try:
        data = request.get_json() or {}
        
        # Handle photo upload
        photo_data = data.get('photo_base64')
        if not photo_data:
            return jsonify({"error": "Product photo is required"}), 400
        
        # Extract product information from photo and user input
        product_analysis = await analyze_product_from_photo(photo_data)
        
        # Generate optimized listing
        listing_content = await generate_optimized_listing(
            product_analysis,
            user_input=data.get('user_input', {}),
            market_research=True
        )
        
        # Get pricing recommendations
        pricing_suggestion = await get_pricing_recommendations(
            product_analysis['category'],
            product_analysis['brand'],
            product_analysis['condition']
        )
        
        # Track usage
        track_usage(g.user_id, 'listing_generation', g.subscription_tier)
        
        return jsonify({
            "listing": listing_content,
            "pricing": pricing_suggestion,
            "product_analysis": product_analysis,
            "seo_score": calculate_seo_score(listing_content),
            "estimated_views": estimate_listing_views(listing_content),
            "optimization_tips": get_optimization_tips(listing_content)
        })
        
    except Exception as e:
        logger.error(f"Listing generation error: {e}", exc_info=True)
        return jsonify({"error": "Listing generation failed", "message": str(e)}), 500

@app.route("/enhance-photo", methods=["POST"])
@limiter.limit("100 per hour") 
async def enhance_photo():
    """AI photo enhancement for listings"""
    if g.subscription_tier == 'free':
        return jsonify({"error": "Photo enhancement requires Seller subscription"}), 403
    
    try:
        data = request.get_json() or {}
        photo_base64 = data.get('photo_base64')
        
        if not photo_base64:
            return jsonify({"error": "Photo data is required"}), 400
        
        # Process photo enhancement
        enhanced_photos = await enhance_product_photos(
            photo_base64,
            enhancement_type=data.get('enhancement_type', 'standard'),
            background_removal=data.get('remove_background', False)
        )
        
        track_usage(g.user_id, 'photo_enhancement', g.subscription_tier)
        
        return jsonify(enhanced_photos)
        
    except Exception as e:
        logger.error(f"Photo enhancement error: {e}", exc_info=True)
        return jsonify({"error": "Photo enhancement failed", "message": str(e)}), 500

# ===============================
# ANALYTICS & INSIGHTS ENDPOINTS
# ===============================

@app.route("/market-insights", methods=["GET"])
@limiter.limit("200 per hour")
async def market_insights():
    """Real-time market intelligence"""
    try:
        category = request.args.get('category', 'all')
        timeframe = request.args.get('timeframe', '7d')
        
        insights = await generate_market_insights(
            category=category,
            timeframe=timeframe,
            subscription_tier=g.subscription_tier
        )
        
        track_usage(g.user_id, 'market_insights', g.subscription_tier)
        
        return jsonify(insights)
        
    except Exception as e:
        logger.error(f"Market insights error: {e}", exc_info=True)
        return jsonify({"error": "Failed to generate market insights"}), 500

@app.route("/user-dashboard", methods=["GET"])
@limiter.limit("100 per hour")
def user_dashboard():
    """Personalized user dashboard with performance metrics"""
    try:
        user_stats = get_user_statistics(g.user_id)
        recent_activity = get_recent_activity(g.user_id, limit=20)
        performance_metrics = calculate_user_performance(g.user_id)
        recommendations = get_personalized_recommendations(g.user_id)
        
        return jsonify({
            "user_stats": user_stats,
            "recent_activity": recent_activity,
            "performance_metrics": performance_metrics,
            "recommendations": recommendations,
            "subscription_info": get_subscription_info(g.user_id)
        })
        
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        return jsonify({"error": "Failed to load dashboard"}), 500

# ===============================
# LEARNING & FEEDBACK ENDPOINTS
# ===============================

@app.route("/feedback", methods=["POST"])
@limiter.limit("1000 per hour")
def submit_feedback():
    """Enhanced feedback system for continuous learning"""
    try:
        data = request.get_json() or {}
        
        feedback_data = {
            "user_id": g.user_id,
            "item_id": data.get('item_id'),
            "feedback_type": data.get('feedback_type'),  # 'accuracy', 'outcome', 'feature_request'
            "rating": data.get('rating'),  # 1-5 stars
            "prediction_accuracy": data.get('prediction_accuracy'),  # 'correct', 'incorrect'
            "actual_outcome": data.get('actual_outcome'),  # 'profit', 'loss', 'broke_even'
            "actual_profit": data.get('actual_profit'),  # Actual profit/loss amount
            "time_to_sell": data.get('time_to_sell'),  # Actual days to sell
            "comment": data.get('comment', ''),
            "features": data.get('features', {}),  # Original features for ML update
            "timestamp": datetime.now().isoformat()
        }
        
        # Store feedback for analysis
        store_feedback(feedback_data)
        
        # Update ML model if outcome data provided
        if feedback_data.get('prediction_accuracy') and feedback_data.get('features'):
            label = 1 if feedback_data['prediction_accuracy'] == 'incorrect' else 0
            ml_model.online_update(feedback_data['features'], label)
        
        # Update user reputation score
        update_user_reputation(g.user_id, feedback_data)
        
        # Reward user for feedback
        reward_points = calculate_feedback_reward(feedback_data)
        add_user_rewards(g.user_id, reward_points)
        
        return jsonify({
            "status": "success",
            "message": "Thank you for your feedback!",
            "reward_points": reward_points,
            "updated_accuracy": ml_model.monitor.get_accuracy_metrics()
        })
        
    except Exception as e:
        logger.error(f"Feedback error: {e}", exc_info=True)
        return jsonify({"error": "Failed to process feedback"}), 500

# ===============================
# SUBSCRIPTION & BILLING
# ===============================

@app.route("/subscription/status", methods=["GET"])
def subscription_status():
    """Get current subscription status and usage"""
    try:
        status = get_subscription_status(g.user_id)
        usage = get_usage_statistics(g.user_id)
        
        return jsonify({
            "subscription": status,
            "usage": usage,
            "limits": get_subscription_limits(g.subscription_tier),
            "upgrade_recommendations": get_upgrade_recommendations(g.user_id, usage)
        })
        
    except Exception as e:
        logger.error(f"Subscription status error: {e}", exc_info=True)
        return jsonify({"error": "Failed to get subscription status"}), 500

@app.route("/subscription/upgrade", methods=["POST"])
def upgrade_subscription():
    """Handle subscription upgrades"""
    try:
        data = request.get_json() or {}
        new_tier = data.get('tier')
        
        if new_tier not in ['basic', 'pro', 'enterprise']:
            return jsonify({"error": "Invalid subscription tier"}), 400
        
        # Process upgrade through payment provider
        upgrade_result = process_subscription_upgrade(g.user_id, new_tier)
        
        if upgrade_result['success']:
            # Update user subscription
            update_user_subscription(g.user_id, new_tier)
            
            # Send welcome email with new features
            send_upgrade_welcome_email(g.user_id, new_tier)
            
            return jsonify({
                "status": "success",
                "new_tier": new_tier,
                "features_unlocked": get_tier_features(new_tier),
                "billing_info": upgrade_result['billing_info']
            })
        else:
            return jsonify({
                "error": "Upgrade failed",
                "message": upgrade_result['error']
            }), 400
            
    except Exception as e:
        logger.error(f"Subscription upgrade error: {e}", exc_info=True)
        return jsonify({"error": "Upgrade failed"}), 500

# ===============================
# ADMIN & ANALYTICS ENDPOINTS
# ===============================

@app.route("/admin/analytics", methods=["GET"])
@limiter.limit("100 per hour")
def admin_analytics():
    """Admin dashboard with system analytics"""
    # Check admin permissions
    if not is_admin_user(g.user_id):
        return jsonify({"error": "Admin access required"}), 403
    
    try:
        analytics_data = {
            "system_performance": {
                "requests_processed": performance_stats['requests_processed'],
                "avg_response_time": performance_stats['avg_response_time'],
                "uptime_hours": (datetime.now() - performance_stats['uptime_start']).total_seconds() / 3600,
                "error_rate": calculate_error_rate(),
                "api_health": check_api_health()
            },
            "user_metrics": {
                "total_users": get_total_users(),
                "active_users_24h": get_active_users(24),
                "subscription_breakdown": get_subscription_breakdown(),
                "churn_rate": calculate_churn_rate(),
                "user_satisfaction": get_user_satisfaction_score()
            },
            "business_metrics": {
                "monthly_revenue": get_monthly_revenue(),
                "revenue_by_tier": get_revenue_by_tier(),
                "conversion_rates": get_conversion_rates(),
                "ltv_by_tier": get_ltv_by_tier()
            },
            "ml_model_performance": ml_model.get_model_status(),
            "verification_accuracy": {
                "overall_accuracy": get_verification_accuracy(),
                "false_positive_rate": get_false_positive_rate(),
                "user_reported_accuracy": get_user_reported_accuracy()
            }
        }
        
        return jsonify(analytics_data)
        
    except Exception as e:
        logger.error(f"Admin analytics error: {e}", exc_info=True)
        return jsonify({"error": "Failed to generate analytics"}), 500

@app.route("/admin/model-retrain", methods=["POST"])
def admin_model_retrain():
    """Trigger manual model retraining"""
    if not is_admin_user(g.user_id):
        return jsonify({"error": "Admin access required"}), 403
    
    try:
        # Trigger asynchronous model retraining
        retrain_result = trigger_model_retraining()
        
        return jsonify({
            "status": "success",
            "message": "Model retraining initiated",
            "job_id": retrain_result['job_id'],
            "estimated_completion": retrain_result['estimated_completion']
        })
        
    except Exception as e:
        logger.error(f"Model retrain error: {e}", exc_info=True)
        return jsonify({"error": "Failed to initiate retraining"}), 500

# ===============================
# UTILITY FUNCTIONS
# ===============================

def validate_subscription_limits(tier: str, user_id: str) -> bool:
    """Check if user has remaining quota for their subscription tier"""
    limits = get_subscription_limits(tier)
    current_usage = get_current_usage(user_id)
    
    if tier == 'free':
        return current_usage.get('daily_verifications', 0) < limits['daily_verifications']
    elif tier == 'basic':
        return current_usage.get('monthly_verifications', 0) < limits['monthly_verifications']
    else:
        return True  # Pro and Enterprise have unlimited verifications

def get_subscription_limits(tier: str) -> Dict[str, Any]:
    """Get limits for subscription tier"""
    limits = {
        'free': {
            'daily_verifications': 10,
            'monthly_verifications': 100,
            'batch_size': 0,
            'advanced_analytics': False,
            'seller_tools': False,
            'priority_support': False
        },
        'basic': {
            'daily_verifications': 1000,
            'monthly_verifications': 10000,
            'batch_size': 10,
            'advanced_analytics': True,
            'seller_tools': False,
            'priority_support': False
        },
        'pro': {
            'daily_verifications': -1,  # Unlimited
            'monthly_verifications': -1,
            'batch_size': 50,
            'advanced_analytics': True,
            'seller_tools': True,
            'priority_support': True
        },
        'enterprise': {
            'daily_verifications': -1,
            'monthly_verifications': -1,
            'batch_size': 200,
            'advanced_analytics': True,
            'seller_tools': True,
            'priority_support': True,
            'api_access': True,
            'custom_integrations': True
        }
    }
    return limits.get(tier, limits['free'])

def extract_features_for_ml(listing_data: Dict, verification_result) -> Dict:
    """Extract ML features from listing data and verification results"""
    return {
        'price_vs_market_pct': listing_data.get('price', 0) / max(listing_data.get('market_value', 1), 1),
        'seller_feedback_pct': listing_data.get('seller_info', {}).get('feedback_pct', 95) / 100,
        'account_age_days_norm': min(listing_data.get('seller_info', {}).get('account_age_days', 365), 3650) / 3650,
        'uses_stock_images': 1.0 if detect_stock_images(listing_data.get('photos', [])) else 0.0,
        'off_platform_payment': 1.0 if detect_off_platform_payment(listing_data.get('description', '')) else 0.0,
        'price_anomaly_flag': 1.0 if verification_result.trust_score < 30 else 0.0,
        'feedback_drop_flag': 0.0,  # TODO: Implement seller feedback history analysis
        'desc_length_norm': min(len(listing_data.get('description', '')), 1000) / 1000,
        'num_identical_listings_norm': min(verification_result.similar_items_found, 100) / 100
    }

def track_usage(user_id: str, action_type: str, subscription_tier: str, quantity: int = 1):
    """Track user usage for billing and analytics"""
    usage_key = f"usage:{user_id}:{datetime.now().strftime('%Y-%m-%d')}"
    
    # Update daily usage in Redis
    redis_client.hincrby(usage_key, action_type, quantity)
    redis_client.expire(usage_key, 86400 * 31)  # Keep for 31 days
    
    # Log for analytics
    logger.info(f"Usage tracked: {user_id} | {action_type} | {quantity} | {subscription_tier}")

def get_advanced_analytics(listing_data: Dict, subscription_tier: str) -> Optional[Dict]:
    """Return advanced analytics for paid tiers"""
    if subscription_tier == 'free':
        return None
    
    return {
        'price_history': get_price_history(listing_data.get('title')),
        'seasonal_trends': get_seasonal_trends(listing_data.get('category')),
        'competitor_analysis': get_competitor_analysis(listing_data),
        'optimization_score': calculate_optimization_score(listing_data),
        'market_position': calculate_market_position(listing_data)
    }

async def analyze_product_from_photo(photo_base64: str) -> Dict:
    """Analyze product from photo using AI"""
    # This would integrate with computer vision APIs
    # For now, return mock analysis
    return {
        'category': 'Electronics',
        'brand': 'Apple',
        'model': 'iPhone 13',
        'condition': 'Used - Good',
        'key_features': ['128GB', 'Unlocked', 'Blue'],
        'color': 'Blue',
        'confidence': 0.85
    }

async def generate_optimized_listing(product_analysis: Dict, user_input: Dict, market_research: bool = True) -> Dict:
    """Generate SEO-optimized listing content"""
    # This would use GPT/Claude API for listing generation
    return {
        'title': f"{product_analysis['brand']} {product_analysis['model']} {' '.join(product_analysis['key_features'])}",
        'description': f"Excellent condition {product_analysis['brand']} {product_analysis['model']}...",
        'keywords': ['smartphone', 'unlocked', 'apple', 'iphone'],
        'category_suggestions': ['9355', '15032'],
        'bullet_points': [
            f"Brand: {product_analysis['brand']}",
            f"Model: {product_analysis['model']}",
            f"Condition: {product_analysis['condition']}"
        ]
    }

# ===============================
# HEALTH CHECK & STATUS
# ===============================

@app.route("/health", methods=["GET"])
def health_check():
    """System health check"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.1.1-strategic",
            "uptime_seconds": (datetime.now() - performance_stats['uptime_start']).total_seconds(),
            "performance": {
                "avg_response_time_ms": performance_stats['avg_response_time'],
                "requests_processed": performance_stats['requests_processed'],
                "error_rate_percent": calculate_error_rate()
            },
            "services": {
                "redis": check_redis_health(),
                "ml_model": ml_model is not None,
                "ebay_api": check_ebay_api_health(),
                "verification_engine": True
            },
            "model_status": ml_model.get_model_status() if ml_model else None
        }
        
        # Determine overall health
        if all(health_status["services"].values()) and health_status["performance"]["error_rate_percent"] < 5:
            status_code = 200
        else:
            health_status["status"] = "degraded"
            status_code = 503
        
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 503

@app.route("/metrics", methods=["GET"])
def get_metrics():
    """Prometheus-style metrics for monitoring"""
    try:
        metrics = []
        
        # Add custom metrics
        metrics.append(f'ebay_requests_total {performance_stats["requests_processed"]}')
        metrics.append(f'ebay_response_time_avg {performance_stats["avg_response_time"]}')
        metrics.append(f'ebay_accuracy_score {performance_stats["accuracy_score"]}')
        
        if ml_model:
            model_status = ml_model.get_model_status()
            metrics.append(f'ebay_model_version {model_status["version"]}')
            metrics.append(f'ebay_model_updates {model_status["update_count"]}')
        
        return '\n'.join(metrics), 200, {'Content-Type': 'text/plain'}
        
    except Exception as e:
        logger.error(f"Metrics error: {e}", exc_info=True)
        return "# Error generating metrics\n", 500, {'Content-Type': 'text/plain'}

# ===============================
# MOCK HELPER FUNCTIONS
# ===============================

def get_user_preferences(user_id: str) -> Dict:
    """Get user preferences for personalized recommendations"""
    return {
        'risk_tolerance': 'medium',
        'profit_threshold': 20,
        'categories_of_interest': ['electronics', 'collectibles'],
        'max_investment': 500
    }

def get_seller_tier(seller_info: Dict) -> str:
    """Determine seller quality tier"""
    feedback_pct = seller_info.get('feedback_pct', 95)
    account_age = seller_info.get('account_age_days', 365)
    
    if feedback_pct >= 99 and account_age >= 1000:
        return 'Trusted'
    elif feedback_pct >= 95 and account_age >= 365:
        return 'Good'
    else:
        return 'New'

def assess_listing_quality(listing_data: Dict) -> str:
    """Assess overall listing quality"""
    score = 0
    
    # Check description length
    if len(listing_data.get('description', '')) > 100:
        score += 1
    
    # Check photos
    if len(listing_data.get('photos', [])) >= 3:
        score += 1
    
    # Check return policy
    if listing_data.get('return_policy'):
        score += 1
    
    if score >= 3:
        return 'High'
    elif score >= 2:
        return 'Medium'
    else:
        return 'Low'

def check_redis_health() -> bool:
    """Check Redis connection"""
    try:
        redis_client.ping()
        return True
    except:
        return False

def check_ebay_api_health() -> bool:
    """Check eBay API availability"""
    # Simple health check - could be more sophisticated
    return EBAY_APP_ID != "DUMMY_KEY"

def calculate_error_rate() -> float:
    """Calculate current error rate"""
    # This would track actual errors over time
    return 1.2  # Mock 1.2% error rate

# Additional mock functions would go here...
def detect_stock_images(photos: List) -> bool: return False
def detect_off_platform_payment(description: str) -> bool: return False
def get_remaining_verifications(user_id: str, tier: str) -> int: return 50
def log_verification_success(listing: Dict, response: Dict, user_id: str): pass
def get_current_usage(user_id: str) -> Dict: return {'daily_verifications': 5}
def is_admin_user(user_id: str) -> bool: return user_id == 'admin'
def store_feedback(data: Dict): pass
def update_user_reputation(user_id: str, feedback: Dict): pass
def calculate_feedback_reward(feedback: Dict) -> int: return 10
def add_user_rewards(user_id: str, points: int): pass

if __name__ == "__main__":
    # Ensure directories exist
    create_directories()
    
    # Start the production server
    logger.info("🚀 Starting Strategic eBay Intelligence Platform")
    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
        threaded=True
    )
