#!/usr/bin/env python3
"""
BLOCK A - BTC Final Isolation Testing
Tests the specific APIs for BTC/SPX/Combined terminal isolation implementation.
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class BlockAIsolationTester:
    def __init__(self, base_url="https://spx-core-engine.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []

    def log_test(self, name: str, success: bool, response_data: Any = None, error: str = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {error}")
        
        self.results.append({
            "test": name,
            "success": success,
            "response": response_data,
            "error": error
        })

    def make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> tuple[bool, Any, str]:
        """Make HTTP request and return (success, response_data, error_message)"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, timeout=30)
            elif method == 'POST':
                if data is not None:
                    headers = {'Content-Type': 'application/json'}
                    response = requests.post(url, params=params, json=data, headers=headers, timeout=30)
                else:
                    response = requests.post(url, params=params, timeout=30)
            else:
                return False, None, f"Unsupported method: {method}"

            if response.status_code == 200:
                try:
                    return True, response.json(), None
                except json.JSONDecodeError:
                    return True, response.text, None
            else:
                return False, None, f"HTTP {response.status_code}: {response.text[:200]}"

        except requests.exceptions.Timeout:
            return False, None, "Request timeout (30s)"
        except requests.exceptions.ConnectionError:
            return False, None, "Connection error"
        except Exception as e:
            return False, None, f"Request error: {str(e)}"

    def test_btc_info(self):
        """Test GET /api/btc/v2.1/info - should return BTC Terminal info"""
        success, data, error = self.make_request('GET', 'api/btc/v2.1/info')
        
        if success and data:
            expected_fields = ['product', 'version', 'symbol', 'frozen', 'horizons', 'governance', 'status', 'description']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                # Verify BTC specific values
                if (data.get('product') == 'BTC Terminal' and 
                    data.get('symbol') == 'BTC' and 
                    data.get('status') == 'FINAL' and 
                    data.get('frozen') == True):
                    self.log_test("BTC Terminal Info", True, data)
                    return data
                else:
                    self.log_test("BTC Terminal Info", False, data, f"Invalid BTC info values: product={data.get('product')}, symbol={data.get('symbol')}, status={data.get('status')}, frozen={data.get('frozen')}")
            else:
                self.log_test("BTC Terminal Info", False, data, "Missing expected fields in BTC info response")
        else:
            self.log_test("BTC Terminal Info", False, data, error)
        
        return None

    def test_spx_status(self):
        """Test GET /api/spx/v2.1/status - should return SPX status BUILDING"""
        success, data, error = self.make_request('GET', 'api/spx/v2.1/status')
        
        if success and data:
            expected_fields = ['ok', 'product', 'status', 'progress', 'nextStep']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                if (data.get('ok') == True and 
                    data.get('product') == 'SPX Terminal' and 
                    data.get('status') == 'BUILDING'):
                    self.log_test("SPX Terminal Status", True, data)
                    return data
                else:
                    self.log_test("SPX Terminal Status", False, data, f"Invalid SPX status values: ok={data.get('ok')}, product={data.get('product')}, status={data.get('status')}")
            else:
                self.log_test("SPX Terminal Status", False, data, "Missing expected fields in SPX status response")
        else:
            self.log_test("SPX Terminal Status", False, data, error)
        
        return None

    def test_combined_info(self):
        """Test GET /api/combined/v2.1/info - should return Combined info"""
        success, data, error = self.make_request('GET', 'api/combined/v2.1/info')
        
        if success and data:
            expected_fields = ['product', 'version', 'status', 'primaryAsset', 'macroAsset', 'layers', 'defaultProfile', 'spxInfluence', 'safety', 'description']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                if (data.get('primaryAsset') == 'BTC' and 
                    data.get('macroAsset') == 'SPX' and 
                    data.get('status') == 'BUILDING'):
                    self.log_test("Combined Terminal Info", True, data)
                    return data
                else:
                    self.log_test("Combined Terminal Info", False, data, f"Invalid Combined info values: primaryAsset={data.get('primaryAsset')}, macroAsset={data.get('macroAsset')}, status={data.get('status')}")
            else:
                self.log_test("Combined Terminal Info", False, data, "Missing expected fields in Combined info response")
        else:
            self.log_test("Combined Terminal Info", False, data, error)
        
        return None

    def test_fractal_admin_overview(self):
        """Test GET /api/fractal/v2.1/admin/overview?symbol=BTC - should return admin data"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/overview',
            params={'symbol': 'BTC'}
        )
        
        if success and data:
            expected_fields = ['governance', 'health', 'guard', 'model', 'performance', 'recommendation', 'recent']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                # Verify governance structure
                governance = data.get('governance', {})
                if 'mode' in governance and 'protectionMode' in governance:
                    self.log_test("Fractal Admin Overview", True, data)
                    return data
                else:
                    self.log_test("Fractal Admin Overview", False, data, "Missing governance mode/protectionMode fields")
            else:
                self.log_test("Fractal Admin Overview", False, data, "Missing expected fields in admin overview response")
        else:
            self.log_test("Fractal Admin Overview", False, data, error)
        
        return None

    def test_health_endpoint(self):
        """Test GET /api/health - basic health check"""
        success, data, error = self.make_request('GET', 'api/health')
        
        if success and data:
            if data.get('ok') == True and data.get('mode') == 'FRACTAL_ONLY':
                self.log_test("Health Check", True, data)
                return data
            else:
                self.log_test("Health Check", False, data, f"Invalid health response: ok={data.get('ok')}, mode={data.get('mode')}")
        else:
            self.log_test("Health Check", False, data, error)
        
        return None

    def run_all_tests(self):
        """Run all BLOCK A isolation tests"""
        print(f"🚀 Starting BLOCK A - BTC Final Isolation Tests")
        print(f"📡 Backend URL: {self.base_url}")
        print("=" * 80)
        
        # Basic health check first
        print("\n🏥 Basic Health Check")
        self.test_health_endpoint()
        
        # Test BLOCK A specific endpoints
        print("\n🟠 BTC Terminal (FINAL)")
        self.test_btc_info()
        
        print("\n🔵 SPX Terminal (BUILDING)")
        self.test_spx_status()
        
        print("\n🟣 Combined Terminal (BUILDING)")
        self.test_combined_info()
        
        print("\n⚙️ Fractal Admin Overview")
        self.test_fractal_admin_overview()
        
        # Summary
        print("\n" + "=" * 80)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All BLOCK A isolation tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    """Main test runner"""
    tester = BlockAIsolationTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())