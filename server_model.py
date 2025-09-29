# server_model.py - Enhanced model with governance and monitoring
"""
Enhanced server-side model with:
- Model versioning and backup
- Drift detection
- Performance monitoring
- Holdout validation
- Batch retraining capability
"""

import os
import math
import time
import json
import joblib
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import log_loss, accuracy_score
from collections import deque, defaultdict
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Feature definitions
FEATURE_KEYS = [
    "price_vs_market_pct",
    "seller_feedback_pct", 
    "account_age_days_norm",
    "uses_stock_images",
    "off_platform_payment",
    "price_anomaly_flag",
    "feedback_drop_flag",
    "desc_length_norm",
    "num_identical_listings_norm"
]

# Initial hand-tuned weights (interpretable baseline)
INITIAL_WEIGHTS = {
    "price_vs_market_pct": 1.0,
    "seller_feedback_pct": -1.5,
    "account_age_days_norm": -0.8,
    "uses_stock_images": 0.9,
    "off_platform_payment": 2.5,
    "price_anomaly_flag": 1.8,
    "feedback_drop_flag": 1.2,
    "desc_length_norm": 0.6,
    "num_identical_listings_norm": 0.3
}
INITIAL_BIAS = -1.0

MODEL_PATH_DEFAULT = "models/online_model.pkl"

def normalize_features(raw):
    """Enhanced feature normalization with bounds checking"""
    out = {}
    
    # Price vs market (0..1 scale)
    price_ratio = raw.get("price_vs_market_pct", 1.0)
    out["price_vs_market_pct"] = min(max(price_ratio / 3.0, 0.0), 1.0)
    
    # Seller feedback (0..1)
    feedback = raw.get("seller_feedback_pct", 0.98)
    out["seller_feedback_pct"] = min(max(feedback, 0.0), 1.0)
    
    # Account age normalized (0..1)
    age_norm = raw.get("account_age_days_norm", 0.5)
    out["account_age_days_norm"] = min(max(age_norm, 0.0), 1.0)
    
    # Binary flags (0 or 1)
    out["uses_stock_images"] = min(max(raw.get("uses_stock_images", 0.0), 0.0), 1.0)
    out["off_platform_payment"] = min(max(raw.get("off_platform_payment", 0.0), 0.0), 1.0)
    out["price_anomaly_flag"] = min(max(raw.get("price_anomaly_flag", 0.0), 0.0), 1.0)
    out["feedback_drop_flag"] = min(max(raw.get("feedback_drop_flag", 0.0), 0.0), 1.0)
    
    # Continuous features (0..1)
    out["desc_length_norm"] = min(max(raw.get("desc_length_norm", 0.0), 0.0), 1.0)
    out["num_identical_listings_norm"] = min(max(raw.get("num_identical_listings_norm", 0.0), 0.0), 1.0)
    
    return out

