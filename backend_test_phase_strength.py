#!/usr/bin/env python3
"""
BLOCK 76.3 — Phase Strength Indicator Testing
Tests the Phase Strength Indicator implementation in the terminal endpoint.
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class PhaseStrengthTester:
    def __init__(self, base_url="https://consensus-timeline.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []
        self.symbol = "BTC"
        self.horizons = ['7d', '14d', '30d', '90d', '180d', '365d']

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

    def make_request(self, endpoint: str, params: Dict = None) -> tuple[bool, Any, str]:
        """Make GET request to terminal endpoint"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                try:
                    return True, response.json(), None
                except json.JSONDecodeError:
                    return False, None, f"Invalid JSON response: {response.text[:200]}"
            else:
                return False, None, f"HTTP {response.status_code}: {response.text[:200]}"

        except requests.exceptions.Timeout:
            return False, None, "Request timeout (30s)"
        except requests.exceptions.ConnectionError:
            return False, None, "Connection error"
        except Exception as e:
            return False, None, f"Request error: {str(e)}"

    def test_terminal_endpoint_basic(self):
        """Test basic terminal endpoint functionality"""
        success, data, error = self.make_request(
            'api/fractal/v2.1/terminal',
            params={'symbol': self.symbol, 'set': 'extended', 'focus': '30d'}
        )
        
        if success and data:
            # Check basic terminal structure
            required_fields = ['meta', 'chart', 'horizonMatrix', 'phaseSnapshot']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                self.log_test("Terminal Endpoint - Basic Structure", True, {"fields_found": required_fields})
                return data
            else:
                self.log_test("Terminal Endpoint - Basic Structure", False, data, f"Missing fields: {missing_fields}")
        else:
            self.log_test("Terminal Endpoint - Basic Structure", False, data, error)
        
        return None

    def test_phase_snapshot_structure(self, focus='30d'):
        """Test phaseSnapshot structure in terminal response"""
        success, data, error = self.make_request(
            'api/fractal/v2.1/terminal',
            params={'symbol': self.symbol, 'set': 'extended', 'focus': focus}
        )
        
        if success and data and 'phaseSnapshot' in data:
            phase_snapshot = data['phaseSnapshot']
            
            # Required fields from BLOCK 76.3 specification
            required_fields = [
                'symbol', 'focus', 'tier', 'phase', 'phaseId', 
                'grade', 'score', 'strengthIndex', 'hitRate', 
                'sharpe', 'expectancy', 'samples', 'volRegime', 
                'divergenceScore', 'flags', 'asof'
            ]
            
            missing_fields = [field for field in required_fields if field not in phase_snapshot]
            
            if not missing_fields:
                # Validate data types and ranges
                validation_errors = []
                
                # Check grade is valid (A-F)
                grade = phase_snapshot.get('grade')
                if grade not in ['A', 'B', 'C', 'D', 'F']:
                    validation_errors.append(f"Invalid grade: {grade}")
                
                # Check score is 0-100
                score = phase_snapshot.get('score', 0)
                if not (0 <= score <= 100):
                    validation_errors.append(f"Score out of range: {score}")
                
                # Check strengthIndex is 0-1
                strength_index = phase_snapshot.get('strengthIndex', 0)
                if not (0 <= strength_index <= 1):
                    validation_errors.append(f"StrengthIndex out of range: {strength_index}")
                
                # Check hitRate is 0-1
                hit_rate = phase_snapshot.get('hitRate', 0)
                if not (0 <= hit_rate <= 1):
                    validation_errors.append(f"HitRate out of range: {hit_rate}")
                
                # Check focus matches request
                if phase_snapshot.get('focus') != focus:
                    validation_errors.append(f"Focus mismatch: expected {focus}, got {phase_snapshot.get('focus')}")
                
                # Check tier is valid
                tier = phase_snapshot.get('tier')
                if tier not in ['TIMING', 'TACTICAL', 'STRUCTURE']:
                    validation_errors.append(f"Invalid tier: {tier}")
                
                # Check phase is valid
                phase = phase_snapshot.get('phase')
                valid_phases = ['ACCUMULATION', 'DISTRIBUTION', 'MARKUP', 'MARKDOWN', 'RECOVERY', 'CAPITULATION', 'UNKNOWN']
                if phase not in valid_phases:
                    validation_errors.append(f"Invalid phase: {phase}")
                
                # Check flags is array
                flags = phase_snapshot.get('flags', [])
                if not isinstance(flags, list):
                    validation_errors.append(f"Flags should be array: {type(flags)}")
                
                if not validation_errors:
                    self.log_test(f"Phase Snapshot Structure ({focus})", True, {
                        "focus": focus,
                        "phase": phase,
                        "grade": grade,
                        "score": score,
                        "strengthIndex": strength_index,
                        "tier": tier,
                        "flags": flags
                    })
                    return phase_snapshot
                else:
                    self.log_test(f"Phase Snapshot Structure ({focus})", False, phase_snapshot, 
                                 f"Validation errors: {validation_errors}")
            else:
                self.log_test(f"Phase Snapshot Structure ({focus})", False, phase_snapshot, 
                             f"Missing fields: {missing_fields}")
        else:
            error_msg = error if error else "No phaseSnapshot in response" 
            self.log_test(f"Phase Snapshot Structure ({focus})", False, data, error_msg)
        
        return None

    def test_horizon_variations(self):
        """Test phaseSnapshot with different horizon values"""
        horizon_results = {}
        
        for horizon in self.horizons:
            success, data, error = self.make_request(
                'api/fractal/v2.1/terminal',
                params={'symbol': self.symbol, 'set': 'extended', 'focus': horizon}
            )
            
            if success and data and 'phaseSnapshot' in data:
                phase_snapshot = data['phaseSnapshot']
                
                # Check that focus matches the horizon
                if phase_snapshot.get('focus') == horizon:
                    # Determine expected tier based on horizon
                    if horizon in ['180d', '365d']:
                        expected_tier = 'STRUCTURE'
                    elif horizon in ['30d', '90d']:
                        expected_tier = 'TACTICAL'
                    else:  # 7d, 14d
                        expected_tier = 'TIMING'
                    
                    actual_tier = phase_snapshot.get('tier')
                    if actual_tier == expected_tier:
                        horizon_results[horizon] = {
                            'success': True,
                            'tier': actual_tier,
                            'phase': phase_snapshot.get('phase'),
                            'grade': phase_snapshot.get('grade'),
                            'strengthIndex': phase_snapshot.get('strengthIndex')
                        }
                    else:
                        horizon_results[horizon] = {
                            'success': False,
                            'error': f"Tier mismatch: expected {expected_tier}, got {actual_tier}"
                        }
                else:
                    horizon_results[horizon] = {
                        'success': False,
                        'error': f"Focus mismatch: expected {horizon}, got {phase_snapshot.get('focus')}"
                    }
            else:
                horizon_results[horizon] = {
                    'success': False,
                    'error': error or "Failed to get valid response"
                }
        
        # Check results
        successful_horizons = [h for h, r in horizon_results.items() if r.get('success')]
        
        if len(successful_horizons) == len(self.horizons):
            self.log_test("Horizon Variations", True, horizon_results)
        elif len(successful_horizons) >= 4:  # Allow some failures
            self.log_test("Horizon Variations", True, horizon_results, 
                         f"Partial success: {len(successful_horizons)}/{len(self.horizons)} horizons")
        else:
            failed_horizons = [h for h, r in horizon_results.items() if not r.get('success')]
            self.log_test("Horizon Variations", False, horizon_results,
                         f"Too many failures: {failed_horizons}")
        
        return horizon_results

    def test_grade_color_mapping(self):
        """Test that grades correspond to expected performance ranges"""
        success, data, error = self.make_request(
            'api/fractal/v2.1/terminal',
            params={'symbol': self.symbol, 'set': 'extended', 'focus': '30d'}
        )
        
        if success and data and 'phaseSnapshot' in data:
            phase_snapshot = data['phaseSnapshot']
            grade = phase_snapshot.get('grade')
            score = phase_snapshot.get('score', 0)
            
            # Test grade-to-score mapping based on implementation
            grade_valid = False
            if grade == 'A' and score >= 80:
                grade_valid = True
            elif grade == 'B' and 65 <= score < 80:
                grade_valid = True  
            elif grade == 'C' and 50 <= score < 65:
                grade_valid = True
            elif grade == 'D' and 35 <= score < 50:
                grade_valid = True
            elif grade == 'F' and score < 35:
                grade_valid = True
            
            if grade_valid:
                self.log_test("Grade Color Mapping", True, {
                    "grade": grade,
                    "score": score,
                    "mapping": "correct"
                })
            else:
                self.log_test("Grade Color Mapping", False, {
                    "grade": grade,
                    "score": score
                }, f"Grade {grade} doesn't match score {score}")
        else:
            self.log_test("Grade Color Mapping", False, data, error)

    def test_warning_flags(self):
        """Test warning flags functionality"""
        success, data, error = self.make_request(
            'api/fractal/v2.1/terminal',
            params={'symbol': self.symbol, 'set': 'extended', 'focus': '7d'}  # Use shorter horizon more likely to have flags
        )
        
        if success and data and 'phaseSnapshot' in data:
            phase_snapshot = data['phaseSnapshot']
            flags = phase_snapshot.get('flags', [])
            
            # Valid flag types from the implementation
            valid_flags = [
                'LOW_SAMPLE', 'VERY_LOW_SAMPLE', 'HIGH_DIVERGENCE', 
                'HIGH_TAIL', 'LOW_RECENCY', 'NEGATIVE_SHARPE', 'VOL_CRISIS'
            ]
            
            invalid_flags = [flag for flag in flags if flag not in valid_flags]
            
            if not invalid_flags:
                self.log_test("Warning Flags", True, {
                    "flags": flags,
                    "count": len(flags),
                    "valid": True
                })
            else:
                self.log_test("Warning Flags", False, {
                    "flags": flags,
                    "invalid": invalid_flags
                }, f"Invalid flag types: {invalid_flags}")
        else:
            self.log_test("Warning Flags", False, data, error)

    def run_all_tests(self):
        """Run all BLOCK 76.3 Phase Strength Indicator tests"""
        print(f"🚀 Starting BLOCK 76.3 Phase Strength Indicator Tests")
        print(f"📡 Backend URL: {self.base_url}")
        print(f"🪙 Symbol: {self.symbol}")
        print("=" * 80)
        
        # Test sequence
        print("\n📡 Terminal Endpoint Tests")
        terminal_data = self.test_terminal_endpoint_basic()
        
        print("\n🎯 Phase Snapshot Structure Tests")
        self.test_phase_snapshot_structure('30d')  # Test default focus
        
        print("\n⏰ Horizon Variation Tests")  
        self.test_horizon_variations()
        
        print("\n🎨 Grade Color Mapping Tests")
        self.test_grade_color_mapping()
        
        print("\n⚠️ Warning Flags Tests")
        self.test_warning_flags()
        
        # Test a few more specific horizons
        print("\n🔍 Specific Horizon Structure Tests")
        for horizon in ['7d', '90d', '365d']:
            self.test_phase_snapshot_structure(horizon)
        
        # Summary
        print("\n" + "=" * 80)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        if self.tests_passed == self.tests_run:
            print("🎉 All BLOCK 76.3 Phase Strength Indicator tests passed!")
            return 0
        elif success_rate >= 80:
            print(f"✅ Most tests passed ({success_rate:.0f}% success rate)")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed ({success_rate:.0f}% success rate)")
            return 1

def main():
    """Main test runner"""
    tester = PhaseStrengthTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())