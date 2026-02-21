#!/usr/bin/env python3
"""
SPX Data Foundation Testing (BLOCK B1-B4)
Tests all SPX backend APIs for data foundation implementation
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class SPXDataFoundationTester:
    def __init__(self, base_url="https://fractal-sync-deploy.preview.emergentagent.com"):
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

    def test_spx_info(self):
        """Test GET /api/spx/v2.1/info - SPX product info"""
        success, data, error = self.make_request('GET', 'api/spx/v2.1/info')
        
        if success and data:
            expected_fields = ['product', 'version', 'symbol', 'status', 'description', 'data']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                if data.get('symbol') == 'SPX' and data.get('product') == 'SPX Terminal':
                    self.log_test("SPX Info API", True, data)
                    return data
                else:
                    self.log_test("SPX Info API", False, data, f"Unexpected product/symbol: {data.get('product')}/{data.get('symbol')}")
            else:
                self.log_test("SPX Info API", False, data, "Missing expected fields")
        else:
            self.log_test("SPX Info API", False, data, error)
        
        return None

    def test_spx_stats(self):
        """Test GET /api/spx/v2.1/stats - should return count ~19828 and cohorts"""
        success, data, error = self.make_request('GET', 'api/spx/v2.1/stats')
        
        if success and data:
            expected_fields = ['ok', 'count', 'cohorts']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                count = data.get('count', 0)
                cohorts = data.get('cohorts', {})
                
                # Check if count is around expected 19,828
                if count >= 19000:  # Allow some variance
                    expected_cohorts = ['V1950', 'V1990', 'V2008', 'V2020', 'LIVE']
                    has_cohorts = any(cohort in cohorts for cohort in expected_cohorts)
                    
                    if has_cohorts:
                        self.log_test("SPX Stats API", True, data, f"Count: {count}, Cohorts: {list(cohorts.keys())}")
                        return data
                    else:
                        self.log_test("SPX Stats API", False, data, f"Missing expected cohorts. Found: {list(cohorts.keys())}")
                else:
                    self.log_test("SPX Stats API", False, data, f"Expected count ~19828, got {count}")
            else:
                self.log_test("SPX Stats API", False, data, "Missing expected fields")
        else:
            self.log_test("SPX Stats API", False, data, error)
        
        return None

    def test_spx_validate(self):
        """Test GET /api/fractal/v2.1/admin/spx/validate - should return ok=true"""
        success, data, error = self.make_request('GET', 'api/fractal/v2.1/admin/spx/validate')
        
        if success and data:
            if data.get('ok') is True:
                expected_fields = ['cohort', 'count', 'badOHLC', 'outliers', 'issues']
                has_fields = all(field in data for field in expected_fields)
                
                if has_fields:
                    issues = data.get('issues', [])
                    if len(issues) == 0:
                        self.log_test("SPX Validation API", True, data)
                        return data
                    else:
                        self.log_test("SPX Validation API", True, data, f"Validation passed but has {len(issues)} issues")
                        return data
                else:
                    self.log_test("SPX Validation API", False, data, "Missing expected validation fields")
            else:
                self.log_test("SPX Validation API", False, data, f"Validation failed: {data}")
        else:
            self.log_test("SPX Validation API", False, data, error)
        
        return None

    def test_spx_cohorts(self):
        """Test GET /api/fractal/v2.1/admin/spx/cohorts - should return cohort breakdown"""
        success, data, error = self.make_request('GET', 'api/fractal/v2.1/admin/spx/cohorts')
        
        if success and data:
            if data.get('ok') is True and 'cohorts' in data:
                cohorts = data.get('cohorts', {})
                expected_cohorts = ['V1950', 'V1990', 'V2008', 'V2020', 'LIVE']
                
                # Check for expected cohorts
                found_cohorts = [c for c in expected_cohorts if c in cohorts]
                
                if len(found_cohorts) >= 3:  # Allow some variance
                    total = sum(cohorts.values())
                    self.log_test("SPX Cohorts API", True, data, f"Total: {total}, Cohorts: {found_cohorts}")
                    return data
                else:
                    self.log_test("SPX Cohorts API", False, data, f"Expected cohorts not found. Found: {list(cohorts.keys())}")
            else:
                self.log_test("SPX Cohorts API", False, data, "Missing ok=true or cohorts field")
        else:
            self.log_test("SPX Cohorts API", False, data, error)
        
        return None

    def test_market_data_candles(self):
        """Test GET /api/market-data/candles?symbol=SPX&source=stooq&tf=1d&limit=10"""
        params = {
            'symbol': 'SPX',
            'source': 'stooq', 
            'tf': '1d',
            'limit': '10'
        }
        
        success, data, error = self.make_request('GET', 'api/market-data/candles', params=params)
        
        if success and data:
            expected_fields = ['ok', 'symbol', 'source', 'tf', 'count', 'candles']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields and data.get('ok') is True:
                candles = data.get('candles', [])
                count = data.get('count', 0)
                
                if len(candles) == count and count <= 10:
                    # Check candle structure
                    if len(candles) > 0:
                        candle = candles[0]
                        candle_fields = ['ts', 'date', 'o', 'h', 'l', 'c', 'cohort']
                        has_candle_fields = all(field in candle for field in candle_fields)
                        
                        if has_candle_fields:
                            self.log_test("Market Data Candles API", True, data, f"Got {count} candles")
                            return data
                        else:
                            self.log_test("Market Data Candles API", False, data, f"Missing candle fields. Found: {list(candle.keys())}")
                    else:
                        self.log_test("Market Data Candles API", False, data, "No candles returned when expected")
                        return None
                else:
                    self.log_test("Market Data Candles API", False, data, f"Count mismatch: candles={len(candles)}, count={count}")
            else:
                self.log_test("Market Data Candles API", False, data, "Missing expected fields or ok=false")
        else:
            self.log_test("Market Data Candles API", False, data, error)
        
        return None

    def test_spx_status(self):
        """Test GET /api/spx/v2.1/status - SPX build status"""
        success, data, error = self.make_request('GET', 'api/spx/v2.1/status')
        
        if success and data:
            expected_fields = ['ok', 'product', 'status', 'progress', 'data']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields and data.get('ok') is True:
                progress = data.get('progress', {})
                progress_fields = ['config', 'routes', 'dataAdapter', 'backfill', 'cohorts']
                has_progress = all(field in progress for field in progress_fields)
                
                if has_progress:
                    self.log_test("SPX Status API", True, data)
                    return data
                else:
                    self.log_test("SPX Status API", False, data, "Missing progress fields")
            else:
                self.log_test("SPX Status API", False, data, "Missing expected fields or ok=false")
        else:
            self.log_test("SPX Status API", False, data, error)
        
        return None

    def test_spx_terminal(self):
        """Test GET /api/spx/v2.1/terminal - SPX terminal endpoint"""
        success, data, error = self.make_request('GET', 'api/spx/v2.1/terminal')
        
        if success and data:
            expected_fields = ['ok', 'status', 'message', 'symbol', 'data']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                if data.get('symbol') == 'SPX':
                    data_field = data.get('data', {})
                    data_fields = ['count', 'cohorts']
                    has_data_fields = all(field in data_field for field in data_fields)
                    
                    if has_data_fields:
                        self.log_test("SPX Terminal API", True, data)
                        return data
                    else:
                        self.log_test("SPX Terminal API", False, data, "Missing data fields")
                else:
                    self.log_test("SPX Terminal API", False, data, f"Expected symbol=SPX, got {data.get('symbol')}")
            else:
                self.log_test("SPX Terminal API", False, data, "Missing expected fields")
        else:
            self.log_test("SPX Terminal API", False, data, error)
        
        return None

    def run_all_tests(self):
        """Run all SPX Data Foundation tests"""
        print(f"🚀 Starting SPX Data Foundation Tests (BLOCK B1-B4)")
        print(f"📡 Backend URL: {self.base_url}")
        print("=" * 80)
        
        # Core SPX APIs
        print("\n🏗️ SPX Core APIs")
        self.test_spx_info()
        self.test_spx_stats()  # Should return ~19828 count and cohorts
        self.test_spx_status()
        self.test_spx_terminal()
        
        # Admin APIs
        print("\n🔧 SPX Admin APIs")
        self.test_spx_validate()  # Should return ok=true
        self.test_spx_cohorts()   # Should return cohort breakdown
        
        # Market Data API
        print("\n📊 Market Data API")
        self.test_market_data_candles()  # Should return candles
        
        # Summary
        print("\n" + "=" * 80)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All SPX Data Foundation tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    """Main test runner"""
    tester = SPXDataFoundationTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())