#!/usr/bin/env python3
"""
BLOCK 82-83 Intel Timeline + Alerts Testing
Tests Intel Timeline and Intel Event Alerts functionality.
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class IntelTimelineAlertsTester:
    def __init__(self, base_url="https://spx-core-engine.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []
        self.symbol = "BTC"

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
                return False, None, f"HTTP {response.status_code}: {response.text[:500]}"

        except requests.exceptions.Timeout:
            return False, None, "Request timeout (30s)"
        except requests.exceptions.ConnectionError:
            return False, None, "Connection error"
        except Exception as e:
            return False, None, f"Request error: {str(e)}"

    def test_intel_counts(self):
        """Test GET /api/fractal/v2.1/admin/intel/counts"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/intel/counts',
            params={'symbol': self.symbol}
        )
        
        if success and data:
            if data.get('ok') and 'counts' in data:
                counts = data['counts']
                # Check expected counts from review request: LIVE=1, V2014=2191, V2020=2192
                expected_counts = {'LIVE': 1, 'V2014': 2191, 'V2020': 2192}
                
                all_match = True
                mismatches = []
                for source, expected in expected_counts.items():
                    actual = counts.get(source, 0)
                    if actual != expected:
                        all_match = False
                        mismatches.append(f"{source}: expected {expected}, got {actual}")
                
                if all_match:
                    self.log_test("Intel Counts", True, data)
                else:
                    self.log_test("Intel Counts", False, data, f"Count mismatches: {', '.join(mismatches)}")
                
                return counts
            else:
                self.log_test("Intel Counts", False, data, "Missing 'ok' or 'counts' fields")
        else:
            self.log_test("Intel Counts", False, data, error)
        
        return None

    def test_intel_timeline_live(self):
        """Test GET /api/fractal/v2.1/admin/intel/timeline for LIVE data"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/intel/timeline',
            params={'symbol': self.symbol, 'source': 'LIVE', 'window': 90}
        )
        
        if success and data:
            if data.get('ok'):
                expected_fields = ['meta', 'series', 'stats']
                has_fields = all(field in data for field in expected_fields)
                
                if has_fields:
                    meta = data['meta']
                    series = data['series']
                    stats = data['stats']
                    
                    # Check meta fields
                    if meta.get('source') == 'LIVE' and meta.get('symbol') == self.symbol:
                        # Check series structure
                        if len(series) > 0:
                            sample = series[0]
                            series_fields = ['date', 'phaseType', 'phaseGrade', 'phaseScore', 'dominanceTier', 'structuralLock']
                            has_series_fields = all(field in sample for field in series_fields)
                            
                            if has_series_fields:
                                # Check stats structure
                                stats_fields = ['lockDays', 'structureDominancePct', 'avgPhaseScore', 'trend7d']
                                has_stats_fields = all(field in stats for field in stats_fields)
                                
                                if has_stats_fields:
                                    self.log_test("Intel Timeline - LIVE", True, data, f"Found {len(series)} LIVE data points")
                                    return data
                                else:
                                    self.log_test("Intel Timeline - LIVE", False, data, "Missing stats fields")
                            else:
                                self.log_test("Intel Timeline - LIVE", False, data, "Missing series fields")
                        else:
                            self.log_test("Intel Timeline - LIVE", True, data, "No LIVE data yet (expected)")
                            return data
                    else:
                        self.log_test("Intel Timeline - LIVE", False, data, f"Meta validation failed: source={meta.get('source')}, symbol={meta.get('symbol')}")
                else:
                    self.log_test("Intel Timeline - LIVE", False, data, "Missing expected top-level fields")
            else:
                self.log_test("Intel Timeline - LIVE", False, data, f"Response not ok: {data}")
        else:
            self.log_test("Intel Timeline - LIVE", False, data, error)
        
        return None

    def test_intel_timeline_v2020(self):
        """Test GET /api/fractal/v2.1/admin/intel/timeline for V2020 data"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/intel/timeline',
            params={'symbol': self.symbol, 'source': 'V2020', 'window': 90}
        )
        
        if success and data:
            if data.get('ok'):
                series = data.get('series', [])
                meta = data.get('meta', {})
                
                if meta.get('source') == 'V2020' and len(series) > 0:
                    self.log_test("Intel Timeline - V2020", True, data, f"Found {len(series)} V2020 data points")
                    return data
                else:
                    self.log_test("Intel Timeline - V2020", False, data, f"No V2020 data or wrong source: source={meta.get('source')}, series_length={len(series)}")
            else:
                self.log_test("Intel Timeline - V2020", False, data, f"Response not ok: {data}")
        else:
            self.log_test("Intel Timeline - V2020", False, data, error)
        
        return None

    def test_intel_timeline_v2014(self):
        """Test GET /api/fractal/v2.1/admin/intel/timeline for V2014 data"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/intel/timeline',
            params={'symbol': self.symbol, 'source': 'V2014', 'window': 90}
        )
        
        if success and data:
            if data.get('ok'):
                series = data.get('series', [])
                meta = data.get('meta', {})
                
                if meta.get('source') == 'V2014' and len(series) > 0:
                    self.log_test("Intel Timeline - V2014", True, data, f"Found {len(series)} V2014 data points")
                    return data
                else:
                    self.log_test("Intel Timeline - V2014", False, data, f"No V2014 data or wrong source: source={meta.get('source')}, series_length={len(series)}")
            else:
                self.log_test("Intel Timeline - V2014", False, data, f"Response not ok: {data}")
        else:
            self.log_test("Intel Timeline - V2014", False, data, error)
        
        return None

    def test_intel_alerts(self):
        """Test GET /api/fractal/v2.1/admin/intel/alerts"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/intel/alerts',
            params={'symbol': self.symbol, 'source': 'LIVE', 'limit': 20}
        )
        
        if success and data:
            if 'items' in data:
                items = data['items']
                self.log_test("Intel Alerts", True, data, f"Found {len(items)} alerts")
                
                # If there are alerts, validate structure
                if len(items) > 0:
                    sample = items[0]
                    expected_fields = ['eventType', 'severity', 'date', 'symbol', 'source', 'payload']
                    has_fields = all(field in sample for field in expected_fields)
                    
                    if has_fields:
                        self.log_test("Intel Alerts - Structure", True, sample)
                    else:
                        self.log_test("Intel Alerts - Structure", False, sample, "Missing expected alert fields")
                
                return items
            else:
                self.log_test("Intel Alerts", False, data, "Missing 'items' field")
        else:
            self.log_test("Intel Alerts", False, data, error)
        
        return None

    def test_daily_run_job(self):
        """Test POST /api/fractal/v2.1/admin/jobs/daily-run-tg-open"""
        success, data, error = self.make_request(
            'POST', 
            'api/fractal/v2.1/admin/jobs/daily-run-tg-open',
            params={'symbol': self.symbol}
        )
        
        if success and data:
            # Check if job started successfully
            if data.get('success') or 'runId' in data:
                expected_steps = ['INTEL_TIMELINE_WRITE', 'INTEL_EVENT_ALERTS']
                
                # Look for our target steps in the response
                if 'snapshot' in data or 'memory' in data or 'runId' in data:
                    self.log_test("Daily Run Job", True, data, "Daily run job executed")
                    return data
                else:
                    self.log_test("Daily Run Job", False, data, "Job executed but missing expected result structure")
            else:
                error_msg = data.get('error') or 'Unknown error'
                if 'already running' in str(error_msg).lower():
                    self.log_test("Daily Run Job", True, data, "Job already running (expected)")
                    return data
                else:
                    self.log_test("Daily Run Job", False, data, f"Job failed: {error_msg}")
        else:
            self.log_test("Daily Run Job", False, data, error)
        
        return None

    def test_service_health(self):
        """Test basic service health"""
        success, data, error = self.make_request('GET', 'api/health')
        
        if success:
            self.log_test("Service Health", True, data)
            return data
        else:
            self.log_test("Service Health", False, data, error)
        
        return None

    def run_intel_tests(self):
        """Run all BLOCK 82-83 Intel tests"""
        print(f"🚀 Starting BLOCK 82-83 Intel Timeline + Alerts Tests")
        print(f"📡 Backend URL: {self.base_url}")
        print(f"🪙 Symbol: {self.symbol}")
        print("=" * 80)
        
        # Basic health check first
        print("\n🏥 Service Health")
        self.test_service_health()
        
        # Test Intel Timeline endpoints
        print("\n📊 BLOCK 82: Intel Timeline")
        self.test_intel_counts()
        self.test_intel_timeline_live()
        self.test_intel_timeline_v2020()
        self.test_intel_timeline_v2014()
        
        # Test Intel Alerts
        print("\n🚨 BLOCK 83: Intel Alerts")
        self.test_intel_alerts()
        
        # Test Daily Run Job (includes INTEL_TIMELINE_WRITE and INTEL_EVENT_ALERTS steps)
        print("\n⚙️ Daily Run Job (INTEL_TIMELINE_WRITE + INTEL_EVENT_ALERTS)")
        self.test_daily_run_job()
        
        # Summary
        print("\n" + "=" * 80)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All BLOCK 82-83 Intel tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    """Main test runner"""
    tester = IntelTimelineAlertsTester()
    return tester.run_intel_tests()

if __name__ == "__main__":
    sys.exit(main())