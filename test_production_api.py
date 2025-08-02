#!/usr/bin/env python3
"""
Comprehensive test suite for the production-ready Store Management API.
"""

import requests
import json
import os
import time
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

class APITester:
    def __init__(self, base_url: str = "http://localhost:5002", token: str = None):
        self.base_url = base_url
        self.token = token or os.getenv("SECRET_TOKEN", "mamad")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.test_store_id = "test-production-store"
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages."""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def test_health_check(self) -> bool:
        """Test the health check endpoint."""
        self.log("Testing health check endpoint...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Health check passed: {data['status']}")
                return True
            else:
                self.log(f"❌ Health check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Health check error: {e}", "ERROR")
            return False
    
    def test_api_documentation(self) -> bool:
        """Test API documentation endpoints."""
        self.log("Testing API documentation...")
        try:
            # Test OpenAPI docs
            docs_response = requests.get(f"{self.base_url}/docs", timeout=5)
            redoc_response = requests.get(f"{self.base_url}/redoc", timeout=5)
            openapi_response = requests.get(f"{self.base_url}/openapi.json", timeout=5)
            
            if all(r.status_code == 200 for r in [docs_response, redoc_response, openapi_response]):
                self.log("✅ API documentation is accessible")
                return True
            else:
                self.log("❌ API documentation not accessible", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Documentation test error: {e}", "ERROR")
            return False
    
    def test_authentication(self) -> bool:
        """Test authentication mechanisms."""
        self.log("Testing authentication...")
        
        # Test without token
        try:
            response = requests.get(f"{self.base_url}/api/v1/stores/test/json", timeout=5)
            if response.status_code == 401:
                self.log("✅ Unauthorized access properly rejected")
            else:
                self.log(f"❌ Expected 401, got {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Auth test error: {e}", "ERROR")
            return False
        
        # Test with invalid token
        try:
            invalid_headers = {"Authorization": "Bearer invalid-token"}
            response = requests.get(
                f"{self.base_url}/api/v1/stores/test/json", 
                headers=invalid_headers, 
                timeout=5
            )
            if response.status_code == 401:
                self.log("✅ Invalid token properly rejected")
                return True
            else:
                self.log(f"❌ Expected 401 for invalid token, got {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Invalid token test error: {e}", "ERROR")
            return False
    
    def test_store_operations(self) -> bool:
        """Test store-related operations."""
        self.log("Testing store operations...")
        
        # Test store initialization
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/stores/{self.test_store_id}/initialize",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log(f"✅ Store initialization: {data['message']}")
                return True
            else:
                self.log(f"❌ Store initialization failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Store operation error: {e}", "ERROR")
            return False
    
    def test_json_operations(self) -> bool:
        """Test JSON file operations."""
        self.log("Testing JSON file operations...")
        
        try:
            # List JSON files
            response = requests.get(
                f"{self.base_url}/api/v1/stores/{self.test_store_id}/json",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                json_files = data.get('json_files', [])
                self.log(f"✅ Found {len(json_files)} JSON files")
                
                # Test getting a specific file if available
                if json_files:
                    test_file = json_files[0]
                    response = requests.get(
                        f"{self.base_url}/api/v1/stores/{self.test_store_id}/json/{test_file}",
                        headers=self.headers,
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        self.log(f"✅ Successfully retrieved {test_file}")
                        return True
                    else:
                        self.log(f"❌ Failed to retrieve {test_file}: {response.status_code}", "ERROR")
                        return False
                else:
                    self.log("✅ JSON listing works (no files found)")
                    return True
            else:
                self.log(f"❌ JSON listing failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ JSON operations error: {e}", "ERROR")
            return False
    
    def test_image_operations(self) -> bool:
        """Test image operations."""
        self.log("Testing image operations...")
        
        try:
            # List images
            response = requests.get(
                f"{self.base_url}/api/v1/stores/{self.test_store_id}/images",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                images = data.get('images', [])
                self.log(f"✅ Image listing works - found {len(images)} images")
                return True
            else:
                self.log(f"❌ Image listing failed: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Image operations error: {e}", "ERROR")
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling."""
        self.log("Testing error handling...")
        
        try:
            # Test 404 for non-existent store
            response = requests.get(
                f"{self.base_url}/api/v1/stores/non-existent-store/json",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 404:
                self.log("✅ 404 error properly handled")
                return True
            else:
                self.log(f"❌ Expected 404, got {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error handling test error: {e}", "ERROR")
            return False
    
    def test_validation(self) -> bool:
        """Test input validation."""
        self.log("Testing input validation...")
        
        try:
            # Test invalid store ID
            response = requests.post(
                f"{self.base_url}/api/v1/stores/invalid@store!/initialize",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 422:  # Validation error
                self.log("✅ Input validation works")
                return True
            else:
                self.log(f"❌ Expected 422 for invalid input, got {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Validation test error: {e}", "ERROR")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results."""
        self.log("🚀 Starting comprehensive API tests...")
        self.log(f"Base URL: {self.base_url}")
        self.log(f"Test Store ID: {self.test_store_id}")
        self.log("-" * 60)
        
        tests = {
            "Health Check": self.test_health_check,
            "API Documentation": self.test_api_documentation,
            "Authentication": self.test_authentication,
            "Store Operations": self.test_store_operations,
            "JSON Operations": self.test_json_operations,
            "Image Operations": self.test_image_operations,
            "Error Handling": self.test_error_handling,
            "Input Validation": self.test_validation,
        }
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests.items():
            self.log(f"\n📋 Running: {test_name}")
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    passed += 1
            except Exception as e:
                self.log(f"❌ Test {test_name} crashed: {e}", "ERROR")
                results[test_name] = False
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("📊 TEST SUMMARY")
        self.log("=" * 60)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name}: {status}")
        
        self.log(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 All tests passed! API is production-ready.")
        else:
            self.log(f"⚠️  {total - passed} tests failed. Please review and fix issues.")
        
        return results

def main():
    """Main test runner."""
    tester = APITester()
    results = tester.run_all_tests()
    
    # Exit with error code if any tests failed
    if not all(results.values()):
        exit(1)

if __name__ == "__main__":
    main()