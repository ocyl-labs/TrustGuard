# payment_system.py
"""
Complete payment processing and subscription management with Stripe
Handles: Subscriptions, one-time payments, webhooks, billing management
"""

import os
import stripe
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from flask import Flask, request, jsonify, g
from functools import wraps
import json

from database_setup import DatabaseManager

logger = logging.getLogger(__name__)

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")

@dataclass
class SubscriptionTier:
    """Subscription tier configuration"""
    id: str
    name: str
    price_monthly: float
    price_yearly: float
    stripe_price_id_monthly: str
    stripe_price_id_yearly: str
    features: List[str]
    limits: Dict[str, Any]

# Subscription tiers configuration
SUBSCRIPTION_TIERS = {
    'free': SubscriptionTier(
        id='free',
        name='Free',
        price_monthly=0.0,
        price_yearly=0.0,
        stripe_price_id_monthly='',
        stripe_price_id_yearly='',
        features=[
            '10 verifications per day',
            'Basic trust scoring',
            'Community support'
        ],
        limits={
            'daily_verifications': 10,
            'monthly_verifications': 300,
            'batch_size': 0,
            'advanced_analytics': False,
            'seller_tools': False,
            'arbitrage_alerts': False
        }
    ),
    'basic': SubscriptionTier(
        id='basic',
        name='Basic',
        price_monthly=9.99,
        price_yearly=99.99,
        stripe_price_id_monthly=os.getenv("STRIPE_BASIC_MONTHLY_PRICE_ID"),
        stripe_price_id_yearly=os.getenv("STRIPE_BASIC_YEARLY_PRICE_ID"),
        features=[
            'Unlimited verifications',
            'Advanced trust scoring',
            'Market insights',
            'Email support'
        ],
        limits={
            'daily_verifications': -1,  # Unlimited
            'monthly_verifications': -1,
            'batch_size': 10,
            'advanced_analytics': True,
            'seller_tools': False,
            'arbitrage_alerts': True
        }
    ),
    'pro': SubscriptionTier(
        id='pro',
        name='Pro',
        price_monthly=19.99,
        price_yearly=199.99,
        stripe_price_id_monthly=os.getenv("STRIPE_PRO_MONTHLY_PRICE_ID"),
        stripe_price_id_yearly=os.getenv("STRIPE_PRO_YEARLY_PRICE_ID"),
        features=[
            'Everything in Basic',
            'Seller tools & AI listing generation',
            'Photo enhancement',
            'Arbitrage scanning',
            'Priority support'
        ],
        limits={
            'daily_verifications': -1,
            'monthly_verifications': -1,
            'batch_size': 50,
            'advanced_analytics': True,
            'seller_tools': True,
            'arbitrage_alerts': True,
            'photo_enhancement': True,
            'listing_generation': True
        }
    ),
    'enterprise': SubscriptionTier(
        id='enterprise',
        name='Enterprise',
        price_monthly=199.99,
        price_yearly=1999.99,
        stripe_price_id_monthly=os.getenv("STRIPE_ENTERPRISE_MONTHLY_PRICE_ID"),
        stripe_price_id_yearly=os.getenv("STRIPE_ENTERPRISE_YEARLY_PRICE_ID"),
        features=[
            'Everything in Pro',
            'API access',
            'Custom integrations',
            'White-label options',
            'Dedicated support',
            'Advanced analytics dashboard'
        ],
        limits={
            'daily_verifications': -1,
            'monthly_verifications': -1,
            'batch_size': 200,
            'advanced_analytics': True,
            'seller_tools': True,
            'arbitrage_alerts': True,
            'api_access': True,
            'custom_integrations': True,
            'white_label': True
        }
    )
}

class PaymentError(Exception):
    """Payment processing error"""
    pass

