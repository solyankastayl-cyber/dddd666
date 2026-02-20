#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date
from typing import Dict, List, Any

class FractalIntelTimelineTest:
    """BLOCK 82 — Intel Timeline API Test Suite"""
    
    def __init__(self, base_url="https://fractal-dev-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data=None, query_params=None) -> tuple[bool, dict]:
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if query_params:
            params = '&'.join([f"{k}={v}" for k, v in query_params.items()])
            url += f"?{params}"
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                response = requests.request(method, url, json=data, headers=headers, timeout=10)
            
            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and 'ok' in response_data:
                        print(f"   Response: {response_data.get('ok')} - {response_data.get('message', '')}")
                except:
                    pass
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}...")
            
            self.test_results.append({
                'name': name,
                'success': success,
                'status_code': response.status_code,
                'expected_status': expected_status,
                'url': url
            })
            
            return success, response.json() if response.text else {}
            
        except Exception as e:
            print(f"❌ FAILED - Exception: {str(e)}")
            self.test_results.append({
                'name': name,
                'success': False,
                'error': str(e),
                'url': url
            })
            return False, {}
    
    def test_intel_timeline_endpoints(self):
        """Test all BLOCK 82 Intel Timeline endpoints"""
        
        print("=" * 60)
        print("🧪 BLOCK 82 — Intel Timeline API Tests")
        print("=" * 60)
        
        # Test 1: GET /api/fractal/v2.1/admin/intel/counts
        print("\n📊 Testing counts endpoint...")
        success, counts_data = self.run_test(
            "Intel Timeline Counts",
            "GET",
            "api/fractal/v2.1/admin/intel/counts",
            200,
            query_params={"symbol": "BTC"}
        )
        
        if success and counts_data:
            counts = counts_data.get('counts', {})
            print(f"   📈 LIVE: {counts.get('LIVE', 0)}")
            print(f"   📈 V2020: {counts.get('V2020', 0)}")  
            print(f"   📈 V2014: {counts.get('V2014', 0)}")
            print(f"   📈 Total: {counts_data.get('total', 0)}")
        
        # Test 2: GET /api/fractal/v2.1/admin/intel/timeline (LIVE source, 30d window)
        print("\n📈 Testing timeline endpoint (LIVE, 30d)...")
        success, timeline_data = self.run_test(
            "Intel Timeline (LIVE, 30d)",
            "GET",
            "api/fractal/v2.1/admin/intel/timeline",
            200,
            query_params={"symbol": "BTC", "source": "LIVE", "window": "30"}
        )
        
        if success and timeline_data:
            series = timeline_data.get('series', [])
            stats = timeline_data.get('stats', {})
            meta = timeline_data.get('meta', {})
            print(f"   📊 Series length: {len(series)}")
            print(f"   📊 Window: {meta.get('window')}d ({meta.get('from')} to {meta.get('to')})")
            if stats:
                print(f"   📊 Lock days: {stats.get('lockDays', 0)}")
                print(f"   📊 Structure dominance: {stats.get('structureDominancePct', 0)}%")
                print(f"   📊 Avg phase score: {stats.get('avgPhaseScore', 0)}")
                print(f"   📊 7d trend: {stats.get('trend7d', 'FLAT')}")
        
        # Test 3: GET /api/fractal/v2.1/admin/intel/timeline (V2020 source, 90d window) 
        print("\n📈 Testing timeline endpoint (V2020, 90d)...")
        success, timeline_v2020 = self.run_test(
            "Intel Timeline (V2020, 90d)",
            "GET",
            "api/fractal/v2.1/admin/intel/timeline",
            200,
            query_params={"symbol": "BTC", "source": "V2020", "window": "90"}
        )
        
        if success and timeline_v2020:
            series = timeline_v2020.get('series', [])
            stats = timeline_v2020.get('stats', {})
            print(f"   📊 V2020 series length: {len(series)}")
            if stats:
                print(f"   📊 V2020 lock days: {stats.get('lockDays', 0)}")
                print(f"   📊 V2020 structure dominance: {stats.get('structureDominancePct', 0)}%")
        
        # Test 4: GET /api/fractal/v2.1/admin/intel/timeline (V2014 source, 180d window)
        print("\n📈 Testing timeline endpoint (V2014, 180d)...")
        success, timeline_v2014 = self.run_test(
            "Intel Timeline (V2014, 180d)",
            "GET",
            "api/fractal/v2.1/admin/intel/timeline",
            200,
            query_params={"symbol": "BTC", "source": "V2014", "window": "180"}
        )
        
        if success and timeline_v2014:
            series = timeline_v2014.get('series', [])
            stats = timeline_v2014.get('stats', {})
            print(f"   📊 V2014 series length: {len(series)}")
            if stats:
                print(f"   📊 V2014 lock days: {stats.get('lockDays', 0)}")
                print(f"   📊 V2014 tactical dominance: {stats.get('tacticalDominancePct', 0)}%")
        
        # Test 5: GET /api/fractal/v2.1/admin/intel/latest (LIVE source)
        print("\n📈 Testing latest endpoint (LIVE)...")
        success, latest_live = self.run_test(
            "Intel Latest (LIVE)",
            "GET",
            "api/fractal/v2.1/admin/intel/latest",
            200,
            query_params={"symbol": "BTC", "source": "LIVE"}
        )
        
        if success and latest_live:
            latest = latest_live.get('latest')
            if latest:
                print(f"   📊 Latest LIVE date: {latest.get('date')}")
                print(f"   📊 Phase: {latest.get('phaseType')} ({latest.get('phaseGrade')})")
                print(f"   📊 Dominance: {latest.get('dominanceTier')}")
                print(f"   📊 Structural lock: {latest.get('structuralLock')}")
            else:
                print(f"   📊 No LIVE data available")
        
        # Test 6: GET /api/fractal/v2.1/admin/intel/latest (V2020 source)
        print("\n📈 Testing latest endpoint (V2020)...")
        success, latest_v2020 = self.run_test(
            "Intel Latest (V2020)",
            "GET",
            "api/fractal/v2.1/admin/intel/latest",
            200,
            query_params={"symbol": "BTC", "source": "V2020"}
        )
        
        if success and latest_v2020:
            latest = latest_v2020.get('latest')
            if latest:
                print(f"   📊 Latest V2020 date: {latest.get('date')}")
                print(f"   📊 Phase: {latest.get('phaseType')} ({latest.get('phaseGrade')})")
                print(f"   📊 Phase score: {latest.get('phaseScore')}")
        
        # Test 7: POST /api/fractal/v2.1/admin/intel/backfill (Test backfill functionality)
        # This should work if the cohort data doesn't exist yet or is small
        print("\n📈 Testing backfill endpoint (small range)...")
        backfill_payload = {
            "cohort": "V2020",
            "from": "2020-01-01",
            "to": "2020-01-05"  # Small range for testing
        }
        success, backfill_result = self.run_test(
            "Intel Backfill (small range)",
            "POST", 
            "api/fractal/v2.1/admin/intel/backfill",
            200,
            data=backfill_payload
        )
        
        if success and backfill_result:
            print(f"   📊 Backfill cohort: {backfill_result.get('cohort')}")
            print(f"   📊 Written: {backfill_result.get('written', 0)}")
            print(f"   📊 Skipped: {backfill_result.get('skipped', 0)}")
        
        # Test 8: Test different window sizes
        print("\n📈 Testing different window sizes...")
        for window in [30, 90, 180, 365]:
            success, _ = self.run_test(
                f"Intel Timeline (LIVE, {window}d)",
                "GET",
                "api/fractal/v2.1/admin/intel/timeline", 
                200,
                query_params={"symbol": "BTC", "source": "LIVE", "window": str(window)}
            )
    
    def test_error_cases(self):
        """Test error handling"""
        print("\n🚨 Testing error cases...")
        
        # Invalid source
        self.run_test(
            "Invalid source",
            "GET",
            "api/fractal/v2.1/admin/intel/timeline",
            200,  # Should still return 200 but empty data
            query_params={"symbol": "BTC", "source": "INVALID", "window": "30"}
        )
        
        # Invalid symbol
        self.run_test(
            "Invalid symbol",
            "GET", 
            "api/fractal/v2.1/admin/intel/timeline",
            200,  # Should still return 200 but empty data
            query_params={"symbol": "INVALID", "source": "LIVE", "window": "30"}
        )
        
        # Invalid backfill data
        self.run_test(
            "Invalid backfill (missing fields)",
            "POST",
            "api/fractal/v2.1/admin/intel/backfill",
            200,  # API should return error message with ok: false
            data={"cohort": "V2020"}  # Missing from/to
        )
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 BLOCK 82 — Intel Timeline Test Summary")
        print("=" * 60)
        print(f"Total tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        # Print failed tests
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print(f"\n❌ Failed tests ({len(failed_tests)}):")
            for test in failed_tests:
                error_msg = test.get('error', f"HTTP {test.get('status_code')}")
                print(f"   • {test['name']}: {error_msg}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test runner"""
    tester = FractalIntelTimelineTest()
    
    try:
        # Test core Intel Timeline endpoints
        tester.test_intel_timeline_endpoints()
        
        # Test error cases
        tester.test_error_cases()
        
        # Print summary
        all_passed = tester.print_summary()
        
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"💥 Fatal test error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())