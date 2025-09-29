# database_setup.py
"""
Complete database setup with PostgreSQL for persistent data
and Redis for caching and real-time features
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
import hashlib

# Database imports
import asyncpg
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/trustguard")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# SQLAlchemy setup
Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=False, pool_size=20, max_overflow=30)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Database Models
class User(Base):
    """User account information"""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile information
    first_name = Column(String(100))
    last_name = Column(String(100))
    avatar_url = Column(String(500))
    
    # Subscription information
    subscription_tier = Column(String(20), default='free', nullable=False)
    subscription_status = Column(String(20), default='active', nullable=False)
    subscription_expires_at = Column(DateTime(timezone=True))
    stripe_customer_id = Column(String(100), unique=True, index=True)
    
    # User preferences
    preferences = Column(JSONB, default=dict)
    
    # Journey tracking
    journey_type = Column(String(20), default='buyer')  # buyer, seller, flipper
    total_profit = Column(Float, default=0.0)
    total_savings = Column(Float, default=0.0)
    success_streak = Column(Integer, default=0)
    risk_alerts_avoided = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))
    
    # Constraints
    __table_args__ = (
        CheckConstraint('subscription_tier IN (\'free\', \'basic\', \'pro\', \'enterprise\')', name='valid_subscription_tier'),
        CheckConstraint('journey_type IN (\'buyer\', \'seller\', \'flipper\')', name='valid_journey_type'),
        Index('idx_users_subscription', 'subscription_tier', 'subscription_status'),
        Index('idx_users_created', 'created_at'),
    )

class ItemVerification(Base):
    """Record of item verifications performed"""
    __tablename__ = 'item_verifications'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    
    # Item information
    ebay_item_id = Column(String(50), index=True)
    title = Column(String(500), nullable=False)
    price = Column(Float, nullable=False)
    seller_username = Column(String(100))
    category = Column(String(100))
    
    # Analysis results
    trust_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    confidence_score = Column(Float, nullable=False)
    market_value = Column(Float)
    profit_potential = Column(Float)
    
    # AI predictions
    features = Column(JSONB, nullable=False)  # ML features used
    model_version = Column(String(20), nullable=False)
    processing_time_ms = Column(Integer)
    
    # User actions
    user_decision = Column(String(20))  # buy, skip, watch
    user_feedback = Column(JSONB)  # feedback provided by user
    actual_outcome = Column(String(20))  # profit, loss, broke_even
    actual_profit = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    decision_at = Column(DateTime(timezone=True))
    outcome_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        CheckConstraint('trust_score >= 0 AND trust_score <= 100', name='valid_trust_score'),
        CheckConstraint('risk_level IN (\'LOW\', \'MEDIUM\', \'HIGH\', \'CRITICAL\')', name='valid_risk_level'),
        Index('idx_verifications_user_created', 'user_id', 'created_at'),
        Index('idx_verifications_trust_score', 'trust_score'),
        Index('idx_verifications_ebay_item', 'ebay_item_id'),
    )

class UserSession(Base):
    """User session tracking"""
    __tablename__ = 'user_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Session information
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(500))
    device_type = Column(String(20))  # web, mobile, extension
    
    # Session state
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_sessions_user_active', 'user_id', 'is_active'),
        Index('idx_sessions_expires', 'expires_at'),
    )

class UserAchievement(Base):
    """User achievements and milestones"""
    __tablename__ = 'user_achievements'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    
    achievement_key = Column(String(50), nullable=False)
    achievement_name = Column(String(100), nullable=False)
    achievement_description = Column(String(500))
    reward = Column(String(200))
    
    # Achievement metadata
    progress_value = Column(Float)  # Current progress
    target_value = Column(Float)    # Target to achieve
    is_completed = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        UniqueConstraint('user_id', 'achievement_key', name='unique_user_achievement'),
        Index('idx_achievements_user_completed', 'user_id', 'is_completed'),
    )

class ArbitrageOpportunity(Base):
    """Arbitrage opportunities found"""
    __tablename__ = 'arbitrage_opportunities'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    
    # Opportunity details
    item_title = Column(String(500), nullable=False)
    source_platform = Column(String(50), nullable=False)
    target_platform = Column(String(50), nullable=False)
    
    # Pricing information
    buy_price = Column(Float, nullable=False)
    sell_price = Column(Float, nullable=False)
    profit_margin = Column(Float, nullable=False)
    estimated_fees = Column(Float, nullable=False)
    net_profit = Column(Float, nullable=False)
    
    # Confidence and risk
    confidence_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    time_to_profit_days = Column(Integer)
    
    # Status tracking
    status = Column(String(20), default='active')  # active, taken, expired
    is_notified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    taken_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('idx_arbitrage_user_status', 'user_id', 'status'),
        Index('idx_arbitrage_profit', 'net_profit'),
        Index('idx_arbitrage_expires', 'expires_at'),
    )

class UsageMetrics(Base):
    """Track usage for billing and analytics"""
    __tablename__ = 'usage_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    
    # Usage information
    action_type = Column(String(50), nullable=False)  # verification, listing_generation, etc.
    quantity = Column(Integer, default=1)
    subscription_tier = Column(String(20), nullable=False)
    
    # Metadata
    request_id = Column(String(100))
    processing_time_ms = Column(Integer)
    success = Column(Boolean, default=True)
    error_message = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_usage_user_date', 'user_id', 'date'),
        Index('idx_usage_action_date', 'action_type', 'date'),
        Index('idx_usage_tier_date', 'subscription_tier', 'date'),
    )

class SecurityEvent(Base):
    """Security events and alerts"""
    __tablename__ = 'security_events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    
    # Event information
    event_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Event details
    details = Column(JSONB, nullable=False)
    resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('idx_security_severity_date', 'severity', 'created_at'),
        Index('idx_security_user_type', 'user_id', 'event_type'),
        Index('idx_security_resolved', 'resolved'),
    )

# Database Manager Class
class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self):
        self.redis_client = None
        
    async def initialize(self):
        """Initialize database connections"""
        # Initialize Redis
        self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        
        # Test connections
        try:
            await self.redis_client.ping()
            logger.info("✅ Redis connection successful")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database initialized successfully")
    
    async def close(self):
        """Close database connections"""
        if self.redis_client:
            await self.redis_client.close()
        await engine.dispose()
    
    # User Management
    async def create_user(self, email: str, password_hash: str, **kwargs) -> Dict:
        """Create a new user"""
        async with AsyncSessionLocal() as session:
            user = User(
                email=email.lower(),
                password_hash=password_hash,
                **kwargs
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            # Initialize user in Redis
            await self._initialize_user_cache(str(user.id))
            
            logger.info(f"Created user: {email}")
            return self._user_to_dict(user)
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                session.query(User).filter(User.email == email.lower())
            )
            user = result.scalar_one_or_none()
            return self._user_to_dict(user) if user else None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID with caching"""
        # Try Redis cache first
        cache_key = f"user:{user_id}"
        cached_user = await self.redis_client.get(cache_key)
        if cached_user:
            return json.loads(cached_user)
        
        # Get from database
        async with AsyncSessionLocal() as session:
            user = await session.get(User, user_id)
            if user:
                user_dict = self._user_to_dict(user)
                # Cache for 1 hour
                await self.redis_client.setex(cache_key, 3600, json.dumps(user_dict, default=str))
                return user_dict
        
        return None
    
    async def update_user(self, user_id: str, **updates) -> Optional[Dict]:
        """Update user information"""
        async with AsyncSessionLocal() as session:
            user = await session.get(User, user_id)
            if not user:
                return None
            
            for key, value in updates.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            user.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(user)
            
            # Update cache
            cache_key = f"user:{user_id}"
            user_dict = self._user_to_dict(user)
            await self.redis_client.setex(cache_key, 3600, json.dumps(user_dict, default=str))
            
            return user_dict
    
    # Item Verification Management
    async def save_verification(self, verification_data: Dict) -> str:
        """Save item verification results"""
        async with AsyncSessionLocal() as session:
            verification = ItemVerification(**verification_data)
            session.add(verification)
            await session.commit()
            await session.refresh(verification)
            
            logger.info(f"Saved verification: {verification.id}")
            return str(verification.id)
    
    async def get_user_verifications(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user's recent verifications"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                session.query(ItemVerification)
                .filter(ItemVerification.user_id == user_id)
                .order_by(ItemVerification.created_at.desc())
                .limit(limit)
            )
            verifications = result.scalars().all()
            return [self._verification_to_dict(v) for v in verifications]
    
    # Usage Tracking
    async def track_usage(self, user_id: str, action_type: str, 
                         subscription_tier: str, **metadata) -> None:
        """Track user action for billing"""
        usage_data = {
            'user_id': user_id,
            'action_type': action_type,
            'subscription_tier': subscription_tier,
            'quantity': metadata.get('quantity', 1),
            'processing_time_ms': metadata.get('processing_time_ms'),
            'success': metadata.get('success', True),
            'error_message': metadata.get('error_message'),
            'request_id': metadata.get('request_id')
        }
        
        # Save to database
        async with AsyncSessionLocal() as session:
            usage = UsageMetrics(**usage_data)
            session.add(usage)
            await session.commit()
        
        # Update daily counters in Redis
        today = datetime.utcnow().strftime('%Y-%m-%d')
        redis_key = f"usage:{user_id}:{today}:{action_type}"
        await self.redis_client.incr(redis_key)
        await self.redis_client.expire(redis_key, 86400 * 32)  # Keep for 32 days
    
    async def get_usage_stats(self, user_id: str, days: int = 30) -> Dict:
        """Get usage statistics for user"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        async with AsyncSessionLocal() as session:
            # Total usage by action type
            result = await session.execute("""
                SELECT action_type, COUNT(*) as count, 
                       AVG(processing_time_ms) as avg_time
                FROM usage_metrics 
                WHERE user_id = :user_id 
                  AND date >= :start_date 
                  AND date <= :end_date
                GROUP BY action_type
            """, {
                'user_id': user_id,
                'start_date': start_date,
                'end_date': end_date
            })
            
            usage_by_type = {row.action_type: {
                'count': row.count,
                'avg_processing_time': row.avg_time
            } for row in result}
            
            return {
                'period_days': days,
                'usage_by_type': usage_by_type,
                'total_actions': sum(stats['count'] for stats in usage_by_type.values())
            }
    
    # Session Management
    async def create_session(self, user_id: str, session_token: str, 
                           ip_address: str, user_agent: str, 
                           device_type: str = 'web') -> None:
        """Create user session"""
        expires_at = datetime.utcnow() + timedelta(days=30)
        
        async with AsyncSessionLocal() as session:
            user_session = UserSession(
                user_id=user_id,
                session_token=session_token,
                ip_address=ip_address,
                user_agent=user_agent,
                device_type=device_type,
                expires_at=expires_at
            )
            session.add(user_session)
            await session.commit()
        
        # Cache session in Redis
        session_data = {
            'user_id': user_id,
            'device_type': device_type,
            'created_at': datetime.utcnow().isoformat()
        }
        await self.redis_client.setex(f"session:{session_token}", 2592000, json.dumps(session_data))
    
    async def validate_session(self, session_token: str) -> Optional[Dict]:
        """Validate user session"""
        # Check Redis first (fast)
        session_data = await self.redis_client.get(f"session:{session_token}")
        if session_data:
            return json.loads(session_data)
        
        # Check database
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                session.query(UserSession)
                .filter(UserSession.session_token == session_token)
                .filter(UserSession.is_active == True)
                .filter(UserSession.expires_at > datetime.utcnow())
            )
            user_session = result.scalar_one_or_none()
            
            if user_session:
                # Update last activity
                user_session.last_activity_at = datetime.utcnow()
                await session.commit()
                
                session_data = {
                    'user_id': str(user_session.user_id),
                    'device_type': user_session.device_type
                }
                
                # Re-cache in Redis
                await self.redis_client.setex(f"session:{session_token}", 3600, json.dumps(session_data))
                return session_data
        
        return None
    
    # Achievement Management
    async def unlock_achievement(self, user_id: str, achievement_key: str, 
                               achievement_data: Dict) -> bool:
        """Unlock achievement for user"""
        async with AsyncSessionLocal() as session:
            # Check if already unlocked
            existing = await session.execute(
                session.query(UserAchievement)
                .filter(UserAchievement.user_id == user_id)
                .filter(UserAchievement.achievement_key == achievement_key)
            )
            
            if existing.scalar_one_or_none():
                return False  # Already unlocked
            
            # Create achievement
            achievement = UserAchievement(
                user_id=user_id,
                achievement_key=achievement_key,
                is_completed=True,
                completed_at=datetime.utcnow(),
                **achievement_data
            )
            session.add(achievement)
            await session.commit()
            
            logger.info(f"Unlocked achievement {achievement_key} for user {user_id}")
            return True
    
    # Arbitrage Management
    async def save_arbitrage_opportunity(self, opportunity_data: Dict) -> str:
        """Save arbitrage opportunity"""
        async with AsyncSessionLocal() as session:
            opportunity = ArbitrageOpportunity(**opportunity_data)
            session.add(opportunity)
            await session.commit()
            await session.refresh(opportunity)
            
            return str(opportunity.id)
    
    async def get_user_arbitrage_opportunities(self, user_id: str, 
                                             status: str = 'active') -> List[Dict]:
        """Get user's arbitrage opportunities"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                session.query(ArbitrageOpportunity)
                .filter(ArbitrageOpportunity.user_id == user_id)
                .filter(ArbitrageOpportunity.status == status)
                .order_by(ArbitrageOpportunity.net_profit.desc())
            )
            opportunities = result.scalars().all()
            return [self._arbitrage_to_dict(opp) for opp in opportunities]
    
    # Security Event Management
    async def log_security_event(self, event_data: Dict) -> None:
        """Log security event"""
        async with AsyncSessionLocal() as session:
            event = SecurityEvent(**event_data)
            session.add(event)
            await session.commit()
            
            # Alert on critical events
            if event_data.get('severity') == 'CRITICAL':
                await self._send_security_alert(event_data)
    
    # Cache Management
    async def _initialize_user_cache(self, user_id: str) -> None:
        """Initialize user-specific cache keys"""
        pipeline = self.redis_client.pipeline()
        pipeline.set(f"user:{user_id}:daily_usage", 0)
        pipeline.expire(f"user:{user_id}:daily_usage", 86400)
        await pipeline.execute()
    
    # Helper Methods
    def _user_to_dict(self, user) -> Dict:
        """Convert User model to dictionary"""
        if not user:
            return None
        
        return {
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'subscription_tier': user.subscription_tier,
            'subscription_status': user.subscription_status,
            'journey_type': user.journey_type,
            'total_profit': user.total_profit,
            'total_savings': user.total_savings,
            'success_streak': user.success_streak,
            'risk_alerts_avoided': user.risk_alerts_avoided,
            'preferences': user.preferences or {},
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None
        }
    
    def _verification_to_dict(self, verification) -> Dict:
        """Convert ItemVerification to dictionary"""
        return {
            'id': str(verification.id),
            'title': verification.title,
            'price': verification.price,
            'trust_score': verification.trust_score,
            'risk_level': verification.risk_level,
            'confidence_score': verification.confidence_score,
            'market_value': verification.market_value,
            'profit_potential': verification.profit_potential,
            'user_decision': verification.user_decision,
            'actual_outcome': verification.actual_outcome,
            'actual_profit': verification.actual_profit,
            'created_at': verification.created_at.isoformat()
        }
    
    def _arbitrage_to_dict(self, opportunity) -> Dict:
        """Convert ArbitrageOpportunity to dictionary"""
        return {
            'id': str(opportunity.id),
            'item_title': opportunity.item_title,
            'source_platform': opportunity.source_platform,
            'target_platform': opportunity.target_platform,
            'buy_price': opportunity.buy_price,
            'sell_price': opportunity.sell_price,
            'net_profit': opportunity.net_profit,
            'profit_margin': opportunity.profit_margin,
            'confidence_score': opportunity.confidence_score,
            'risk_level': opportunity.risk_level,
            'time_to_profit_days': opportunity.time_to_profit_days,
            'status': opportunity.status,
            'created_at': opportunity.created_at.isoformat(),
            'expires_at': opportunity.expires_at.isoformat() if opportunity.expires_at else None
        }
    
    async def _send_security_alert(self, event_data: Dict) -> None:
        """Send security alert notification"""
        # This would integrate with notification service
        logger.critical(f"SECURITY ALERT: {event_data}")

# Database initialization script
async def init_database():
    """Initialize database with sample data"""
    db = DatabaseManager()
    await db.initialize()
    
    print("✅ Database initialization complete!")
    
    # Create sample admin user
    try:
        admin_user = await db.create_user(
            email="admin@trustguard.com",
            password_hash="$2b$12$sample_hash_here",
            first_name="Admin",
            last_name="User",
            subscription_tier="enterprise",
            journey_type="flipper"
        )
        print(f"✅ Created admin user: {admin_user['id']}")
    except Exception as e:
        print(f"Admin user may already exist: {e}")
    
    await db.close()

if __name__ == "__main__":
    asyncio.run(init_database())