class SubscriptionManager:
    """Handles all subscription and payment operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        
        # Validate Stripe configuration
        if not stripe.api_key:
            logger.warning("Stripe API key not configured - payments disabled")
    
    # Customer Management
    async def create_stripe_customer(self, user_data: Dict) -> str:
        """Create Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=user_data['email'],
                name=f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip(),
                metadata={
                    'user_id': user_data['id'],
                    'journey_type': user_data.get('journey_type', 'buyer')
                }
            )
            
            # Update user with Stripe customer ID
            await self.db.update_user(user_data['id'], stripe_customer_id=customer.id)
            
            logger.info(f"Created Stripe customer {customer.id} for user {user_data['id']}")
            return customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise PaymentError(f"Failed to create customer: {e}")
    
    async def get_or_create_customer(self, user_id: str) -> str:
        """Get existing or create new Stripe customer"""
        user = await self.db.get_user_by_id(user_id)
        if not user:
            raise PaymentError("User not found")
        
        if user.get('stripe_customer_id'):
            return user['stripe_customer_id']
        
        return await self.create_stripe_customer(user)
    
    # Subscription Management
    async def create_subscription(self, user_id: str, tier: str, 
                                billing_cycle: str = 'monthly') -> Dict:
        """Create new subscription"""
        if tier not in SUBSCRIPTION_TIERS:
            raise PaymentError(f"Invalid subscription tier: {tier}")
        
        if tier == 'free':
            # Handle free tier
            await self.db.update_user(
                user_id,
                subscription_tier='free',
                subscription_status='active',
                subscription_expires_at=None
            )
            return {'tier': 'free', 'status': 'active'}
        
        tier_config = SUBSCRIPTION_TIERS[tier]
        
        # Get Stripe price ID based on billing cycle
        if billing_cycle == 'yearly':
            price_id = tier_config.stripe_price_id_yearly
        else:
            price_id = tier_config.stripe_price_id_monthly
            
        if not price_id:
            raise PaymentError("Stripe price ID not configured for this tier")
        
        try:
            customer_id = await self.get_or_create_customer(user_id)
            
            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                payment_behavior='default_incomplete',
                payment_settings={'save_default_payment_method': 'on_subscription'},
                expand=['latest_invoice.payment_intent'],
                metadata={
                    'user_id': user_id,
                    'tier': tier,
                    'billing_cycle': billing_cycle
                }
            )
            
            # Update user subscription in database
            expires_at = datetime.utcnow() + timedelta(days=30 if billing_cycle == 'monthly' else 365)
            await self.db.update_user(
                user_id,
                subscription_tier=tier,
                subscription_status=subscription.status,
                subscription_expires_at=expires_at
            )
            
            logger.info(f"Created subscription {subscription.id} for user {user_id}")
            
            return {
                'subscription_id': subscription.id,
                'client_secret': subscription.latest_invoice.payment_intent.client_secret,
                'status': subscription.status,
                'tier': tier,
                'billing_cycle': billing_cycle
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription: {e}")
            raise PaymentError(f"Failed to create subscription: {e}")
    
    async def cancel_subscription(self, user_id: str, immediate: bool = False) -> Dict:
        """Cancel user subscription"""
        user = await self.db.get_user_by_id(user_id)
        if not user or not user.get('stripe_customer_id'):
            raise PaymentError("No active subscription found")
        
        try:
            # Find active subscription
            subscriptions = stripe.Subscription.list(
                customer=user['stripe_customer_id'],
                status='active'
            )
            
            if not subscriptions.data:
                raise PaymentError("No active subscription found")
            
            subscription = subscriptions.data[0]
            
            if immediate:
                # Cancel immediately
                canceled_subscription = stripe.Subscription.delete(subscription.id)
                status = 'canceled'
                expires_at = datetime.utcnow()
            else:
                # Cancel at period end
                canceled_subscription = stripe.Subscription.modify(
                    subscription.id,
                    cancel_at_period_end=True
                )
                status = 'cancel_at_period_end'
                expires_at = datetime.utcfromtimestamp(subscription.current_period_end)
            
            # Update database
            await self.db.update_user(
                user_id,
                subscription_status=status,
                subscription_expires_at=expires_at
            )
            
            logger.info(f"Canceled subscription {subscription.id} for user {user_id}")
            
            return {
                'subscription_id': subscription.id,
                'status': status,
                'expires_at': expires_at.isoformat()
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {e}")
            raise PaymentError(f"Failed to cancel subscription: {e}")
    
    async def update_subscription(self, user_id: str, new_tier: str) -> Dict:
        """Update subscription tier"""
        if new_tier not in SUBSCRIPTION_TIERS:
            raise PaymentError(f"Invalid subscription tier: {new_tier}")
        
        user = await self.db.get_user_by_id(user_id)
        if not user or not user.get('stripe_customer_id'):
            raise PaymentError("No customer found")
        
        try:
            # Find active subscription
            subscriptions = stripe.Subscription.list(
                customer=user['stripe_customer_id'],
                status='active'
            )
            
            if not subscriptions.data:
                # No active subscription, create new one
                return await self.create_subscription(user_id, new_tier)
            
            subscription = subscriptions.data[0]
            tier_config = SUBSCRIPTION_TIERS[new_tier]
            
            # Update subscription item with new price
            stripe.Subscription.modify(
                subscription.id,
                items=[{
                    'id': subscription['items']['data'][0].id,
                    'price': tier_config.stripe_price_id_monthly,
                }],
                proration_behavior='always_invoice'
            )
            
            # Update database
            await self.db.update_user(
                user_id,
                subscription_tier=new_tier,
                subscription_status='active'
            )
            
            logger.info(f"Updated subscription for user {user_id} to {new_tier}")
            
            return {
                'subscription_id': subscription.id,
                'tier': new_tier,
                'status': 'active'
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update subscription: {e}")
            raise PaymentError(f"Failed to update subscription: {e}")
    
    # Payment Methods
    async def add_payment_method(self, user_id: str, payment_method_id: str) -> Dict:
        """Add payment method to customer"""
        try:
            customer_id = await self.get_or_create_customer(user_id)
            
            # Attach payment method to customer
            stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
            
            # Set as default payment method
            stripe.Customer.modify(
                customer_id,
                invoice_settings={'default_payment_method': payment_method_id}
            )
            
            logger.info(f"Added payment method for user {user_id}")
            
            return {'status': 'success', 'payment_method_id': payment_method_id}
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to add payment method: {e}")
            raise PaymentError(f"Failed to add payment method: {e}")
    
    # One-time Payments
    async def create_payment_intent(self, user_id: str, amount: float, 
                                  description: str, metadata: Dict = None) -> Dict:
        """Create payment intent for one-time payment"""
        try:
            customer_id = await self.get_or_create_customer(user_id)
            
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency='usd',
                customer=customer_id,
                description=description,
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True}
            )
            
            return {
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment intent: {e}")
            raise PaymentError(f"Failed to create payment intent: {e}")
    
    # Billing and Invoices
    async def get_billing_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get billing history for user"""
        user = await self.db.get_user_by_id(user_id)
        if not user or not user.get('stripe_customer_id'):
            return []
        
        try:
            invoices = stripe.Invoice.list(
                customer=user['stripe_customer_id'],
                limit=limit
            )
            
            billing_history = []
            for invoice in invoices.data:
                billing_history.append({
                    'id': invoice.id,
                    'amount': invoice.amount_paid / 100,
                    'currency': invoice.currency.upper(),
                    'status': invoice.status,
                    'created': datetime.utcfromtimestamp(invoice.created).isoformat(),
                    'description': invoice.description or 'Subscription payment',
                    'invoice_url': invoice.hosted_invoice_url
                })
            
            return billing_history
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get billing history: {e}")
            return []
    
    # Usage-based Billing
    async def record_usage(self, user_id: str, feature: str, quantity: int = 1):
        """Record usage for potential usage-based billing"""
        # For now, just track in database
        await self.db.track_usage(
            user_id=user_id,
            action_type=feature,
            subscription_tier='usage_based',
            quantity=quantity
        )
    
    # Webhook Processing
    async def handle_webhook_event(self, event_type: str, event_data: Dict) -> Dict:
        """Handle Stripe webhook events"""
        try:
            if event_type == 'customer.subscription.updated':
                return await self._handle_subscription_updated(event_data)
            elif event_type == 'customer.subscription.deleted':
                return await self._handle_subscription_deleted(event_data)
            elif event_type == 'invoice.payment_succeeded':
                return await self._handle_payment_succeeded(event_data)
            elif event_type == 'invoice.payment_failed':
                return await self._handle_payment_failed(event_data)
            else:
                logger.info(f"Unhandled webhook event: {event_type}")
                return {'status': 'ignored'}
                
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def _handle_subscription_updated(self, event_data: Dict) -> Dict:
        """Handle subscription update webhook"""
        subscription = event_data['object']
        user_id = subscription['metadata'].get('user_id')
        
        if not user_id:
            logger.warning("No user_id in subscription metadata")
            return {'status': 'ignored'}
        
        # Update subscription status in database
        expires_at = datetime.utcfromtimestamp(subscription['current_period_end'])
        
        await self.db.update_user(
            user_id,
            subscription_status=subscription['status'],
            subscription_expires_at=expires_at
        )
        
        logger.info(f"Updated subscription status for user {user_id}: {subscription['status']}")
        return {'status': 'processed'}
    
    async def _handle_subscription_deleted(self, event_data: Dict) -> Dict:
        """Handle subscription deletion webhook"""
        subscription = event_data['object']
        user_id = subscription['metadata'].get('user_id')
        
        if not user_id:
            return {'status': 'ignored'}
        
        # Downgrade to free tier
        await self.db.update_user(
            user_id,
            subscription_tier='free',
            subscription_status='canceled',
            subscription_expires_at=datetime.utcnow()
        )
        
        logger.info(f"Subscription canceled for user {user_id}")
        return {'status': 'processed'}
    
    async def _handle_payment_succeeded(self, event_data: Dict) -> Dict:
        """Handle successful payment webhook"""
        invoice = event_data['object']
        subscription_id = invoice.get('subscription')
        
        if subscription_id:
            # Update subscription status to active
            subscription = stripe.Subscription.retrieve(subscription_id)
            user_id = subscription['metadata'].get('user_id')
            
            if user_id:
                await self.db.update_user(
                    user_id,
                    subscription_status='active'
                )
                logger.info(f"Payment succeeded for user {user_id}")
        
        return {'status': 'processed'}
    
    async def _handle_payment_failed(self, event_data: Dict) -> Dict:
        """Handle failed payment webhook"""
        invoice = event_data['object']
        subscription_id = invoice.get('subscription')
        
        if subscription_id:
            subscription = stripe.Subscription.retrieve(subscription_id)
            user_id = subscription['metadata'].get('user_id')
            
            if user_id:
                await self.db.update_user(
                    user_id,
                    subscription_status='past_due'
                )
                
                # TODO: Send payment failed notification email
                logger.warning(f"Payment failed for user {user_id}")
        
        return {'status': 'processed'}

# Flask Payment Routes
def create_payment_routes(app: Flask, subscription_manager: SubscriptionManager, 
                         require_auth, require_subscription):
    """Create Flask payment and subscription routes"""
    
    @app.route('/api/subscription/tiers', methods=['GET'])
    def get_subscription_tiers():
        """Get available subscription tiers"""
        tiers = {}
        for tier_id, tier in SUBSCRIPTION_TIERS.items():
            tiers[tier_id] = {
                'id': tier.id,
                'name': tier.name,
                'price_monthly': tier.price_monthly,
                'price_yearly': tier.price_yearly,
                'features': tier.features,
                'limits': tier.limits
            }
        
        return jsonify({
            'success': True,
            'tiers': tiers,
            'stripe_publishable_key': STRIPE_PUBLISHABLE_KEY
        })
    
    @app.route('/api/subscription/create', methods=['POST'])
    @require_auth
    async def create_subscription():
        """Create new subscription"""
        try:
            data = request.get_json() or {}
            tier = data.get('tier')
            billing_cycle = data.get('billing_cycle', 'monthly')
            
            if not tier or tier not in SUBSCRIPTION_TIERS:
                return jsonify({'error': 'Invalid subscription tier'}), 400
            
            result = await subscription_manager.create_subscription(
                g.user_id, tier, billing_cycle
            )
            
            return jsonify({
                'success': True,
                'subscription': result
            })
            
        except PaymentError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Subscription creation error: {e}")
            return jsonify({'error': 'Failed to create subscription'}), 500
    
    @app.route('/api/subscription/cancel', methods=['POST'])
    @require_auth
    async def cancel_subscription():
        """Cancel subscription"""
        try:
            data = request.get_json() or {}
            immediate = data.get('immediate', False)
            
            result = await subscription_manager.cancel_subscription(g.user_id, immediate)
            
            return jsonify({
                'success': True,
                'cancellation': result
            })
            
        except PaymentError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Subscription cancellation error: {e}")
            return jsonify({'error': 'Failed to cancel subscription'}), 500
    
    @app.route('/api/subscription/update', methods=['POST'])
    @require_auth
    async def update_subscription():
        """Update subscription tier"""
        try:
            data = request.get_json() or {}
            new_tier = data.get('tier')
            
            if not new_tier or new_tier not in SUBSCRIPTION_TIERS:
                return jsonify({'error': 'Invalid subscription tier'}), 400
            
            result = await subscription_manager.update_subscription(g.user_id, new_tier)
            
            return jsonify({
                'success': True,
                'subscription': result
            })
            
        except PaymentError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Subscription update error: {e}")
            return jsonify({'error': 'Failed to update subscription'}), 500
    
    @app.route('/api/payment/add-method', methods=['POST'])
    @require_auth
    async def add_payment_method():
        """Add payment method"""
        try:
            data = request.get_json() or {}
            payment_method_id = data.get('payment_method_id')
            
            if not payment_method_id:
                return jsonify({'error': 'Payment method ID required'}), 400
            
            result = await subscription_manager.add_payment_method(g.user_id, payment_method_id)
            
            return jsonify({
                'success': True,
                'payment_method': result
            })
            
        except PaymentError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Add payment method error: {e}")
            return jsonify({'error': 'Failed to add payment method'}), 500
    
    @app.route('/api/payment/create-intent', methods=['POST'])
    @require_auth
    async def create_payment_intent():
        """Create payment intent for one-time payment"""
        try:
            data = request.get_json() or {}
            amount = data.get('amount')
            description = data.get('description', 'One-time payment')
            metadata = data.get('metadata', {})
            
            if not amount or amount <= 0:
                return jsonify({'error': 'Valid amount required'}), 400
            
            result = await subscription_manager.create_payment_intent(
                g.user_id, amount, description, metadata
            )
            
            return jsonify({
                'success': True,
                'payment_intent': result
            })
            
        except PaymentError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Payment intent creation error: {e}")
            return jsonify({'error': 'Failed to create payment intent'}), 500
    
    @app.route('/api/billing/history', methods=['GET'])
    @require_auth
    async def get_billing_history():
        """Get billing history"""
        try:
            limit = min(int(request.args.get('limit', 20)), 100)
            
            history = await subscription_manager.get_billing_history(g.user_id, limit)
            
            return jsonify({
                'success': True,
                'billing_history': history
            })
            
        except Exception as e:
            logger.error(f"Billing history error: {e}")
            return jsonify({'error': 'Failed to get billing history'}), 500
    
    @app.route('/api/subscription/status', methods=['GET'])
    @require_auth
    async def get_subscription_status():
        """Get current subscription status"""
        try:
            user = await subscription_manager.db.get_user_by_id(g.user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            current_tier = SUBSCRIPTION_TIERS.get(user['subscription_tier'], SUBSCRIPTION_TIERS['free'])
            
            status = {
                'tier': user['subscription_tier'],
                'status': user['subscription_status'],
                'expires_at': user['subscription_expires_at'].isoformat() if user['subscription_expires_at'] else None,
                'features': current_tier.features,
                'limits': current_tier.limits
            }
            
            return jsonify({
                'success': True,
                'subscription': status
            })
            
        except Exception as e:
            logger.error(f"Subscription status error: {e}")
            return jsonify({'error': 'Failed to get subscription status'}), 500
    
    @app.route('/webhooks/stripe', methods=['POST'])
    def handle_stripe_webhook():
        """Handle Stripe webhooks"""
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        
        if not STRIPE_WEBHOOK_SECRET:
            logger.warning("Stripe webhook secret not configured")
            return jsonify({'error': 'Webhook secret not configured'}), 500
        
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        except ValueError:
            logger.error("Invalid payload in webhook")
            return jsonify({'error': 'Invalid payload'}), 400
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid signature in webhook")
            return jsonify({'error': 'Invalid signature'}), 400
        
        # Process webhook asynchronously
        async def process_webhook():
            try:
                result = await subscription_manager.handle_webhook_event(
                    event['type'], 
                    event['data']
                )
                logger.info(f"Webhook processed: {event['type']} - {result['status']}")
            except Exception as e:
                logger.error(f"Webhook processing failed: {e}")
        
        # Schedule async processing
        asyncio.create_task(process_webhook())
        
        return jsonify({'status': 'received'}), 200

# Subscription validation helpers
def validate_subscription_limits(user_id: str, action: str, quantity: int = 1):
    """Validate if user can perform action based on subscription limits"""
    async def _validate():
        user = await subscription_manager.db.get_user_by_id(user_id)
        if not user:
            return False
        
        tier = SUBSCRIPTION_TIERS.get(user['subscription_tier'], SUBSCRIPTION_TIERS['free'])
        limits = tier.limits
        
        # Check specific limits based on action
        if action == 'verification':
            daily_limit = limits.get('daily_verifications', 0)
            if daily_limit > 0:  # -1 means unlimited
                # Check current usage
                usage_stats = await subscription_manager.db.get_usage_stats(user_id, days=1)
                current_usage = usage_stats.get('usage_by_type', {}).get('verification', {}).get('count', 0)
                return current_usage + quantity <= daily_limit
        
        elif action == 'batch_verification':
            max_batch = limits.get('batch_size', 0)
            return quantity <= max_batch
        
        elif action == 'seller_tools':
            return limits.get('seller_tools', False)
        
        elif action == 'advanced_analytics':
            return limits.get('advanced_analytics', False)
        
        return True  # Default allow
    
    return asyncio.create_task(_validate())

# Usage example and setup
async def setup_payment_system(app: Flask, db_manager: DatabaseManager, 
                              require_auth, require_subscription):
    """Setup complete payment system"""
    
    # Initialize subscription manager
    subscription_manager = SubscriptionManager(db_manager)
    
    # Create payment routes
    create_payment_routes(app, subscription_manager, require_auth, require_subscription)
    
    logger.info("✅ Payment system setup complete")
    
    return subscription_manager

if __name__ == "__main__":
    # Test payment system
    import asyncio
    from database_setup import DatabaseManager
    
    async def test_payments():
        if not stripe.api_key:
            print("❌ Stripe API key not configured")
            return
        
        db = DatabaseManager()
        await db.initialize()
        
        subscription_manager = SubscriptionManager(db)
        
        print("Testing payment system...")
        
        try:
            # Test creating a test customer (requires test user in DB)
            test_user = {
                'id': 'test_user_id',
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
            
            customer_id = await subscription_manager.create_stripe_customer(test_user)
            print(f"✅ Created test customer: {customer_id}")
            
        except Exception as e:
            print(f"❌ Payment test failed: {e}")
        
        await db.close()
    
    asyncio.run(test_payments())
