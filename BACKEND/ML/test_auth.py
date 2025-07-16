#!/usr/bin/env python3
"""
Test script for ML service role-based access control.
This script tests the authentication and authorization for churn prediction and training APIs.
"""

import requests
import json
import os
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8090/ml"  # Through API Gateway
AUTH_URL = "http://localhost:8090/auth/v1/auth"  # Auth service

def get_auth_token(username: str, password: str) -> Dict[str, Any]:
    """Get JWT token from auth service"""
    login_data = {
        "customer_name_or_email": username,
        "password": password
    }
    
    response = requests.post(f"{AUTH_URL}/login", json=login_data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None

def test_endpoint(endpoint: str, token: str, method: str = "GET", files: Dict = None, data: Dict = None) -> Dict[str, Any]:
    """Test an endpoint with authentication"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "POST":
            if files:
                response = requests.post(url, headers=headers, files=files, data=data)
            else:
                response = requests.post(url, headers=headers, json=data)
        else:
            response = requests.get(url, headers=headers)
        
        return {
            "status_code": response.status_code,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "success": response.status_code < 400
        }
    except Exception as e:
        return {
            "status_code": None,
            "response": str(e),
            "success": False
        }

def create_test_csv():
    """Create a simple test CSV file for churn prediction"""
    test_data = """customer_id,Customer Name,Purchase Date,Product Category,Quantity,Payment Method,Customer_Labels
1,John Doe,2024-01-15,Electronics,2,Credit Card,Regular
2,Jane Smith,2024-01-20,Clothing,1,Cash,VIP
3,Bob Johnson,2024-01-25,Electronics,3,Credit Card,Regular
"""
    with open("test_churn_data.csv", "w") as f:
        f.write(test_data)
    return "test_churn_data.csv"

def main():
    print("🧪 Testing ML Service Role-Based Access Control")
    print("=" * 60)
    
    # Test scenarios
    test_users = [
        {"username": "user_test", "password": "password123", "expected_role": "user"},
        {"username": "staff_test", "password": "password123", "expected_role": "staff"},
        {"username": "admin_test", "password": "password123", "expected_role": "admin"}
    ]
    
    # Create test file
    test_file = create_test_csv()
    
    for user in test_users:
        print(f"\n👤 Testing with {user['expected_role']} user: {user['username']}")
        print("-" * 40)
        
        # Get token
        auth_result = get_auth_token(user['username'], user['password'])
        if not auth_result:
            print(f"❌ Failed to authenticate {user['username']}")
            continue
        
        token = auth_result.get('access_token')
        actual_role = auth_result.get('role')
        
        print(f"✅ Authenticated successfully - Role: {actual_role}")
        
        # Test 1: Access root endpoint (should work for all authenticated users)
        print("\n📋 Testing root endpoint...")
        result = test_endpoint("/", token)
        print(f"   Status: {result['status_code']} - {'✅ Success' if result['success'] else '❌ Failed'}")
        
        # Test 2: Churn Prediction (should work for staff and admin only)
        print("\n🔮 Testing churn prediction endpoint...")
        with open(test_file, 'rb') as f:
            files = {'file': f}
            data = {
                'model_version': '1',
                'scaler_version': 'scaler/scaler_churn_version_20250705T125012.pkl',
                'run_id': 'e26506b0b99247c6bcec84a630fa665e'
            }
            result = test_endpoint("/churn_prediction/", token, "POST", files=files, data=data)
        
        expected_success = actual_role in ['staff', 'admin']
        status_icon = "✅" if result['success'] == expected_success else "❌"
        print(f"   Status: {result['status_code']} - {status_icon} {'Success' if result['success'] else 'Failed'}")
        
        if result['status_code'] == 403:
            print(f"   Expected 403 for {actual_role} role: ✅")
        elif result['success'] and expected_success:
            print(f"   Prediction successful for {actual_role}: ✅")
        
        # Test 3: Churn Training (should work for admin only)
        print("\n🏋️ Testing churn training endpoint...")
        with open(test_file, 'rb') as f:
            files = {'file': f}
            result = test_endpoint("/churn_training/", token, "POST", files=files)
        
        expected_success = actual_role == 'admin'
        status_icon = "✅" if result['success'] == expected_success else "❌"
        print(f"   Status: {result['status_code']} - {status_icon} {'Success' if result['success'] else 'Failed'}")
        
        if result['status_code'] == 403:
            print(f"   Expected 403 for {actual_role} role: ✅")
        elif result['success'] and expected_success:
            print(f"   Training successful for {actual_role}: ✅")
    
    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)
    
    print("\n" + "=" * 60)
    print("🎯 Test Summary:")
    print("   - Users should NOT access prediction or training APIs")
    print("   - Staff should access prediction APIs but NOT training APIs")
    print("   - Admin should access BOTH prediction and training APIs")
    print("=" * 60)

if __name__ == "__main__":
    main()