class ModelPerformanceMonitor:
    """Monitor model performance and detect drift"""
    
    def __init__(self, window_size=1000):
        self.window_size = window_size
        self.predictions = deque(maxlen=window_size)
        self.labels = deque(maxlen=window_size)
        self.daily_stats = defaultdict(list)
        
    def add_prediction(self, prediction, label=None):
        """Add a prediction (and optional true label) to monitoring"""
        timestamp = datetime.now()
        day_key = timestamp.strftime("%Y-%m-%d")
        
        self.predictions.append({
            "prediction": prediction,
            "timestamp": timestamp,
            "day": day_key
        })
        
        self.daily_stats[day_key].append(prediction)
        
        if label is not None:
            self.labels.append({
                "label": label,
                "timestamp": timestamp,
                "day": day_key
            })
    
    def get_drift_metrics(self):
        """Calculate drift detection metrics"""
        if len(self.daily_stats) < 7:  # Need at least a week of data
            return {"status": "insufficient_data", "days": len(self.daily_stats)}
        
        # Get recent vs baseline periods
        sorted_days = sorted(self.daily_stats.keys())
        recent_days = sorted_days[-3:]  # Last 3 days
        baseline_days = sorted_days[-10:-3]  # 7 days before that
        
        if len(baseline_days) < 3:
            return {"status": "insufficient_baseline", "days": len(baseline_days)}
        
        # Calculate average risk scores
        recent_avg = np.mean([
            np.mean(self.daily_stats[day]) 
            for day in recent_days
        ])
        baseline_avg = np.mean([
            np.mean(self.daily_stats[day])
            for day in baseline_days  
        ])
        
        # Drift detection
        drift_ratio = recent_avg / baseline_avg if baseline_avg > 0 else 1.0
        
        # Flag significant drift (>30% change)
        drift_detected = abs(drift_ratio - 1.0) > 0.3
        
        return {
            "status": "normal" if not drift_detected else "drift_detected",
            "recent_avg_risk": round(recent_avg, 3),
            "baseline_avg_risk": round(baseline_avg, 3),
            "drift_ratio": round(drift_ratio, 3),
            "days_monitored": len(self.daily_stats)
        }
    
    def get_accuracy_metrics(self):
        """Calculate accuracy if we have labels"""
        if len(self.labels) < 50:
            return {"status": "insufficient_labels", "count": len(self.labels)}
        
        # Match predictions with labels by timestamp (within 1 hour)
        matched_pairs = []
        for label_entry in list(self.labels)[-100:]:  # Last 100 labels
            label_time = label_entry["timestamp"]
            
            # Find closest prediction within 1 hour
            closest_pred = None
            min_time_diff = timedelta(hours=1)
            
            for pred_entry in self.predictions:
                time_diff = abs(pred_entry["timestamp"] - label_time)
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    closest_pred = pred_entry
            
            if closest_pred:
                matched_pairs.append({
                    "prediction": closest_pred["prediction"],
                    "label": label_entry["label"]
                })
        
        if len(matched_pairs) < 10:
            return {"status": "insufficient_matches", "count": len(matched_pairs)}
        
        # Calculate metrics
        y_true = [p["label"] for p in matched_pairs]
        y_prob = [p["prediction"] for p in matched_pairs]
        y_pred = [1 if p > 0.5 else 0 for p in y_prob]
        
        accuracy = accuracy_score(y_true, y_pred)
        try:
            logloss = log_loss(y_true, y_prob)
        except:
            logloss = float('inf')
        
        return {
            "status": "calculated",
            "accuracy": round(accuracy, 3),
            "log_loss": round(logloss, 3),
            "sample_size": len(matched_pairs)
        }

