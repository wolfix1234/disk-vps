#!/usr/bin/env python3
"""
Test script to verify authentication and API functionality
"""
import requests
import json

# Configuration
BASE_URL = "http://localhost:5002"
API_TOKEN = "mamad"  # From .env file

def test_health_endpoint():
    """Test the health endpoint (should work without auth)"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_without_auth():
    """Test API endpoint without authentication (should fail)"""
    print("🔍 Testing API without authentication...")
    response = requests.post(f"{BASE_URL}/api/v1/stores/test-store/initialize")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_with_auth():
    """Test API endpoint with authentication (should work)"""
    print("🔍 Testing API with authentication...")
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(f"{BASE_URL}/api/v1/stores/test-store-auth/initialize", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_openapi_schema():
    """Test OpenAPI schema generation"""
    print("🔍 Testing OpenAPI schema...")
    response = requests.get(f"{BASE_URL}/openapi.json")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        schema = response.json()
        # Check if security schemes are defined
        if "components" in schema and "securitySchemes" in schema["components"]:
            print("✅ Security schemes found in OpenAPI schema")
            print(f"Security schemes: {list(schema['components']['securitySchemes'].keys())}")
        else:
            print("❌ No security schemes found in OpenAPI schema")
        
        # Check if paths have security requirements
        if "paths" in schema:
            sample_path = list(schema["paths"].keys())[0] if schema["paths"] else None
            if sample_path:
                sample_method = list(schema["paths"][sample_path].keys())[0]
                if "security" in schema["paths"][sample_path][sample_method]:
                    print("✅ Security requirements found on endpoints")
                else:
                    print("❌ No security requirements found on endpoints")
    print()

def main():
    print("🚀 Starting API Authentication Tests")
    print("=" * 50)
    
    try:
        test_health_endpoint()
        test_without_auth()
        test_with_auth()
        test_openapi_schema()
        
        print("✅ All tests completed!")
        print("\n📝 Instructions for Swagger UI:")
        print("1. Go to http://localhost:5002/docs")
        print("2. Click the 'Authorize' button (lock icon)")
        print("3. Enter 'mamad' in the Value field")
        print("4. Click 'Authorize'")
        print("5. Now you can test endpoints with authentication!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API. Make sure the server is running:")
        print("   python run.py")

if __name__ == "__main__":
    main()