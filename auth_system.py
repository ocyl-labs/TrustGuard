# auth_system.py
"""
Complete authentication and session management system
Includes: JWT tokens, password hashing, session management, rate limiting
"""

import os
import jwt
import bcrypt
import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
import re
from email_validator import validate_email, EmailNotValidError

from database_setup import DatabaseManager
from flask import Flask, request, jsonify, g
from functools import wraps
import redis.asyncio as redis

logger = logging.getLogger(__name__)

@dataclass
class AuthConfig:
    """Authentication configuration"""
    jwt_secret: str = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15

class AuthenticationError(Exception):
    """Custom authentication error"""
    pass

class AuthorizationError(Exception):
    """Custom authorization error"""
    pass

class AuthManager:
    """Handles all authentication and authorization logic"""
    
    def __init__(self, config: AuthConfig, db_manager: DatabaseManager):
        self.config = config
        self.db = db_manager
        self.redis_client = None
        
    async def initialize(self):
        """Initialize Redis client for rate limiting"""
        self.redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        await self.redis_client.ping()
        logger.info("✅ AuthManager initialized")
    
    # Password Management
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < self.config.password_min_length:
            errors.append(f"Password must be at least {self.config.password_min_length} characters")
        
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r"\d", password):
            errors.append("Password must contain at least one number")
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    # Rate Limiting
    async def check_rate_limit(self, identifier: str, action: str, 
                             max_attempts: int = None, 
                             window_minutes: int = None) -> bool:
        """Check if action is rate limited"""
        max_attempts = max_attempts or self.config.max_login_attempts
        window_minutes = window_minutes or self.config.lockout_duration_minutes
        
        key = f"rate_limit:{action}:{identifier}"
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(minutes=window_minutes)
        
        # Get attempts in current window
        attempts = await self.redis_client.zcount(key, 
                                                 window_start.timestamp(), 
                                                 current_time.timestamp())
        
        if attempts >= max_attempts:
            logger.warning(f"Rate limit exceeded for {identifier} on {action}")
            return False
        
        # Record this attempt
        await self.redis_client.zadd(key, {current_time.timestamp(): current_time.timestamp()})
        await self.redis_client.expire(key, window_minutes * 60)
        
        return True
    
    async def clear_rate_limit(self, identifier: str, action: str):
        """Clear rate limiting for identifier"""
        key = f"rate_limit:{action}:{identifier}"
        await self.redis_client.delete(key)
    
    # JWT Token Management
    def create_access_token(self, user_id: str, user_data: Dict) -> str:
        """Create JWT access token"""
        payload = {
            'user_id': user_id,
            'email': user_data.get('email'),
            'subscription_tier': user_data.get('subscription_tier', 'free'),
            'exp': datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        return jwt.encode(payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=self.config.refresh_token_expire_days),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        
        return jwt.encode(payload, self.config.jwt_secret, algorithm=self.config.jwt_algorithm)
    
    def verify_token(self, token: str, token_type: str = 'access') -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.config.jwt_secret, 
                               algorithms=[self.config.jwt_algorithm])
            
            if payload.get('type') != token_type:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.info("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    # Registration
    async def register_user(self, email: str, password: str, 
                          first_name: str = None, last_name: str = None,
                          **kwargs) -> Dict:
        """Register new user"""
        # Validate email
        try:
            validated_email = validate_email(email)
            email = validated_email.email
        except EmailNotValidError as e:
            raise AuthenticationError(f"Invalid email: {e}")
        
        # Check if user already exists
        existing_user = await self.db.get_user_by_email(email)
        if existing_user:
            raise AuthenticationError("User with this email already exists")
        
        # Validate password strength
        is_valid, password_errors = self.validate_password_strength(password)
        if not is_valid:
            raise AuthenticationError(f"Weak password: {'; '.join(password_errors)}")
        
        # Check registration rate limiting
        ip_address = request.remote_addr if request else "unknown"
        if not await self.check_rate_limit(ip_address, "registration", 3, 60):
            raise AuthenticationError("Too many registration attempts. Please try again later.")
        
        # Hash password and create user
        password_hash = self.hash_password(password)
        
        try:
            user_data = await self.db.create_user(
                email=email,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                **kwargs
            )
            
            logger.info(f"User registered: {email}")
            
            # Clear rate limit on successful registration
            await self.clear_rate_limit(ip_address, "registration")
            
            return user_data
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise AuthenticationError("Failed to create user account")
    
    # Login
    async def login_user(self, email: str, password: str, 
                        device_type: str = 'web') -> Dict:
        """Authenticate user and create session"""
        # Rate limiting check
        if not await self.check_rate_limit(email, "login"):
            raise AuthenticationError(
                f"Too many failed login attempts. Account locked for "
                f"{self.config.lockout_duration_minutes} minutes."
            )
        
        # Get user from database
        user = await self.db.get_user_by_email(email)
        if not user:
            raise AuthenticationError("Invalid email or password")
        
        # Verify password
        if not self.verify_password(password, user['password_hash']):
            raise AuthenticationError("Invalid email or password")
        
        # Clear rate limit on successful login
        await self.clear_rate_limit(email, "login")
        
        # Create tokens
        access_token = self.create_access_token(user['id'], user)
        refresh_token = self.create_refresh_token(user['id'])
        
        # Create session in database
        session_token = secrets.token_urlsafe(32)
        ip_address = request.remote_addr if request else "unknown"
        user_agent = request.headers.get('User-Agent', '') if request else "unknown"
        
        await self.db.create_session(
            user_id=user['id'],
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=device_type
        )
        
        # Update last login
        await self.db.update_user(user['id'], last_login_at=datetime.utcnow())
        
        logger.info(f"User logged in: {email}")
        
        return {
            'user': user,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'session_token': session_token,
            'expires_in': self.config.access_token_expire_minutes * 60
        }
    
    # Token Refresh
    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """Refresh access token using refresh token"""
        payload = self.verify_token(refresh_token, 'refresh')
        if not payload:
            raise AuthenticationError("Invalid refresh token")
        
        user_id = payload['user_id']
        user = await self.db.get_user_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")
        
        # Create new access token
        access_token = self.create_access_token(user_id, user)
        
        return {
            'access_token': access_token,
            'expires_in': self.config.access_token_expire_minutes * 60
        }
    
    # Session Management
    async def validate_session_token(self, session_token: str) -> Optional[Dict]:
        """Validate session token"""
        return await self.db.validate_session(session_token)
    
    async def logout_user(self, session_token: str = None, user_id: str = None):
        """Logout user and invalidate sessions"""
        if session_token:
            # Invalidate specific session
            await self.redis_client.delete(f"session:{session_token}")
        elif user_id:
            # Invalidate all user sessions
            pattern = f"session:*"
            sessions = await self.redis_client.keys(pattern)
            
            pipeline = self.redis_client.pipeline()
            for session_key in sessions:
                session_data = await self.redis_client.get(session_key)
                if session_data:
                    data = json.loads(session_data)
                    if data.get('user_id') == user_id:
                        pipeline.delete(session_key)
            await pipeline.execute()
    
    # Password Reset
    async def request_password_reset(self, email: str) -> str:
        """Request password reset token"""
        user = await self.db.get_user_by_email(email)
        if not user:
            # Don't reveal if email exists
            logger.info(f"Password reset requested for non-existent email: {email}")
            return "If the email exists, a reset link has been sent."
        
        # Check rate limiting
        if not await self.check_rate_limit(email, "password_reset", 3, 60):
            raise AuthenticationError("Too many password reset requests. Please try again later.")
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        reset_expires = datetime.utcnow() + timedelta(hours=1)
        
        # Store reset token in Redis
        await self.redis_client.setex(
            f"reset_token:{reset_token}",
            3600,  # 1 hour
            user['id']
        )
        
        # In production, send email here
        logger.info(f"Password reset token generated for {email}: {reset_token}")
        
        return "Password reset instructions have been sent to your email."
    
    async def reset_password(self, reset_token: str, new_password: str) -> str:
        """Reset password using reset token"""
        # Validate new password
        is_valid, password_errors = self.validate_password_strength(new_password)
        if not is_valid:
            raise AuthenticationError(f"Weak password: {'; '.join(password_errors)}")
        
        # Get user ID from reset token
        user_id = await self.redis_client.get(f"reset_token:{reset_token}")
        if not user_id:
            raise AuthenticationError("Invalid or expired reset token")
        
        # Update password
        password_hash = self.hash_password(new_password)
        await self.db.update_user(user_id, password_hash=password_hash)
        
        # Invalidate reset token
        await self.redis_client.delete(f"reset_token:{reset_token}")
        
        # Logout all sessions for security
        await self.logout_user(user_id=user_id)
        
        logger.info(f"Password reset completed for user {user_id}")
        return "Password has been successfully reset."

# Flask Authentication Decorators
def create_auth_decorators(auth_manager: AuthManager):
    """Create Flask authentication decorators"""
    
    def require_auth(f):
        """Require valid authentication"""
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Missing or invalid authorization header'}), 401
            
            token = auth_header.split(' ')[1]
            payload = auth_manager.verify_token(token, 'access')
            
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            # Store user info in Flask's g object
            g.user_id = payload['user_id']
            g.user_email = payload.get('email')
            g.subscription_tier = payload.get('subscription_tier', 'free')
            g.token_payload = payload
            
            return await f(*args, **kwargs)
        
        return decorated_function
    
    def require_subscription(min_tier: str):
        """Require minimum subscription tier"""
        tier_levels = {'free': 0, 'basic': 1, 'pro': 2, 'enterprise': 3}
        
        def decorator(f):
            @wraps(f)
            @require_auth
            async def decorated_function(*args, **kwargs):
                user_tier = g.subscription_tier
                
                if tier_levels.get(user_tier, 0) < tier_levels.get(min_tier, 0):
                    return jsonify({
                        'error': 'Subscription upgrade required',
                        'required_tier': min_tier,
                        'current_tier': user_tier,
                        'upgrade_url': '/pricing'
                    }), 403
                
                return await f(*args, **kwargs)
            
            return decorated_function
        return decorator
    
    def require_admin(f):
        """Require admin privileges"""
        @wraps(f)
        @require_auth
        async def decorated_function(*args, **kwargs):
            # Check if user has admin role
            user = await auth_manager.db.get_user_by_id(g.user_id)
            if not user or user.get('subscription_tier') != 'enterprise':
                return jsonify({'error': 'Admin access required'}), 403
            
            return await f(*args, **kwargs)
        
        return decorated_function
    
    return require_auth, require_subscription, require_admin

# Flask Auth Routes
def create_auth_routes(app: Flask, auth_manager: AuthManager):
    """Create Flask authentication routes"""
    
    @app.route('/auth/register', methods=['POST'])
    async def register():
        """User registration endpoint"""
        try:
            data = request.get_json() or {}
            
            email = data.get('email', '').strip()
            password = data.get('password', '')
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            journey_type = data.get('journey_type', 'buyer')
            
            if not email or not password:
                return jsonify({'error': 'Email and password are required'}), 400
            
            user = await auth_manager.register_user(
                email=email,
                password=password,
                first_name=first_name or None,
                last_name=last_name or None,
                journey_type=journey_type
            )
            
            # Auto-login after registration
            login_result = await auth_manager.login_user(email, password)
            
            return jsonify({
                'success': True,
                'message': 'Account created successfully',
                'user': login_result['user'],
                'access_token': login_result['access_token'],
                'refresh_token': login_result['refresh_token']
            }), 201
            
        except AuthenticationError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return jsonify({'error': 'Registration failed'}), 500
    
    @app.route('/auth/login', methods=['POST'])
    async def login():
        """User login endpoint"""
        try:
            data = request.get_json() or {}
            
            email = data.get('email', '').strip()
            password = data.get('password', '')
            device_type = data.get('device_type', 'web')
            
            if not email or not password:
                return jsonify({'error': 'Email and password are required'}), 400
            
            login_result = await auth_manager.login_user(email, password, device_type)
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': login_result['user'],
                'access_token': login_result['access_token'],
                'refresh_token': login_result['refresh_token'],
                'expires_in': login_result['expires_in']
            })
            
        except AuthenticationError as e:
            return jsonify({'error': str(e)}), 401
        except Exception as e:
            logger.error(f"Login error: {e}")
            return jsonify({'error': 'Login failed'}), 500
    
    @app.route('/auth/refresh', methods=['POST'])
    async def refresh_token():
        """Refresh access token"""
        try:
            data = request.get_json() or {}
            refresh_token = data.get('refresh_token')
            
            if not refresh_token:
                return jsonify({'error': 'Refresh token required'}), 400
            
            result = await auth_manager.refresh_access_token(refresh_token)
            
            return jsonify({
                'success': True,
                'access_token': result['access_token'],
                'expires_in': result['expires_in']
            })
            
        except AuthenticationError as e:
            return jsonify({'error': str(e)}), 401
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return jsonify({'error': 'Token refresh failed'}), 500
    
    @app.route('/auth/logout', methods=['POST'])
    async def logout():
        """User logout endpoint"""
        try:
            data = request.get_json() or {}
            session_token = data.get('session_token')
            
            if session_token:
                await auth_manager.logout_user(session_token=session_token)
            
            return jsonify({
                'success': True,
                'message': 'Logged out successfully'
            })
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return jsonify({'error': 'Logout failed'}), 500
    
    @app.route('/auth/forgot-password', methods=['POST'])
    async def forgot_password():
        """Request password reset"""
        try:
            data = request.get_json() or {}
            email = data.get('email', '').strip()
            
            if not email:
                return jsonify({'error': 'Email is required'}), 400
            
            message = await auth_manager.request_password_reset(email)
            
            return jsonify({
                'success': True,
                'message': message
            })
            
        except AuthenticationError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Password reset request error: {e}")
            return jsonify({'error': 'Password reset request failed'}), 500
    
    @app.route('/auth/reset-password', methods=['POST'])
    async def reset_password():
        """Reset password with token"""
        try:
            data = request.get_json() or {}
            reset_token = data.get('reset_token')
            new_password = data.get('new_password')
            
            if not reset_token or not new_password:
                return jsonify({'error': 'Reset token and new password are required'}), 400
            
            message = await auth_manager.reset_password(reset_token, new_password)
            
            return jsonify({
                'success': True,
                'message': message
            })
            
        except AuthenticationError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            return jsonify({'error': 'Password reset failed'}), 500
    
    @app.route('/auth/profile', methods=['GET'])
    async def get_profile():
        """Get user profile (requires authentication)"""
        require_auth, _, _ = create_auth_decorators(auth_manager)
        
        @require_auth
        async def _get_profile():
            try:
                user = await auth_manager.db.get_user_by_id(g.user_id)
                if not user:
                    return jsonify({'error': 'User not found'}), 404
                
                # Remove sensitive data
                safe_user = {k: v for k, v in user.items() if k != 'password_hash'}
                
                return jsonify({
                    'success': True,
                    'user': safe_user
                })
                
            except Exception as e:
                logger.error(f"Profile fetch error: {e}")
                return jsonify({'error': 'Failed to fetch profile'}), 500
        
        return await _get_profile()
    
    @app.route('/auth/profile', methods=['PUT'])
    async def update_profile():
        """Update user profile (requires authentication)"""
        require_auth, _, _ = create_auth_decorators(auth_manager)
        
        @require_auth
        async def _update_profile():
            try:
                data = request.get_json() or {}
                
                # Only allow certain fields to be updated
                allowed_fields = ['first_name', 'last_name', 'username', 'preferences', 'journey_type']
                updates = {k: v for k, v in data.items() if k in allowed_fields}
                
                if not updates:
                    return jsonify({'error': 'No valid fields to update'}), 400
                
                user = await auth_manager.db.update_user(g.user_id, **updates)
                if not user:
                    return jsonify({'error': 'User not found'}), 404
                
                # Remove sensitive data
                safe_user = {k: v for k, v in user.items() if k != 'password_hash'}
                
                return jsonify({
                    'success': True,
                    'message': 'Profile updated successfully',
                    'user': safe_user
                })
                
            except Exception as e:
                logger.error(f"Profile update error: {e}")
                return jsonify({'error': 'Failed to update profile'}), 500
        
        return await _update_profile()

