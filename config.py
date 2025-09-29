# config.py - Enhanced configuration with environment support
import os
from pathlib import Path

# Environment detection
ENV = os.getenv("FLASK_ENV", "development")
DEBUG = ENV == "development"

# eBay API Configuration
EBAY_APP_ID = os.getenv("EBAY_APP_ID", "DUMMY_KEY")
EBAY_CERT_ID = os.getenv("EBAY_CERT_ID", "")
EBAY_DEV_ID = os.getenv("EBAY_DEV_ID", "")

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))

# Cache Configuration
CACHE_EXPIRY = int(os.getenv("CACHE_EXPIRY", 3600))  # 1 hour default
CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", 1000))  # Max cached items

# Model Configuration
MODEL_DIR = Path(os.getenv("MODEL_DIR", "models"))
MODEL_PATH = MODEL_DIR / "online_model.pkl"
MODEL_BACKUP_INTERVAL = int(os.getenv("MODEL_BACKUP_INTERVAL", 100))  # Backup every N updates

# Logging Configuration
LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LABELS_FILE = LOG_DIR / "labels.jsonl"
APP_LOG_FILE = LOG_DIR / "app.log"

# Risk Scoring Configuration
RISK_THRESHOLD_HIGH = float(os.getenv("RISK_THRESHOLD_HIGH", 0.7))
RISK_THRESHOLD_MEDIUM = float(os.getenv("RISK_THRESHOLD_MEDIUM", 0.4))

# Feature Engineering Configuration
MAX_PRICE_RATIO = float(os.getenv("MAX_PRICE_RATIO", 3.0))
MIN_DESCRIPTION_LENGTH = int(os.getenv("MIN_DESCRIPTION_LENGTH", 30))
MAX_ACCOUNT_AGE_DAYS = int(os.getenv("MAX_ACCOUNT_AGE_DAYS", 3650))

# Rate Limiting
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", 100))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 3600))  # 1 hour

# Database Configuration (for future SQLite/Postgres upgrade)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{LOG_DIR}/labels.db")

# Ensure directories exist
def create_directories():
    """Create necessary directories if they don't exist"""
    MODEL_DIR.mkdir(exist_ok=True)
    LOG_DIR.mkdir(exist_ok=True)
    
# Validation
def validate_config():
    """Validate configuration and warn about issues"""
    issues = []
    
    if EBAY_APP_ID == "DUMMY_KEY":
        issues.append("⚠️  Using DUMMY_KEY for eBay API - real data unavailable")
    
    if not MODEL_DIR.exists():
        issues.append(f"⚠️  Model directory doesn't exist: {MODEL_DIR}")
        
    if not LOG_DIR.exists():
        issues.append(f"⚠️  Log directory doesn't exist: {LOG_DIR}")
        
    return issues

# Configuration summary
def get_config_summary():
    """Get configuration summary for logging"""
    return {
        "environment": ENV,
        "ebay_api": "REAL" if EBAY_APP_ID != "DUMMY_KEY" else "DUMMY",
        "model_path": str(MODEL_PATH),
        "cache_expiry": CACHE_EXPIRY,
        "risk_thresholds": {
            "high": RISK_THRESHOLD_HIGH,
            "medium": RISK_THRESHOLD_MEDIUM
        }
    }

if __name__ == "__main__":
    create_directories()
    issues = validate_config()
    
    print("🔧 Configuration Summary:")
    summary = get_config_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    if issues:
        print("\n⚠️  Configuration Issues:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ Configuration looks good!")
