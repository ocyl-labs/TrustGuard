# test_suite.py
"""
Comprehensive test suite for eBay Profit Analyzer
Run with: python test_suite.py
"""
import requests
import json
import time
from pathlib import Path

# Test configuration
BASE_URL = "http://127.0.0.1:5000"
TEST_RESULTS = []

def log_test(test_name, passed, details=""):
    """Log test results"""
    status = "✅ PASS" if passed else "❌ FAIL"
    result = f"{status} - {test_name}"
    if details:
        result += f"\n    Details: {details}"
    print(result)
    TEST_RESULTS.append({"test": test_name, "passed": passed, "details": details})

def test_server_health():
    """Test if Flask server is running"""
    try:
        response = requests.get(f"{BASE_URL}/model-info", timeout=5)
        passed = response.status_code == 200
        log_test("Server Health Check", passed, f"Status: {response.status_code}")
        return passed
    except Exception as e:
        log_test("Server Health Check", False, str(e))
        return False

def test_value_item_basic():
    """Test basic /value-item functionality"""
    payload = {
        "title": "iPhone 13 Pro Max 256GB Unlocked",
        "listing_price": 800,
        "description": "Brand new iPhone 13 Pro Max in excellent condition"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/value-item", json=payload, timeout=10)
        data = response.json()
        
        # Check required fields
        required_fields = ["market_value", "profit", "risk_score", "category", "explain_top_features"]
        missing_fields = [f for f in required_fields if f not in data]
        
        passed = response.status_code == 200 and not missing_fields
        details = f"Response keys: {list(data.keys())}"
        if missing_fields:
            details += f", Missing: {missing_fields}"
            
        log_test("Value Item Basic", passed, details)
        return data if passed else None
        
    except Exception as e:
        log_test("Value Item Basic", False, str(e))
        return None

def test_value_item_edge_cases():
    """Test edge cases for /value-item"""
    test_cases = [
        {"title": "", "expected_status": 400},  # Empty title
        {"title": "Very Rare Unique Item XYZ123"}, # Unusual item
        {"title": "MacBook Pro", "listing_price": 0.01}, # Extremely low price
        {"title": "Gold Bar 999 Pure", "listing_price": 50000}, # High price item
    ]
    
    all_passed = True
    for i, case in enumerate(test_cases):
        try:
            response = requests.post(f"{BASE_URL}/value-item", json=case, timeout=10)
            expected_status = case.get("expected_status", 200)
            
            passed = response.status_code == expected_status
            if not passed:
                all_passed = False
                
            details = f"Case {i+1}: Status {response.status_code}, Expected {expected_status}"
            log_test(f"Edge Case {i+1}", passed, details)
            
        except Exception as e:
            log_test(f"Edge Case {i+1}", False, str(e))
            all_passed = False
    
    return all_passed

def test_labeling_system():
    """Test the labeling and online learning system"""
    # First get a prediction to get features
    item_data = test_value_item_basic()
    if not item_data:
        log_test("Labeling System", False, "Could not get item data for labeling test")
        return False
    
    # Test labeling endpoint
    label_payload = {
        "item_id": "test_iphone_123",
        "label": 1,  # Mark as risky
        "label_source": "test_suite",
        "features": item_data.get("features", {})
    }
    
    try:
        response = requests.post(f"{BASE_URL}/label-listing", json=label_payload, timeout=5)
        data = response.json()
        
        passed = response.status_code == 200 and data.get("ok") is True
        log_test("Labeling System", passed, f"Response: {data}")
        
        # Verify log file was created
        log_file = Path("logs/labels.jsonl")
        if log_file.exists():
            with open(log_file, 'r') as f:
                lines = f.readlines()
                log_test("Label Persistence", len(lines) > 0, f"Found {len(lines)} label records")
        
        return passed
        
    except Exception as e:
        log_test("Labeling System", False, str(e))
        return False

def test_model_explainability():
    """Test model explainability features"""
    payload = {
        "title": "Suspicious iPhone Deal",
        "listing_price": 50,  # Very low price to trigger risk flags
        "seller_info": {
            "feedback_pct": 85,  # Lower feedback
            "account_age_days": 30  # New account
        },
        "description": "New"  # Very short description
    }
    
    try:
        response = requests.post(f"{BASE_URL}/value-item", json=payload, timeout=10)
        data = response.json()
        
        explanations = data.get("explain_top_features", [])
        risk_score = data.get("risk_score", 0)
        
        # Should have explanations and elevated risk score
        has_explanations = len(explanations) > 0
        has_risk_score = risk_score > 0.3  # Should be flagged as risky
        
        passed = has_explanations and has_risk_score
        details = f"Risk score: {risk_score}, Explanations: {len(explanations)}"
        
        log_test("Model Explainability", passed, details)
        return passed
        
    except Exception as e:
        log_test("Model Explainability", False, str(e))
        return False

def test_dummy_mode():
    """Test system works in DUMMY_KEY mode"""
    # This should work even without real eBay API key
    payload = {"title": "Test Product DUMMY Mode"}
    
    try:
        response = requests.post(f"{BASE_URL}/value-item", json=payload, timeout=10)
        data = response.json()
        
        # Should get reasonable dummy data
        has_market_value = data.get("market_value", 0) > 0
        has_sold_count = "sold_count" in data
        
        passed = response.status_code == 200 and has_market_value and has_sold_count
        log_test("Dummy Mode Operation", passed, f"Market value: {data.get('market_value')}")
        return passed
        
    except Exception as e:
        log_test("Dummy Mode Operation", False, str(e))
        return False

def test_performance():
    """Test response time performance"""
    payload = {"title": "Performance Test Item"}
    
    start_time = time.time()
    try:
        response = requests.post(f"{BASE_URL}/value-item", json=payload, timeout=15)
        end_time = time.time()
        
        response_time = end_time - start_time
        passed = response.status_code == 200 and response_time < 10.0  # Should respond within 10s
        
        log_test("Performance Test", passed, f"Response time: {response_time:.2f}s")
        return passed
        
    except Exception as e:
        log_test("Performance Test", False, str(e))
        return False

def run_all_tests():
    """Run complete test suite"""
    print("🧪 Starting eBay Profit Analyzer Test Suite\n")
    
    # Core functionality tests
    test_server_health()
    test_value_item_basic()
    test_value_item_edge_cases()
    test_labeling_system()
    test_model_explainability()
    test_dummy_mode()
    test_performance()
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed_tests = sum(1 for result in TEST_RESULTS if result["passed"])
    total_tests = len(TEST_RESULTS)
    
    print(f"Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! System is ready for production.")
    else:
        print("⚠️  Some tests failed. Please review and fix issues.")
        
    # Failed test details
    failed_tests = [r for r in TEST_RESULTS if not r["passed"]]
    if failed_tests:
        print("\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"  - {test['test']}: {test['details']}")

if __name__ == "__main__":
    run_all_tests()