class EnhancedServerModel:
    """Enhanced server model with governance features"""
    
    def __init__(self, model_path=MODEL_PATH_DEFAULT, backup_interval=100):
        self.model_path = Path(model_path)
        self.backup_interval = backup_interval
        self.model_version = 1
        self.update_count = 0
        self.created_at = datetime.now()
        
        # Performance monitoring
        self.monitor = ModelPerformanceMonitor()
        
        # Create models directory
        self.model_path.parent.mkdir(exist_ok=True)
        
        # Load or create model
        self._load_or_create_model()
        
        # Holdout buffer for validation (store last 100 examples)
        self.holdout_buffer = deque(maxlen=100)
        
        logger.info(f"Model initialized: version {self.model_version}")
    
    def _load_or_create_model(self):
        """Load existing model or create new one"""
        if self.model_path.exists():
            try:
                checkpoint = joblib.load(self.model_path)
                self.clf = checkpoint.get("model")
                self.model_version = checkpoint.get("version", 1)
                self.update_count = checkpoint.get("update_count", 0)
                self.created_at = checkpoint.get("created_at", datetime.now())
                
                logger.info(f"Loaded model version {self.model_version} with {self.update_count} updates")
                return
            except Exception as e:
                logger.warning(f"Could not load model: {e}. Creating new one.")
        
        # Create new model
        self.clf = SGDClassifier(
            loss="log_loss", 
            max_iter=5,
            learning_rate="adaptive",
            eta0=0.01,
            random_state=42
        )
        
        # Initialize with dummy data
        dummy_X = np.zeros((1, len(FEATURE_KEYS)))
        self.clf.partial_fit(dummy_X, [0], classes=[0, 1])
        
        self._save_checkpoint()
        logger.info("Created new model")
    
    def _save_checkpoint(self):
        """Save model checkpoint with metadata"""
        checkpoint = {
            "model": self.clf,
            "version": self.model_version,
            "update_count": self.update_count,
            "created_at": self.created_at,
            "updated_at": datetime.now(),
            "feature_keys": FEATURE_KEYS
        }
        
        try:
            joblib.dump(checkpoint, self.model_path)
        except Exception as e:
            logger.error(f"Could not save model: {e}")
    
    def _create_backup(self):
        """Create timestamped backup of current model"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.model_path.parent / f"model_backup_{timestamp}_v{self.model_version}.pkl"
        
        try:
            joblib.dump({
                "model": self.clf,
                "version": self.model_version,
                "update_count": self.update_count,
                "backup_created": datetime.now()
            }, backup_path)
            logger.info(f"Created backup: {backup_path}")
        except Exception as e:
            logger.error(f"Could not create backup: {e}")
    
    def features_to_vector(self, features_dict):
        """Convert features dict to numpy array"""
        return np.array([[features_dict.get(k, 0.0) for k in FEATURE_KEYS]])
    
    def predict_prob(self, features_dict):
        """Get prediction probability with monitoring"""
        X = self.features_to_vector(features_dict)
        
        try:
            # Get prediction from model
            prob = float(self.clf.predict_proba(X)[0][1])
        except Exception as e:
            logger.warning(f"Model prediction failed: {e}. Using fallback.")
            # Fallback to manual logistic regression
            s = INITIAL_BIAS
            for k, w in INITIAL_WEIGHTS.items():
                s += w * float(features_dict.get(k, 0.0))
            prob = 1.0 / (1.0 + math.exp(-max(-500, min(500, s))))  # Bound to prevent overflow
        
        # Add to monitoring
        self.monitor.add_prediction(prob)
        
        return prob
    
    def explain_top_contributors(self, features_dict, top_n=4):
        """Get top contributing features"""
        try:
            # Use model coefficients if available
            coef = self.clf.coef_[0] 
            weights = {k: float(v) for k, v in zip(FEATURE_KEYS, coef)}
        except:
            # Fallback to initial weights
            weights = INITIAL_WEIGHTS.copy()
        
        # Calculate contributions
        contributions = []
        for k in FEATURE_KEYS:
            val = float(features_dict.get(k, 0.0))
            w = weights.get(k, 0.0)
            contributions.append((k, w * val))
        
        # Sort by absolute contribution
        contributions.sort(key=lambda x: abs(x[1]), reverse=True)
        
        return [
            {"feature": k, "contribution": round(float(v), 4)} 
            for k, v in contributions[:top_n]
        ]
    
    def online_update(self, features_dict, label):
        """Perform online update with governance"""
        try:
            X = self.features_to_vector(features_dict)
            y = [int(label)]
            
            # Add to holdout buffer (for validation)
            self.holdout_buffer.append({
                "features": features_dict.copy(),
                "label": label,
                "timestamp": datetime.now()
            })
            
            # Perform update
            self.clf.partial_fit(X, y)
            self.update_count += 1
            self.model_version += 1
            
            # Add to monitoring
            self.monitor.add_prediction(self.predict_prob(features_dict), label)
            
            # Save checkpoint
            self._save_checkpoint()
            
            # Create backup if needed
            if self.update_count % self.backup_interval == 0:
                self._create_backup()
            
            logger.info(f"Model updated: version {self.model_version}, total updates: {self.update_count}")
            return True
            
        except Exception as e:
            logger.error(f"Online update failed: {e}")
            return False
    
    def get_model_status(self):
        """Get comprehensive model status"""
        status = {
            "version": self.model_version,
            "update_count": self.update_count,
            "created_at": self.created_at.isoformat(),
            "feature_count": len(FEATURE_KEYS),
            "holdout_buffer_size": len(self.holdout_buffer)
        }
        
        # Add drift metrics
        drift_metrics = self.monitor.get_drift_metrics()
        status["drift_detection"] = drift_metrics
        
        # Add accuracy if available
        accuracy_metrics = self.monitor.get_accuracy_metrics()
        status["accuracy_metrics"] = accuracy_metrics
        
        # Model weights summary
        try:
            coef = self.clf.coef_[0]
            status["weights"] = {k: round(float(v), 4) for k, v in zip(FEATURE_KEYS, coef)}
            status["intercept"] = round(float(self.clf.intercept_[0]), 4)
        except:
            status["weights"] = INITIAL_WEIGHTS
            status["intercept"] = INITIAL_BIAS
        
        return status
    
    def validate_on_holdout(self):