# Usage Example
async def setup_auth_system(app: Flask, db_manager: DatabaseManager):
    """Setup complete authentication system"""
    
    # Initialize auth manager
    config = AuthConfig()
    auth_manager = AuthManager(config, db_manager)
    await auth_manager.initialize()
    
    # Create auth routes
    create_auth_routes(app, auth_manager)
    
    # Create decorators for use in other routes
    require_auth, require_subscription, require_admin = create_auth_decorators(auth_manager)
    
    logger.info("✅ Authentication system setup complete")
    
    return auth_manager, require_auth, require_subscription, require_admin

if __name__ == "__main__":
    # Test the authentication system
    import asyncio
    from database_setup import DatabaseManager
    
    async def test_auth():
        db = DatabaseManager()
        await db.initialize()
        
        config = AuthConfig()
        auth = AuthManager(config, db)
        await auth.initialize()
        
        print("Testing authentication system...")
        
        try:
            # Test registration
            user = await auth.register_user(
                email="test@example.com",
                password="SecurePass123!",
                first_name="Test",
                last_name="User"
            )
            print(f"✅ User registered: {user['email']}")
            
            # Test login
            login_result = await auth.login_user("test@example.com", "SecurePass123!")
            print(f"✅ Login successful, token: {login_result['access_token'][:20]}...")
            
            # Test token verification
            payload = auth.verify_token(login_result['access_token'])
            print(f"✅ Token verified for user: {payload['user_id']}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        await auth.redis_client.close()
        await db.close()
    
    asyncio.run(test_auth())
