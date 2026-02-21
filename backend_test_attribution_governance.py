#!/usr/bin/env python3
"""
BLOCK 75.UI Attribution & Governance Tab Testing
Tests the new admin panel endpoints for institutional grade UI.
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class AttributionGovernanceTester:
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
                return False, None, f"HTTP {response.status_code}: {response.text[:200]}"

        except requests.exceptions.Timeout:
            return False, None, "Request timeout (30s)"
        except requests.exceptions.ConnectionError:
            return False, None, "Connection error"
        except Exception as e:
            return False, None, f"Request error: {str(e)}"

    def test_attribution_endpoint(self):
        """Test GET /api/fractal/v2.1/admin/attribution"""
        print("\n🔍 Testing Attribution Tab Endpoint...")
        
        # Test with default parameters
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/attribution',
            params={'symbol': self.symbol, 'window': '90d', 'preset': 'balanced', 'role': 'ACTIVE'}
        )
        
        if success and data:
            # Check for expected top-level structure
            expected_fields = ['meta', 'headline', 'tiers', 'regimes', 'divergence', 'phases', 'insights', 'guardrails']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                # Check meta structure
                meta = data.get('meta', {})
                meta_fields = ['symbol', 'windowDays', 'asof', 'preset', 'role', 'sampleCount', 'resolvedCount']
                has_meta = all(field in meta for field in meta_fields)
                
                # Check headline structure
                headline = data.get('headline', {})
                headline_fields = ['hitRate', 'expectancy', 'sharpe', 'maxDD', 'calibrationError', 'avgDivergenceScore']
                has_headline = all(field in headline for field in headline_fields)
                
                # Check tiers structure (should be array)
                tiers = data.get('tiers', [])
                is_tiers_array = isinstance(tiers, list)
                
                # Check guardrails structure
                guardrails = data.get('guardrails', {})
                guardrails_fields = ['minSamplesByTier', 'insufficientData', 'reasons']
                has_guardrails = all(field in guardrails for field in guardrails_fields)
                
                if has_meta and has_headline and is_tiers_array and has_guardrails:
                    # Check if we have insufficient data warning (expected behavior)
                    insufficient_data = guardrails.get('insufficientData', False)
                    sample_count = meta.get('sampleCount', 0)
                    
                    if insufficient_data and sample_count == 0:
                        self.log_test("Attribution Endpoint - Structure & Insufficient Data Warning", True, 
                                    {"sample_count": sample_count, "insufficient_data": insufficient_data})
                    elif sample_count > 0:
                        self.log_test("Attribution Endpoint - Structure & Data Available", True, 
                                    {"sample_count": sample_count})
                    else:
                        self.log_test("Attribution Endpoint - Structure Valid", True, data)
                else:
                    missing = []
                    if not has_meta: missing.append("meta fields")
                    if not has_headline: missing.append("headline fields")
                    if not is_tiers_array: missing.append("tiers array")
                    if not has_guardrails: missing.append("guardrails fields")
                    self.log_test("Attribution Endpoint", False, data, f"Missing: {', '.join(missing)}")
            else:
                missing_fields = [f for f in expected_fields if f not in data]
                self.log_test("Attribution Endpoint", False, data, f"Missing top-level fields: {missing_fields}")
        else:
            self.log_test("Attribution Endpoint", False, data, error)
        
        return data

    def test_attribution_parameters(self):
        """Test Attribution endpoint with different parameters"""
        print("\n🔧 Testing Attribution Parameter Variations...")
        
        # Test different windows
        for window in ['30d', '180d', '365d']:
            success, data, error = self.make_request(
                'GET', 
                'api/fractal/v2.1/admin/attribution',
                params={'symbol': self.symbol, 'window': window, 'preset': 'balanced', 'role': 'ACTIVE'}
            )
            
            if success and data and 'meta' in data:
                expected_days = {'30d': 30, '180d': 180, '365d': 365}[window]
                actual_days = data['meta'].get('windowDays')
                if actual_days == expected_days:
                    self.log_test(f"Attribution Window {window}", True, {"windowDays": actual_days})
                else:
                    self.log_test(f"Attribution Window {window}", False, data, 
                                f"Expected {expected_days} days, got {actual_days}")
            else:
                self.log_test(f"Attribution Window {window}", False, data, error)
        
        # Test different presets
        for preset in ['conservative', 'aggressive']:
            success, data, error = self.make_request(
                'GET', 
                'api/fractal/v2.1/admin/attribution',
                params={'symbol': self.symbol, 'window': '90d', 'preset': preset, 'role': 'ACTIVE'}
            )
            
            if success and data and 'meta' in data:
                actual_preset = data['meta'].get('preset')
                if actual_preset == preset:
                    self.log_test(f"Attribution Preset {preset}", True, {"preset": actual_preset})
                else:
                    self.log_test(f"Attribution Preset {preset}", False, data, 
                                f"Expected {preset}, got {actual_preset}")
            else:
                self.log_test(f"Attribution Preset {preset}", False, data, error)

    def test_governance_endpoint(self):
        """Test GET /api/fractal/v2.1/admin/governance"""
        print("\n🏛️ Testing Governance Tab Endpoint...")
        
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/governance',
            params={'symbol': self.symbol}
        )
        
        if success and data:
            # Check for expected top-level structure
            expected_fields = ['currentPolicy', 'proposedChanges', 'driftStats', 'guardrails', 'auditLog']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                # Check currentPolicy structure
                current_policy = data.get('currentPolicy', {})
                policy_fields = ['version', 'tierWeights', 'horizonWeights', 'regimeMultipliers', 
                               'divergencePenalties', 'phaseGradeMultipliers', 'updatedAt']
                has_policy = all(field in current_policy for field in policy_fields)
                
                # Check tierWeights structure
                tier_weights = current_policy.get('tierWeights', {})
                expected_tiers = ['STRUCTURE', 'TACTICAL', 'TIMING']
                has_tier_weights = all(tier in tier_weights for tier in expected_tiers)
                
                # Check guardrails structure
                guardrails = data.get('guardrails', {})
                guardrails_fields = ['minSamplesOk', 'driftWithinLimit', 'notInCrisis', 'canApply', 'reasons']
                has_guardrails = all(field in guardrails for field in guardrails_fields)
                
                # Check auditLog structure (should be array)
                audit_log = data.get('auditLog', [])
                is_audit_array = isinstance(audit_log, list)
                
                if has_policy and has_tier_weights and has_guardrails and is_audit_array:
                    # Check if proposed changes exist
                    proposed_changes = data.get('proposedChanges')
                    if proposed_changes is None:
                        self.log_test("Governance Endpoint - No Proposed Changes", True, 
                                    {"has_proposed": False, "audit_entries": len(audit_log)})
                    else:
                        self.log_test("Governance Endpoint - With Proposed Changes", True, 
                                    {"has_proposed": True, "audit_entries": len(audit_log)})
                else:
                    missing = []
                    if not has_policy: missing.append("currentPolicy fields")
                    if not has_tier_weights: missing.append("tierWeights")
                    if not has_guardrails: missing.append("guardrails fields")
                    if not is_audit_array: missing.append("auditLog array")
                    self.log_test("Governance Endpoint", False, data, f"Missing: {', '.join(missing)}")
            else:
                missing_fields = [f for f in expected_fields if f not in data]
                self.log_test("Governance Endpoint", False, data, f"Missing top-level fields: {missing_fields}")
        else:
            self.log_test("Governance Endpoint", False, data, error)
        
        return data

    def test_governance_actions(self):
        """Test Governance action endpoints"""
        print("\n⚙️ Testing Governance Actions...")
        
        # Test DRY_RUN
        success, data, error = self.make_request(
            'POST', 
            'api/fractal/v2.1/admin/governance/policy/dry-run',
            params={'symbol': self.symbol}
        )
        
        if success and data:
            # Should have mode, success, message fields
            expected_fields = ['mode', 'success', 'message']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields and data.get('mode') == 'DRY_RUN':
                # Can succeed or fail depending on data availability
                if data.get('success'):
                    self.log_test("Governance Dry Run - Success", True, 
                                {"success": True, "message": data.get('message')})
                else:
                    self.log_test("Governance Dry Run - Expected Failure", True, 
                                {"success": False, "message": data.get('message')})
            else:
                self.log_test("Governance Dry Run", False, data, "Missing fields or wrong mode")
        else:
            self.log_test("Governance Dry Run", False, data, error)
        
        # Test PROPOSE (should work similar to dry-run)
        success, data, error = self.make_request(
            'POST', 
            'api/fractal/v2.1/admin/governance/policy/propose',
            params={'symbol': self.symbol}
        )
        
        if success and data:
            expected_fields = ['mode', 'success', 'message']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields and data.get('mode') == 'PROPOSE':
                # Can succeed or fail
                if data.get('success'):
                    self.log_test("Governance Propose - Success", True, 
                                {"success": True, "message": data.get('message')})
                else:
                    self.log_test("Governance Propose - Expected Failure", True, 
                                {"success": False, "message": data.get('message')})
            else:
                self.log_test("Governance Propose", False, data, "Missing fields or wrong mode")
        else:
            self.log_test("Governance Propose", False, data, error)

    def test_governance_info_endpoints(self):
        """Test Governance information endpoints"""
        print("\n📋 Testing Governance Info Endpoints...")
        
        # Test current policy
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/governance/policy/current',
            params={'symbol': self.symbol}
        )
        
        if success and data:
            if 'symbol' in data and 'config' in data:
                config = data.get('config', {})
                expected_fields = ['tierWeights', 'horizonWeights', 'regimeMultipliers']
                has_fields = all(field in config for field in expected_fields)
                
                if has_fields:
                    self.log_test("Current Policy", True, {"symbol": data.get('symbol')})
                else:
                    self.log_test("Current Policy", False, data, "Missing config fields")
            else:
                self.log_test("Current Policy", False, data, "Missing symbol or config")
        else:
            self.log_test("Current Policy", False, data, error)
        
        # Test policy history
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/governance/policy/history',
            params={'symbol': self.symbol, 'limit': '5'}
        )
        
        if success and data:
            expected_fields = ['symbol', 'count', 'proposals']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                count = data.get('count', 0)
                proposals = data.get('proposals', [])
                if count == len(proposals):
                    self.log_test("Policy History", True, {"count": count})
                else:
                    self.log_test("Policy History", False, data, f"Count mismatch: {count} vs {len(proposals)}")
            else:
                self.log_test("Policy History", False, data, "Missing expected fields")
        else:
            self.log_test("Policy History", False, data, error)
        
        # Test pending proposals
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/governance/policy/pending',
            params={'symbol': self.symbol}
        )
        
        if success and data:
            expected_fields = ['symbol', 'count', 'proposals']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                count = data.get('count', 0)
                proposals = data.get('proposals', [])
                if count == len(proposals):
                    self.log_test("Pending Proposals", True, {"count": count})
                else:
                    self.log_test("Pending Proposals", False, data, f"Count mismatch: {count} vs {len(proposals)}")
            else:
                self.log_test("Pending Proposals", False, data, "Missing expected fields")
        else:
            self.log_test("Pending Proposals", False, data, error)

    def run_all_tests(self):
        """Run all Attribution & Governance UI tests"""
        print(f"🚀 Starting BLOCK 75.UI Attribution & Governance Tab Tests")
        print(f"📡 Backend URL: {self.base_url}")
        print(f"🪙 Symbol: {self.symbol}")
        print("=" * 80)
        
        # Test Attribution Tab
        print("\n📊 BLOCK 75.UI.1: Attribution Tab")
        self.test_attribution_endpoint()
        self.test_attribution_parameters()
        
        # Test Governance Tab
        print("\n🏛️ BLOCK 75.UI.2: Governance Tab")
        self.test_governance_endpoint()
        self.test_governance_actions()
        self.test_governance_info_endpoints()
        
        # Summary
        print("\n" + "=" * 80)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All Attribution & Governance UI tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    """Main test runner"""
    tester = AttributionGovernanceTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())