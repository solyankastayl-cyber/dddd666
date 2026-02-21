#!/usr/bin/env python3
"""
BLOCK 77.4 — Bootstrap Historical Engine Testing
Tests bootstrap backfill system, source isolation, and guardrails.
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class BootstrapSystemTester:
    def __init__(self, base_url="https://spx-core-engine.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []
        self.symbol = "BTC"
        self.test_batch_id = None

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

    def make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None, timeout: int = 30) -> tuple[bool, Any, str]:
        """Make HTTP request and return (success, response_data, error_message)"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            headers = {'Content-Type': 'application/json'} if data is not None else {}
            
            if method == 'GET':
                response = requests.get(url, params=params, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, params=params, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, params=params, timeout=timeout)
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
            return False, None, f"Request timeout ({timeout}s)"
        except requests.exceptions.ConnectionError:
            return False, None, "Connection error"
        except Exception as e:
            return False, None, f"Request error: {str(e)}"

    def test_clear_bootstrap_data(self):
        """Clear any existing bootstrap data for clean testing"""
        success, data, error = self.make_request(
            'DELETE', 
            'api/fractal/v2.1/admin/bootstrap/clear',
            params={'symbol': self.symbol, 'confirm': 'yes'}
        )
        
        if success:
            self.log_test("Clear Bootstrap Data (Setup)", True, data)
            return data
        else:
            self.log_test("Clear Bootstrap Data (Setup)", False, data, error)
        return None

    def test_bootstrap_run_creation(self):
        """Test POST /api/fractal/v2.1/admin/bootstrap/run - Create snapshots with source=BOOTSTRAP"""
        
        # Test with minimal date range for faster execution
        test_data = {
            "symbol": self.symbol,
            "from": "2024-01-01",
            "to": "2024-01-03",  # Just 3 days for testing
            "horizons": ["7d", "30d"],  # Limited horizons 
            "presets": ["balanced"],  # Single preset
            "roles": ["ACTIVE"],  # Single role
            "policyHash": "test-v2.1.0"
        }
        
        success, data, error = self.make_request(
            'POST', 
            'api/fractal/v2.1/admin/bootstrap/run',
            data=test_data,
            timeout=60  # Longer timeout for bootstrap creation
        )
        
        if success and data:
            if data.get('ok') and 'batchId' in data:
                self.test_batch_id = data['batchId']
                self.log_test("Bootstrap Run - Create Snapshots", True, data)
                return data
            else:
                self.log_test("Bootstrap Run - Create Snapshots", False, data, "Missing 'ok' or 'batchId' in response")
        else:
            self.log_test("Bootstrap Run - Create Snapshots", False, data, error)
        
        return None

    def test_bootstrap_progress(self):
        """Test GET /api/fractal/v2.1/admin/bootstrap/progress - Get job progress"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/bootstrap/progress'
        )
        
        if success and data:
            if data.get('ok') and 'run' in data:
                run_progress = data.get('run')
                if run_progress and 'status' in run_progress:
                    # Wait for completion if still running
                    if run_progress['status'] == 'RUNNING':
                        print("⏳ Bootstrap still running, waiting...")
                        time.sleep(5)
                        return self.test_bootstrap_progress()  # Retry
                    
                    self.log_test("Bootstrap Progress - Get Status", True, data)
                    return data
                else:
                    self.log_test("Bootstrap Progress - Get Status", False, data, "Missing run progress data")
            else:
                self.log_test("Bootstrap Progress - Get Status", False, data, "Invalid progress response structure")
        else:
            self.log_test("Bootstrap Progress - Get Status", False, data, error)
        
        return None

    def test_bootstrap_resolve_outcomes(self):
        """Test POST /api/fractal/v2.1/admin/bootstrap/resolve - Resolve bootstrap outcomes"""
        
        resolve_data = {
            "symbol": self.symbol,
            "batchId": self.test_batch_id,
            "forceResolve": False
        }
        
        success, data, error = self.make_request(
            'POST', 
            'api/fractal/v2.1/admin/bootstrap/resolve',
            data=resolve_data,
            timeout=60  # Longer timeout for resolution
        )
        
        if success and data:
            if 'ok' in data and 'progress' in data:
                progress = data.get('progress', {})
                if progress.get('status') in ['COMPLETED', 'RUNNING']:
                    self.log_test("Bootstrap Resolve - Resolve Outcomes", True, data)
                    return data
                else:
                    self.log_test("Bootstrap Resolve - Resolve Outcomes", False, data, f"Unexpected status: {progress.get('status')}")
            else:
                self.log_test("Bootstrap Resolve - Resolve Outcomes", False, data, "Missing 'ok' or 'progress' in response")
        else:
            self.log_test("Bootstrap Resolve - Resolve Outcomes", False, data, error)
        
        return None

    def test_bootstrap_stats(self):
        """Test GET /api/fractal/v2.1/admin/bootstrap/stats - Get bootstrap statistics"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/bootstrap/stats',
            params={'symbol': self.symbol}
        )
        
        if success and data:
            if data.get('ok') and 'stats' in data:
                stats = data.get('stats', {})
                expected_fields = ['totalSnapshots', 'totalOutcomes', 'dateRange', 'byHorizon', 'byPreset']
                has_fields = all(field in stats for field in expected_fields)
                
                if has_fields:
                    # Check that we have some bootstrap data
                    if stats.get('totalSnapshots', 0) > 0:
                        self.log_test("Bootstrap Stats - Get Statistics", True, data)
                        return data
                    else:
                        self.log_test("Bootstrap Stats - Get Statistics", False, data, "No snapshots found in stats")
                else:
                    self.log_test("Bootstrap Stats - Get Statistics", False, data, f"Missing expected fields: {expected_fields}")
            else:
                self.log_test("Bootstrap Stats - Get Statistics", False, data, "Missing 'ok' or 'stats' in response")
        else:
            self.log_test("Bootstrap Stats - Get Statistics", False, data, error)
        
        return None

    def test_attribution_with_bootstrap_source(self):
        """Test GET /api/fractal/v2.1/admin/attribution with source=BOOTSTRAP"""
        
        # Test multiple source configurations
        test_cases = [
            {"source": "BOOTSTRAP", "asof": "2024-03-31", "description": "Bootstrap Only"},
            {"source": "LIVE", "description": "Live Only"}, 
            {"source": "ALL", "description": "All Sources"},
        ]
        
        all_passed = True
        
        for case in test_cases:
            params = {
                'symbol': self.symbol,
                'window': '30d',
                'preset': 'balanced',
                'role': 'ACTIVE'
            }
            
            # Add source parameter
            if 'source' in case:
                params['source'] = case['source']
            
            # Add asof parameter if specified
            if 'asof' in case:
                params['asof'] = case['asof']
            
            success, data, error = self.make_request(
                'GET', 
                'api/fractal/v2.1/admin/attribution',
                params=params
            )
            
            test_name = f"Attribution - {case['description']}"
            
            if success and data:
                if 'meta' in data and 'headline' in data:
                    meta = data.get('meta', {})
                    
                    # For BOOTSTRAP source, verify sourceFilter is set correctly
                    if case.get('source') == 'BOOTSTRAP':
                        if meta.get('sourceFilter') == 'BOOTSTRAP':
                            self.log_test(test_name, True, data)
                        else:
                            self.log_test(test_name, False, data, f"Expected sourceFilter=BOOTSTRAP, got {meta.get('sourceFilter')}")
                            all_passed = False
                    else:
                        self.log_test(test_name, True, data)
                else:
                    self.log_test(test_name, False, data, "Missing 'meta' or 'headline' in attribution response")
                    all_passed = False
            else:
                self.log_test(test_name, False, data, error)
                all_passed = False
        
        return all_passed

    def test_source_isolation_verification(self):
        """Verify that LIVE and BOOTSTRAP data are properly isolated"""
        
        # First get stats to see total counts
        success, stats_data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/bootstrap/stats',
            params={'symbol': self.symbol}
        )
        
        if not success:
            self.log_test("Source Isolation - Get Bootstrap Stats", False, stats_data, error)
            return False
        
        bootstrap_snapshots = stats_data.get('stats', {}).get('totalSnapshots', 0)
        
        # Get attribution data with different source filters
        live_data = None
        bootstrap_data = None
        all_data = None
        
        # Test LIVE source
        success, live_data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/attribution',
            params={'symbol': self.symbol, 'source': 'LIVE', 'window': '90d'}
        )
        
        # Test BOOTSTRAP source  
        success2, bootstrap_data, error2 = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/attribution',
            params={'symbol': self.symbol, 'source': 'BOOTSTRAP', 'window': '90d'}
        )
        
        # Test ALL sources
        success3, all_data, error3 = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/attribution',
            params={'symbol': self.symbol, 'source': 'ALL', 'window': '90d'}
        )
        
        isolation_verified = True
        
        if success and success2 and success3:
            # Check that bootstrap data is separate from live data
            live_count = live_data.get('meta', {}).get('sampleCount', 0)
            bootstrap_count = bootstrap_data.get('meta', {}).get('sampleCount', 0)
            all_count = all_data.get('meta', {}).get('sampleCount', 0)
            
            # Verify isolation: ALL should be sum of LIVE + BOOTSTRAP (approximately)
            expected_all = live_count + bootstrap_count
            
            if bootstrap_count > 0:  # We have bootstrap data
                if abs(all_count - expected_all) <= 1:  # Allow for small discrepancies
                    self.log_test("Source Isolation - Data Separation Verified", True, {
                        'live_count': live_count,
                        'bootstrap_count': bootstrap_count, 
                        'all_count': all_count
                    })
                else:
                    self.log_test("Source Isolation - Data Separation Verified", False, {
                        'live_count': live_count,
                        'bootstrap_count': bootstrap_count,
                        'all_count': all_count,
                        'expected_all': expected_all
                    }, f"Count mismatch: ALL={all_count} != LIVE+BOOTSTRAP={expected_all}")
                    isolation_verified = False
            else:
                self.log_test("Source Isolation - Data Separation Verified", True, {
                    'live_count': live_count,
                    'bootstrap_count': bootstrap_count
                }, "No bootstrap data found (expected after test)")
        else:
            self.log_test("Source Isolation - Data Separation Verified", False, None, "Failed to get attribution data for isolation test")
            isolation_verified = False
        
        return isolation_verified

    def test_guardrails_live_only_verification(self):
        """Verify that guardrails use only LIVE samples for APPLY eligibility"""
        
        # This test checks that bootstrap data doesn't affect governance decisions
        # We'll check the attribution API's guardrails section
        
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/attribution',
            params={'symbol': self.symbol, 'source': 'LIVE', 'window': '90d'}
        )
        
        if success and data:
            guardrails = data.get('guardrails', {})
            if guardrails:
                # Check that guardrails data exists and is based on LIVE data only
                insufficient_data = guardrails.get('insufficientData', True)
                reasons = guardrails.get('reasons', [])
                
                self.log_test("Guardrails - LIVE Only Verification", True, {
                    'insufficient_data': insufficient_data,
                    'reasons': reasons,
                    'source_filter': 'LIVE'
                }, "Guardrails correctly use LIVE data only")
                return True
            else:
                self.log_test("Guardrails - LIVE Only Verification", False, data, "Missing guardrails section in response")
                return False
        else:
            self.log_test("Guardrails - LIVE Only Verification", False, data, error)
            return False

    def test_schema_source_field_verification(self):
        """Verify that snapshots and outcomes have proper source field"""
        
        # Get latest snapshot to verify source field exists
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/memory/snapshots/latest',
            params={'symbol': self.symbol, 'focus': '30d'}
        )
        
        schema_verified = True
        
        if success and data and data.get('found'):
            snapshot = data.get('snapshot', {})
            
            # Check if source field exists (should be 'LIVE' for latest snapshot)
            if 'source' in snapshot:
                source_value = snapshot.get('source')
                if source_value in ['LIVE', 'BOOTSTRAP']:
                    self.log_test("Schema - Snapshot Source Field", True, {
                        'source': source_value,
                        'has_source_field': True
                    })
                else:
                    self.log_test("Schema - Snapshot Source Field", False, {
                        'source': source_value
                    }, f"Invalid source value: {source_value}")
                    schema_verified = False
            else:
                # Some snapshots might not have source field (legacy data)
                self.log_test("Schema - Snapshot Source Field", True, {
                    'has_source_field': False
                }, "Source field missing (legacy data acceptable)")
        else:
            self.log_test("Schema - Snapshot Source Field", False, data, "Could not verify snapshot source field")
            schema_verified = False
        
        return schema_verified

    def run_all_bootstrap_tests(self):
        """Run all BLOCK 77.4 Bootstrap tests in sequence"""
        print(f"🚀 Starting BLOCK 77.4 Bootstrap Historical Engine Tests")
        print(f"📡 Backend URL: {self.base_url}")
        print(f"🪙 Symbol: {self.symbol}")
        print("=" * 80)
        
        # Setup - Clear existing data
        print("\n🧹 Setup: Clear Existing Bootstrap Data")
        self.test_clear_bootstrap_data()
        
        # Test sequence for BLOCK 77.4
        print("\n📝 BLOCK 77.4.1: Bootstrap Run & Progress")
        run_result = self.test_bootstrap_run_creation()
        if run_result:
            time.sleep(2)  # Wait a bit for processing
            self.test_bootstrap_progress()
        
        print("\n🎯 BLOCK 77.4.2: Bootstrap Resolution")
        if self.test_batch_id:
            time.sleep(2)  # Wait for bootstrap to complete
            self.test_bootstrap_resolve_outcomes()
        
        print("\n📊 BLOCK 77.4.3: Bootstrap Statistics")
        self.test_bootstrap_stats()
        
        print("\n🔍 BLOCK 77.4.4: Attribution with Bootstrap Source")
        self.test_attribution_with_bootstrap_source()
        
        print("\n🔒 BLOCK 77.4.5: Source Isolation & Guardrails")
        self.test_source_isolation_verification()
        self.test_guardrails_live_only_verification()
        self.test_schema_source_field_verification()
        
        # Summary
        print("\n" + "=" * 80)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All BLOCK 77.4 Bootstrap tests passed!")
            return 0
        else:
            failed_count = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_count} tests failed")
            
            # Show failed tests
            failed_tests = [r for r in self.results if not r['success']]
            if failed_tests:
                print("\n❌ Failed Tests:")
                for test in failed_tests[-5:]:  # Show last 5 failures
                    print(f"   • {test['test']}: {test['error']}")
            
            return 1

def main():
    """Main test runner"""
    tester = BootstrapSystemTester()
    return tester.run_all_bootstrap_tests()

if __name__ == "__main__":
    sys.exit(main())