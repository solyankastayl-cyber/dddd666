#!/usr/bin/env python3
"""
BLOCK 79 — Proposal Persistence + Audit Trail Testing
Tests all proposal lifecycle endpoints and audit trail functionality.
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class Block79ProposalTester:
    def __init__(self, base_url="https://consensus-timeline.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []
        self.symbol = "BTC"
        self.test_proposal_id = None
        self.test_application_id = None

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

    def test_create_proposal(self):
        """Test POST /api/fractal/v2.1/admin/proposal/propose"""
        test_data = {
            "symbol": self.symbol,
            "preset": "balanced",
            "role": "ACTIVE",
            "focus": "30d",
            "source": "LIVE",
            "window": 90
        }
        
        success, data, error = self.make_request(
            'POST', 
            'api/fractal/v2.1/admin/proposal/propose',
            data=test_data
        )
        
        if success and data:
            if data.get('ok') and 'proposal' in data:
                proposal = data['proposal']
                expected_fields = ['proposalId', 'status', 'verdict', 'source', 'scope', 'deltas', 'simulation', 'guardrails']
                has_fields = all(field in proposal for field in expected_fields)
                
                if has_fields:
                    if proposal.get('status') == 'PROPOSED' and proposal.get('source') == 'LIVE':
                        self.test_proposal_id = proposal['proposalId']
                        self.log_test("Create Proposal", True, data)
                        return proposal
                    else:
                        self.log_test("Create Proposal", False, data, f"Invalid status or source: {proposal.get('status')}, {proposal.get('source')}")
                else:
                    self.log_test("Create Proposal", False, data, "Missing expected proposal fields")
            else:
                self.log_test("Create Proposal", False, data, f"Missing ok=true or proposal field: {data}")
        else:
            self.log_test("Create Proposal", False, data, error)
        
        return None

    def test_list_proposals(self):
        """Test GET /api/fractal/v2.1/admin/proposal/list"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/proposal/list',
            params={'symbol': self.symbol, 'limit': '10'}
        )
        
        if success and data:
            if data.get('ok') and 'proposals' in data and 'total' in data:
                proposals = data['proposals']
                total = data['total']
                
                if len(proposals) <= total:
                    # Check if our test proposal exists
                    has_test_proposal = any(p.get('proposalId') == self.test_proposal_id for p in proposals) if self.test_proposal_id else True
                    
                    if has_test_proposal:
                        self.log_test("List Proposals", True, data)
                        return proposals
                    else:
                        self.log_test("List Proposals", False, data, f"Test proposal {self.test_proposal_id} not found in list")
                else:
                    self.log_test("List Proposals", False, data, f"Proposals length {len(proposals)} exceeds total {total}")
            else:
                self.log_test("List Proposals", False, data, "Missing ok=true, proposals, or total fields")
        else:
            self.log_test("List Proposals", False, data, error)
        
        return None

    def test_get_latest_proposal(self):
        """Test GET /api/fractal/v2.1/admin/proposal/latest"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/proposal/latest',
            params={'source': 'LIVE'}
        )
        
        if success and data:
            if data.get('ok'):
                proposal = data.get('proposal')
                if proposal:
                    expected_fields = ['proposalId', 'status', 'source', 'createdAt']
                    has_fields = all(field in proposal for field in expected_fields)
                    
                    if has_fields:
                        self.log_test("Get Latest Proposal", True, data)
                        return proposal
                    else:
                        self.log_test("Get Latest Proposal", False, data, "Missing expected proposal fields")
                else:
                    self.log_test("Get Latest Proposal", True, data, "No latest proposal (expected if none exist)")
                    return None
            else:
                self.log_test("Get Latest Proposal", False, data, "Missing ok=true")
        else:
            self.log_test("Get Latest Proposal", False, data, error)
        
        return None

    def test_get_proposal_by_id(self):
        """Test GET /api/fractal/v2.1/admin/proposal/:proposalId"""
        if not self.test_proposal_id:
            # Try to get an existing proposal ID
            success, data, error = self.make_request(
                'GET', 
                'api/fractal/v2.1/admin/proposal/list',
                params={'limit': '1'}
            )
            
            if success and data and data.get('proposals'):
                self.test_proposal_id = data['proposals'][0].get('proposalId')
            
            if not self.test_proposal_id:
                # Use the known existing proposal ID
                self.test_proposal_id = "prop_cb50d4f8"
        
        success, data, error = self.make_request(
            'GET', 
            f'api/fractal/v2.1/admin/proposal/{self.test_proposal_id}'
        )
        
        if success and data:
            if data.get('ok') and 'proposal' in data:
                proposal = data['proposal']
                if proposal.get('proposalId') == self.test_proposal_id:
                    self.log_test("Get Proposal by ID", True, data)
                    return proposal
                else:
                    self.log_test("Get Proposal by ID", False, data, f"ID mismatch: expected {self.test_proposal_id}, got {proposal.get('proposalId')}")
            else:
                self.log_test("Get Proposal by ID", False, data, "Missing ok=true or proposal field")
        else:
            self.log_test("Get Proposal by ID", False, data, error)
        
        return None

    def test_reject_proposal(self):
        """Test POST /api/fractal/v2.1/admin/proposal/reject/:proposalId"""
        # Create a new proposal specifically for rejection
        test_data = {
            "symbol": self.symbol,
            "preset": "conservative",
            "role": "SHADOW",
            "focus": "7d",
            "source": "V2020",
            "window": 30
        }
        
        success, data, error = self.make_request(
            'POST', 
            'api/fractal/v2.1/admin/proposal/propose',
            data=test_data
        )
        
        reject_proposal_id = None
        if success and data and data.get('ok'):
            reject_proposal_id = data['proposal']['proposalId']
        
        if not reject_proposal_id:
            self.log_test("Reject Proposal", False, None, "Could not create proposal for rejection test")
            return None
        
        # Now reject it
        reject_data = {
            "reason": "Test rejection for automation testing",
            "actor": "ADMIN"
        }
        
        success, data, error = self.make_request(
            'POST', 
            f'api/fractal/v2.1/admin/proposal/reject/{reject_proposal_id}',
            data=reject_data
        )
        
        if success and data:
            if data.get('ok') and 'proposal' in data:
                proposal = data['proposal']
                if proposal.get('status') == 'REJECTED' and proposal.get('rejectedReason'):
                    self.log_test("Reject Proposal", True, data)
                    return proposal
                else:
                    self.log_test("Reject Proposal", False, data, f"Status not REJECTED or missing reason: {proposal.get('status')}")
            else:
                self.log_test("Reject Proposal", False, data, "Missing ok=true or proposal field")
        else:
            self.log_test("Reject Proposal", False, data, error)
        
        return None

    def test_apply_proposal_governance_lock(self):
        """Test POST /api/fractal/v2.1/admin/proposal/apply/:proposalId - should fail due to governance lock"""
        if not self.test_proposal_id:
            self.log_test("Apply Proposal (Governance Lock)", False, None, "No test proposal ID available")
            return None
        
        apply_data = {
            "reason": "Test application - should be blocked by governance lock",
            "actor": "ADMIN"
        }
        
        success, data, error = self.make_request(
            'POST', 
            f'api/fractal/v2.1/admin/proposal/apply/{self.test_proposal_id}',
            data=apply_data
        )
        
        # This should FAIL due to governance lock (LIVE samples = 0, need >= 30)
        if success and data:
            if data.get('ok'):
                # This should NOT happen
                self.log_test("Apply Proposal (Governance Lock)", False, data, "Apply succeeded when it should be blocked by governance lock")
            else:
                # This is expected - blocked by governance lock
                error_msg = data.get('error', '').lower()
                if 'governance lock' in error_msg or 'live samples' in error_msg or 'blocked' in error_msg:
                    self.log_test("Apply Proposal (Governance Lock)", True, data, "Correctly blocked by governance lock")
                    return data
                else:
                    self.log_test("Apply Proposal (Governance Lock)", False, data, f"Failed but not due to governance lock: {data.get('error')}")
        else:
            # Check if error message indicates governance lock
            if error and ('governance' in error.lower() or 'lock' in error.lower() or 'samples' in error.lower()):
                self.log_test("Apply Proposal (Governance Lock)", True, None, f"Correctly blocked by governance lock: {error}")
            else:
                self.log_test("Apply Proposal (Governance Lock)", False, data, error)
        
        return None

    def test_get_current_policy(self):
        """Test GET /api/fractal/v2.1/admin/policy/current"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/policy/current'
        )
        
        if success and data:
            if data.get('ok') and 'policy' in data and 'hash' in data:
                policy = data['policy']
                hash_value = data['hash']
                version = data.get('version')
                
                # Check policy structure
                policy_fields = ['tierWeights', 'divergencePenalties', 'phaseGradeMultipliers']
                has_policy_fields = any(field in policy for field in policy_fields)
                
                if has_policy_fields and hash_value:
                    self.log_test("Get Current Policy", True, data)
                    return data
                else:
                    self.log_test("Get Current Policy", False, data, "Missing expected policy fields or hash")
            else:
                self.log_test("Get Current Policy", False, data, "Missing ok=true, policy, or hash fields")
        else:
            self.log_test("Get Current Policy", False, data, error)
        
        return None

    def test_get_audit_trail(self):
        """Test GET /api/fractal/v2.1/admin/policy/applications"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/policy/applications',
            params={'limit': '10'}
        )
        
        if success and data:
            if data.get('ok') and 'applications' in data and 'total' in data:
                applications = data['applications']
                total = data['total']
                
                # Each application should have expected fields
                for app in applications:
                    expected_fields = ['applicationId', 'proposalId', 'appliedAt', 'appliedBy', 'previousPolicyHash', 'newPolicyHash']
                    has_fields = all(field in app for field in expected_fields)
                    
                    if not has_fields:
                        self.log_test("Get Audit Trail", False, data, f"Application missing expected fields: {app}")
                        return None
                
                self.log_test("Get Audit Trail", True, data)
                return applications
            else:
                self.log_test("Get Audit Trail", False, data, "Missing ok=true, applications, or total fields")
        else:
            self.log_test("Get Audit Trail", False, data, error)
        
        return None

    def test_proposal_stats(self):
        """Test GET /api/fractal/v2.1/admin/proposal/stats"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/proposal/stats'
        )
        
        if success and data:
            if data.get('ok') and 'stats' in data:
                stats = data['stats']
                expected_fields = ['total', 'byStatus', 'bySource']
                has_fields = all(field in stats for field in expected_fields)
                
                if has_fields:
                    # Check that stats make sense
                    total = stats.get('total', 0)
                    by_status = stats.get('byStatus', {})
                    by_source = stats.get('bySource', {})
                    
                    # Sum of byStatus should equal total
                    status_sum = sum(by_status.values())
                    if total == status_sum:
                        self.log_test("Proposal Stats", True, data)
                        return stats
                    else:
                        self.log_test("Proposal Stats", False, data, f"Total mismatch: total={total}, status_sum={status_sum}")
                else:
                    self.log_test("Proposal Stats", False, data, "Missing expected stats fields")
            else:
                self.log_test("Proposal Stats", False, data, "Missing ok=true or stats field")
        else:
            self.log_test("Proposal Stats", False, data, error)
        
        return None

    def test_rollback_functionality(self):
        """Test POST /api/fractal/v2.1/admin/policy/rollback/:applicationId"""
        # First get applications to see if any exist
        applications = self.test_get_audit_trail()
        
        if not applications or len(applications) == 0:
            self.log_test("Rollback Functionality", True, None, "No applications to rollback (expected)")
            return None
        
        # Try to rollback the most recent application
        recent_app = applications[0]
        app_id = recent_app.get('applicationId')
        
        if not app_id:
            self.log_test("Rollback Functionality", False, applications, "No applicationId found")
            return None
        
        rollback_data = {
            "reason": "Test rollback for automation testing",
            "actor": "ADMIN"
        }
        
        success, data, error = self.make_request(
            'POST', 
            f'api/fractal/v2.1/admin/policy/rollback/{app_id}',
            data=rollback_data
        )
        
        if success and data:
            if data.get('ok'):
                # Rollback succeeded
                self.log_test("Rollback Functionality", True, data)
                return data
            else:
                # Check if error is acceptable (e.g., already rolled back)
                error_msg = data.get('error', '').lower()
                if 'already' in error_msg or 'not found' in error_msg:
                    self.log_test("Rollback Functionality", True, data, f"Expected error: {data.get('error')}")
                else:
                    self.log_test("Rollback Functionality", False, data, f"Unexpected error: {data.get('error')}")
        else:
            self.log_test("Rollback Functionality", False, data, error)
        
        return None

    def run_all_tests(self):
        """Run all BLOCK 79 Proposal Persistence tests"""
        print(f"🚀 Starting BLOCK 79 Proposal Persistence + Audit Trail Tests")
        print(f"📡 Backend URL: {self.base_url}")
        print(f"🪙 Symbol: {self.symbol}")
        print("=" * 80)
        
        print("\n📝 BLOCK 79.1: Proposal CRUD Operations")
        self.test_create_proposal()
        self.test_list_proposals()
        self.test_get_latest_proposal()
        self.test_get_proposal_by_id()
        
        print("\n🔄 BLOCK 79.2: Proposal Lifecycle Actions")
        self.test_reject_proposal()
        self.test_apply_proposal_governance_lock()
        
        print("\n📊 BLOCK 79.3: Policy State & Audit Trail")
        self.test_get_current_policy()
        self.test_get_audit_trail()
        self.test_proposal_stats()
        
        print("\n🔙 BLOCK 79.4: Rollback Functionality")
        self.test_rollback_functionality()
        
        # Summary
        print("\n" + "=" * 80)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All BLOCK 79 Proposal Persistence tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    """Main test runner for BLOCK 79"""
    tester = Block79ProposalTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())