#!/usr/bin/env python3
"""
BLOCK 77 — Adaptive Weight Learning System Testing
Tests all learning endpoints for policy proposal generation and governance.
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class Block77LearningTester:
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
                    # POST without body
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

    def test_learning_vector(self):
        """Test GET /api/fractal/v2.1/learning-vector - returns tier/regime/phase performance, eligibility status"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/learning-vector',
            params={'symbol': self.symbol, 'window': '90', 'preset': 'balanced', 'role': 'ACTIVE'}
        )
        
        if success and data:
            # Check if we got expected structure
            if data.get('ok') and 'vector' in data:
                vector = data['vector']
                
                # Check required fields in learning vector
                required_fields = [
                    'symbol', 'windowDays', 'asof', 'resolvedSamples', 
                    'tier', 'regime', 'phase', 'divergenceImpact',
                    'equityDrift', 'calibrationError', 'learningEligible',
                    'eligibilityReasons', 'regimeDistribution', 'dominantTier', 'dominantRegime'
                ]
                has_required = all(field in vector for field in required_fields)
                
                if has_required:
                    # Check tier structure (STRUCTURE, TACTICAL, TIMING)
                    tier = vector.get('tier', {})
                    expected_tiers = ['STRUCTURE', 'TACTICAL', 'TIMING']
                    has_tiers = all(t in tier for t in expected_tiers)
                    
                    # Check regime structure (LOW, NORMAL, HIGH, EXPANSION, CRISIS)
                    regime = vector.get('regime', {})
                    expected_regimes = ['LOW', 'NORMAL', 'HIGH', 'EXPANSION', 'CRISIS']
                    has_regimes = all(r in regime for r in expected_regimes)
                    
                    # Check phase array exists
                    phase = vector.get('phase', [])
                    
                    if has_tiers and has_regimes:
                        self.log_test("Learning Vector API", True, {
                            'symbol': vector['symbol'],
                            'windowDays': vector['windowDays'],
                            'resolvedSamples': vector['resolvedSamples'],
                            'learningEligible': vector['learningEligible'],
                            'dominantTier': vector['dominantTier'],
                            'dominantRegime': vector['dominantRegime']
                        })
                        return vector
                    else:
                        self.log_test("Learning Vector API", False, data, f"Missing tier or regime structures: tiers={has_tiers}, regimes={has_regimes}")
                else:
                    missing = [f for f in required_fields if f not in vector]
                    self.log_test("Learning Vector API", False, data, f"Missing required fields: {missing}")
            elif data.get('error'):
                self.log_test("Learning Vector API", False, data, f"API returned error: {data.get('message', 'Unknown error')}")
            else:
                self.log_test("Learning Vector API", False, data, "Invalid response structure")
        else:
            self.log_test("Learning Vector API", False, data, error)
        
        return None

    def test_proposal_dry_run(self):
        """Test POST /api/fractal/v2.1/admin/governance/proposal/dry-run - generates proposal with verdict, deltas, guardrails, simulation"""
        success, data, error = self.make_request(
            'POST', 
            'api/fractal/v2.1/admin/governance/proposal/dry-run',
            data={'symbol': self.symbol, 'windowDays': 90, 'preset': 'balanced', 'role': 'ACTIVE'}
        )
        
        if success and data:
            if data.get('ok') and 'proposal' in data:
                proposal = data['proposal']
                
                # Check required proposal structure
                required_fields = [
                    'id', 'asof', 'symbol', 'windowDays', 'status',
                    'headline', 'deltas', 'guardrails', 'simulation',
                    'currentPolicy', 'proposedPolicy', 'audit'
                ]
                has_required = all(field in proposal for field in required_fields)
                
                if has_required:
                    # Check headline structure (verdict, risk, expectedImpact, summary)
                    headline = proposal.get('headline', {})
                    headline_fields = ['verdict', 'risk', 'expectedImpact', 'summary']
                    has_headline = all(field in headline for field in headline_fields)
                    
                    # Check guardrails structure
                    guardrails = proposal.get('guardrails', {})
                    guardrails_fields = ['eligible', 'reasons', 'checks']
                    has_guardrails = all(field in guardrails for field in guardrails_fields)
                    
                    # Check simulation structure
                    simulation = proposal.get('simulation', {})
                    simulation_fields = ['method', 'passed', 'notes', 'metrics']
                    has_simulation = all(field in simulation for field in simulation_fields)
                    
                    if has_headline and has_guardrails and has_simulation:
                        # Verify specific values
                        verdict = headline.get('verdict')
                        risk = headline.get('risk') 
                        eligible = guardrails.get('eligible')
                        sim_passed = simulation.get('passed')
                        method = simulation.get('method')
                        
                        if verdict in ['HOLD', 'TUNE', 'ROLLBACK'] and risk in ['LOW', 'MED', 'HIGH']:
                            self.log_test("Proposal Dry Run API", True, {
                                'id': proposal['id'],
                                'verdict': verdict,
                                'risk': risk,
                                'eligible': eligible,
                                'simulation_passed': sim_passed,
                                'method': method,
                                'deltas_count': len(proposal.get('deltas', [])),
                                'status': proposal['status']
                            })
                            return proposal
                        else:
                            self.log_test("Proposal Dry Run API", False, data, f"Invalid verdict ({verdict}) or risk ({risk})")
                    else:
                        self.log_test("Proposal Dry Run API", False, data, f"Missing structures: headline={has_headline}, guardrails={has_guardrails}, simulation={has_simulation}")
                else:
                    missing = [f for f in required_fields if f not in proposal]
                    self.log_test("Proposal Dry Run API", False, data, f"Missing required fields: {missing}")
            elif data.get('error'):
                self.log_test("Proposal Dry Run API", False, data, f"API returned error: {data.get('message', 'Unknown error')}")
            else:
                self.log_test("Proposal Dry Run API", False, data, "Invalid response structure")
        else:
            self.log_test("Proposal Dry Run API", False, data, error)
        
        return None

    def test_proposal_latest(self):
        """Test GET /api/fractal/v2.1/admin/governance/proposal/latest - returns latest proposal"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/governance/proposal/latest',
            params={'symbol': self.symbol}
        )
        
        if success and data:
            if data.get('ok') and 'proposal' in data:
                proposal = data['proposal']
                
                # Should have same structure as dry-run proposal
                required_fields = [
                    'id', 'asof', 'symbol', 'windowDays', 'status',
                    'headline', 'guardrails', 'simulation'
                ]
                has_required = all(field in proposal for field in required_fields)
                
                if has_required:
                    headline = proposal.get('headline', {})
                    verdict = headline.get('verdict')
                    risk = headline.get('risk')
                    
                    if verdict in ['HOLD', 'TUNE', 'ROLLBACK'] and risk in ['LOW', 'MED', 'HIGH']:
                        self.log_test("Latest Proposal API", True, {
                            'id': proposal['id'],
                            'verdict': verdict,
                            'risk': risk,
                            'status': proposal['status'],
                            'symbol': proposal['symbol']
                        })
                        return proposal
                    else:
                        self.log_test("Latest Proposal API", False, data, f"Invalid verdict ({verdict}) or risk ({risk})")
                else:
                    missing = [f for f in required_fields if f not in proposal]
                    self.log_test("Latest Proposal API", False, data, f"Missing required fields: {missing}")
            elif data.get('error'):
                self.log_test("Latest Proposal API", False, data, f"API returned error: {data.get('message', 'Unknown error')}")
            else:
                self.log_test("Latest Proposal API", False, data, "Invalid response structure")
        else:
            self.log_test("Latest Proposal API", False, data, error)
        
        return None

    def test_proposal_propose(self):
        """Test POST /api/fractal/v2.1/admin/governance/proposal/propose - save proposal for review"""
        success, data, error = self.make_request(
            'POST', 
            'api/fractal/v2.1/admin/governance/proposal/propose',
            data={'symbol': self.symbol, 'windowDays': 90, 'preset': 'balanced', 'role': 'ACTIVE'}
        )
        
        if success and data:
            # This may fail if guardrails fail, which is expected behavior
            if data.get('ok') and 'proposal' in data:
                proposal = data['proposal']
                # Should have status = 'PROPOSED'
                if proposal.get('status') == 'PROPOSED':
                    self.log_test("Propose API - Success", True, {'id': proposal['id'], 'status': proposal['status']})
                    return proposal
                else:
                    self.log_test("Propose API - Status Check", False, data, f"Expected status PROPOSED, got {proposal.get('status')}")
            elif not data.get('ok') and data.get('error'):
                # Expected failure case (guardrails or simulation failed)
                error_type = data.get('error')
                if error_type in ['GUARDRAILS_FAILED', 'SIMULATION_FAILED']:
                    reasons = data.get('reasons', data.get('notes', []))
                    self.log_test("Propose API - Expected Failure", True, {'error': error_type, 'reasons': reasons}, f"Expected failure: {error_type}")
                    return data
                else:
                    self.log_test("Propose API", False, data, f"Unexpected error: {error_type}")
            else:
                self.log_test("Propose API", False, data, "Invalid response structure")
        else:
            self.log_test("Propose API", False, data, error)
        
        return None

    def test_proposal_apply(self):
        """Test POST /api/fractal/v2.1/admin/governance/proposal/apply - apply a proposed policy change"""
        success, data, error = self.make_request(
            'POST', 
            'api/fractal/v2.1/admin/governance/proposal/apply',
            data={'proposalId': 'test_proposal_id'}
        )
        
        if success and data:
            # This should return NOT_IMPLEMENTED as mentioned in the code
            if not data.get('ok') and data.get('error') == 'NOT_IMPLEMENTED':
                self.log_test("Apply API - Not Implemented", True, data, "Expected NOT_IMPLEMENTED response")
                return data
            elif data.get('error') == 'PROPOSAL_ID_REQUIRED':
                # Test without proposalId
                success2, data2, error2 = self.make_request(
                    'POST', 
                    'api/fractal/v2.1/admin/governance/proposal/apply',
                    data={}
                )
                if success2 and data2.get('error') == 'PROPOSAL_ID_REQUIRED':
                    self.log_test("Apply API - Validation", True, data2, "Expected PROPOSAL_ID_REQUIRED validation")
                    return data2
                else:
                    self.log_test("Apply API - Validation", False, data2, "Expected PROPOSAL_ID_REQUIRED error")
            else:
                self.log_test("Apply API", False, data, "Unexpected response structure")
        else:
            self.log_test("Apply API", False, data, error)
        
        return None

    def run_all_tests(self):
        """Run all BLOCK 77 tests in sequence"""
        print(f"🚀 Starting BLOCK 77 Adaptive Weight Learning Tests")
        print(f"📡 Backend URL: {self.base_url}")
        print(f"🪙 Symbol: {self.symbol}")
        print("=" * 80)
        
        # Test sequence for BLOCK 77
        print("\n🧠 BLOCK 77.1: Learning Aggregator Service")
        learning_vector = self.test_learning_vector()
        
        print("\n⚖️ BLOCK 77.2: Proposal Engine")
        dry_run_proposal = self.test_proposal_dry_run()
        latest_proposal = self.test_proposal_latest()
        propose_result = self.test_proposal_propose()
        apply_result = self.test_proposal_apply()
        
        # Summary
        print("\n" + "=" * 80)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        # Additional analysis
        if learning_vector:
            print(f"\n🔍 Learning Analysis:")
            print(f"   • Samples: {learning_vector.get('resolvedSamples', 0)}")
            print(f"   • Eligible: {learning_vector.get('learningEligible', False)}")
            print(f"   • Dominant Tier: {learning_vector.get('dominantTier', 'N/A')}")
            print(f"   • Dominant Regime: {learning_vector.get('dominantRegime', 'N/A')}")
            
            if not learning_vector.get('learningEligible', False):
                reasons = learning_vector.get('eligibilityReasons', [])
                print(f"   • Ineligibility Reasons: {reasons}")
        
        if dry_run_proposal:
            print(f"\n📋 Proposal Analysis:")
            headline = dry_run_proposal.get('headline', {})
            print(f"   • Verdict: {headline.get('verdict', 'N/A')}")
            print(f"   • Risk: {headline.get('risk', 'N/A')}")
            print(f"   • Guardrails Pass: {dry_run_proposal.get('guardrails', {}).get('eligible', False)}")
            print(f"   • Simulation Pass: {dry_run_proposal.get('simulation', {}).get('passed', False)}")
            print(f"   • Delta Count: {len(dry_run_proposal.get('deltas', []))}")
            
            if not dry_run_proposal.get('guardrails', {}).get('eligible', False):
                reasons = dry_run_proposal.get('guardrails', {}).get('reasons', [])
                print(f"   • Guardrail Failures: {reasons}")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All BLOCK 77 tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    """Main test runner"""
    tester = Block77LearningTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())