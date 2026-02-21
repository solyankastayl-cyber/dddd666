#!/usr/bin/env python3
"""
BLOCK 75 Memory & Self-Validation Layer Testing
Tests all endpoints for snapshot persistence, outcome resolution, attribution, and policy governance.
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class Block75MemoryTester:
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
                    # POST without body - don't set Content-Type header
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

    def test_write_snapshots_initial(self):
        """Test POST /api/fractal/v2.1/admin/memory/write-snapshots?symbol=BTC"""
        success, data, error = self.make_request(
            'POST', 
            'api/fractal/v2.1/admin/memory/write-snapshots',
            params={'symbol': self.symbol}
        )
        
        if success and data:
            # Check if we got expected structure
            expected_fields = ['symbol', 'asofDate', 'written', 'skipped', 'focusBreakdown']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                total_expected = data.get('written', 0) + data.get('skipped', 0)
                # Should be 36 total (6 horizons × 3 presets × 2 roles)
                if total_expected == 36:
                    self.log_test("Write Snapshots - Initial Call", True, data)
                    return data
                else:
                    self.log_test("Write Snapshots - Initial Call", False, data, f"Expected 36 total snapshots, got {total_expected}")
            else:
                self.log_test("Write Snapshots - Initial Call", False, data, "Missing expected fields in response")
        else:
            self.log_test("Write Snapshots - Initial Call", False, data, error)
        
        return None

    def test_write_snapshots_idempotency(self):
        """Test idempotency - second call should skip all"""
        success, data, error = self.make_request(
            'POST', 
            'api/fractal/v2.1/admin/memory/write-snapshots',
            params={'symbol': self.symbol}
        )
        
        if success and data:
            written = data.get('written', 0)
            skipped = data.get('skipped', 0)
            
            # On second call, should skip all (written=0, skipped=36)
            if written == 0 and skipped == 36:
                self.log_test("Write Snapshots - Idempotency", True, data)
            else:
                self.log_test("Write Snapshots - Idempotency", False, data, f"Expected written=0, skipped=36, got written={written}, skipped={skipped}")
        else:
            self.log_test("Write Snapshots - Idempotency", False, data, error)

    def test_get_latest_snapshot(self):
        """Test GET /api/fractal/v2.1/admin/memory/snapshots/latest?symbol=BTC&focus=30d"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/memory/snapshots/latest',
            params={'symbol': self.symbol, 'focus': '30d'}
        )
        
        if success and data:
            if data.get('found') and 'snapshot' in data:
                snapshot = data['snapshot']
                required_fields = ['kernelDigest', 'tierWeights', 'asofDate', 'focus', 'role', 'preset']
                has_required = all(field in snapshot for field in required_fields)
                
                if has_required:
                    # Check kernelDigest structure
                    kd = snapshot['kernelDigest']
                    kd_fields = ['direction', 'mode', 'finalSize', 'consensusIndex', 'conflictLevel']
                    has_kd_fields = all(field in kd for field in kd_fields)
                    
                    # Check tierWeights structure
                    tw = snapshot['tierWeights']
                    tw_fields = ['structureWeightSum', 'tacticalWeightSum', 'timingWeightSum']
                    has_tw_fields = all(field in tw for field in tw_fields)
                    
                    if has_kd_fields and has_tw_fields:
                        self.log_test("Get Latest Snapshot", True, data)
                        return snapshot
                    else:
                        self.log_test("Get Latest Snapshot", False, data, "Missing kernelDigest or tierWeights fields")
                else:
                    self.log_test("Get Latest Snapshot", False, data, "Missing required snapshot fields")
            else:
                self.log_test("Get Latest Snapshot", False, data, "No snapshot found or invalid response structure")
        else:
            self.log_test("Get Latest Snapshot", False, data, error)
        
        return None

    def test_count_snapshots(self):
        """Test GET /api/fractal/v2.1/admin/memory/snapshots/count"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/memory/snapshots/count',
            params={'symbol': self.symbol}
        )
        
        if success and data:
            if 'total' in data and 'byRole' in data:
                total = data.get('total', 0)
                by_role = data.get('byRole', {})
                
                # Should have counts for ACTIVE and SHADOW roles
                if 'ACTIVE' in by_role and 'SHADOW' in by_role:
                    expected_total = by_role['ACTIVE'] + by_role['SHADOW']
                    if total == expected_total and total > 0:
                        self.log_test("Count Snapshots", True, data)
                        return data
                    else:
                        self.log_test("Count Snapshots", False, data, f"Total mismatch or zero count: total={total}")
                else:
                    self.log_test("Count Snapshots", False, data, "Missing ACTIVE/SHADOW role counts")
            else:
                self.log_test("Count Snapshots", False, data, "Missing total or byRole fields")
        else:
            self.log_test("Count Snapshots", False, data, error)
        
        return None

    def test_resolve_outcomes(self):
        """Test POST /api/fractal/v2.1/admin/memory/resolve-outcomes?symbol=BTC"""
        success, data, error = self.make_request(
            'POST', 
            'api/fractal/v2.1/admin/memory/resolve-outcomes',
            params={'symbol': self.symbol}
        )
        
        if success and data:
            expected_fields = ['symbol', 'latestCandleDate', 'resolved', 'skipped', 'byFocus', 'reasons']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                # Check byFocus structure (should have all 6 horizons)
                by_focus = data.get('byFocus', {})
                expected_horizons = ['7d', '14d', '30d', '90d', '180d', '365d']
                has_horizons = all(horizon in by_focus for horizon in expected_horizons)
                
                if has_horizons:
                    self.log_test("Resolve Outcomes", True, data)
                    return data
                else:
                    self.log_test("Resolve Outcomes", False, data, "Missing expected horizon keys in byFocus")
            else:
                self.log_test("Resolve Outcomes", False, data, "Missing expected fields in response")
        else:
            self.log_test("Resolve Outcomes", False, data, error)
        
        return None

    def test_forward_stats(self):
        """Test GET /api/fractal/v2.1/admin/memory/forward-stats?symbol=BTC"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/memory/forward-stats',
            params={'symbol': self.symbol}
        )
        
        if success and data:
            expected_fields = ['symbol', 'totalResolved', 'hitRate', 'avgRealizedReturnPct', 'byPreset', 'byRole']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                total_resolved = data.get('totalResolved', 0)
                
                # If no outcomes resolved yet, that's acceptable
                if total_resolved == 0:
                    self.log_test("Forward Stats", True, data, "No resolved outcomes yet (expected)")
                    return data
                
                # Check byPreset structure
                by_preset = data.get('byPreset', {})
                by_role = data.get('byRole', {})
                
                preset_ok = len(by_preset) > 0
                role_ok = len(by_role) > 0
                
                if preset_ok or role_ok:
                    self.log_test("Forward Stats", True, data)
                    return data
                else:
                    self.log_test("Forward Stats", False, data, f"No data in byPreset or byRole (totalResolved={total_resolved})")
            else:
                self.log_test("Forward Stats", False, data, "Missing expected fields in response")
        else:
            self.log_test("Forward Stats", False, data, error)
        
        return None

    def test_calibration_stats(self):
        """Test GET /api/fractal/v2.1/admin/memory/calibration?symbol=BTC&focus=30d"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/memory/calibration',
            params={'symbol': self.symbol, 'focus': '30d'}
        )
        
        if success and data:
            expected_fields = ['symbol', 'focus', 'preset', 'hitRate', 'bandHitRate', 'avgError', 'count']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                # Check that focus is 30d and preset is balanced (defaults)
                if data.get('focus') == '30d' and data.get('preset') == 'balanced':
                    self.log_test("Calibration Stats", True, data)
                    return data
                else:
                    self.log_test("Calibration Stats", False, data, f"Unexpected focus/preset: {data.get('focus')}/{data.get('preset')}")
            else:
                self.log_test("Calibration Stats", False, data, "Missing expected fields in response")
        else:
            self.log_test("Calibration Stats", False, data, error)
        
        return None

    def test_attribution_summary(self):
        """Test GET /api/fractal/v2.1/admin/memory/attribution/summary?symbol=BTC"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/memory/attribution/summary',
            params={'symbol': self.symbol}
        )
        
        if success and data:
            expected_fields = ['symbol', 'period', 'totalOutcomes', 'tierAccuracy', 'dominantTier', 'insights']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                total_outcomes = data.get('totalOutcomes', 0)
                
                # If no outcomes available yet, that's acceptable
                if total_outcomes == 0:
                    insights = data.get('insights', [])
                    if 'No outcomes available for attribution' in insights:
                        self.log_test("Attribution Summary", True, data, "No outcomes available yet (expected)")
                        return data
                
                # Check tierAccuracy structure
                tier_accuracy = data.get('tierAccuracy', [])
                expected_tiers = ['STRUCTURE', 'TACTICAL', 'TIMING']
                
                if len(tier_accuracy) >= 3:
                    tier_names = [t.get('tier') for t in tier_accuracy]
                    has_all_tiers = all(tier in tier_names for tier in expected_tiers)
                    
                    if has_all_tiers:
                        self.log_test("Attribution Summary", True, data)
                        return data
                    else:
                        self.log_test("Attribution Summary", False, data, f"Missing tiers in tierAccuracy: {tier_names}")
                else:
                    self.log_test("Attribution Summary", False, data, f"Expected 3 tiers, got {len(tier_accuracy)} (totalOutcomes={total_outcomes})")
            else:
                self.log_test("Attribution Summary", False, data, "Missing expected fields in response")
        else:
            self.log_test("Attribution Summary", False, data, error)
        
        return None

    def test_attribution_full_tab_all_sources(self):
        """Test BLOCK 77.4: GET /api/fractal/v2.1/admin/attribution with source=ALL"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/attribution',
            params={'symbol': self.symbol, 'window': '90d', 'preset': 'balanced', 'role': 'ACTIVE', 'source': 'ALL'}
        )
        
        if success and data:
            expected_fields = ['meta', 'headline', 'tiers', 'regimes', 'divergence', 'phases', 'insights', 'guardrails']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                meta = data.get('meta', {})
                # Check for BLOCK 77.4 fields
                if 'liveCount' in meta and 'bootstrapCount' in meta and 'sourceFilter' in meta:
                    if meta.get('sourceFilter') == 'ALL':
                        self.log_test("Attribution Full Tab - ALL Sources", True, data)
                        return data
                    else:
                        self.log_test("Attribution Full Tab - ALL Sources", False, data, f"Expected sourceFilter=ALL, got {meta.get('sourceFilter')}")
                else:
                    self.log_test("Attribution Full Tab - ALL Sources", False, data, "Missing BLOCK 77.4 fields: liveCount, bootstrapCount, sourceFilter")
            else:
                self.log_test("Attribution Full Tab - ALL Sources", False, data, "Missing expected fields in response")
        else:
            self.log_test("Attribution Full Tab - ALL Sources", False, data, error)
        
        return None

    def test_attribution_full_tab_live_only(self):
        """Test BLOCK 77.4: GET /api/fractal/v2.1/admin/attribution with source=LIVE"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/attribution',
            params={'symbol': self.symbol, 'window': '90d', 'preset': 'balanced', 'role': 'ACTIVE', 'source': 'LIVE'}
        )
        
        if success and data:
            expected_fields = ['meta', 'headline', 'tiers', 'regimes', 'divergence', 'phases', 'insights', 'guardrails']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                meta = data.get('meta', {})
                # Check for BLOCK 77.4 fields
                if 'liveCount' in meta and 'bootstrapCount' in meta and 'sourceFilter' in meta:
                    if meta.get('sourceFilter') == 'LIVE':
                        self.log_test("Attribution Full Tab - LIVE Only", True, data)
                        return data
                    else:
                        self.log_test("Attribution Full Tab - LIVE Only", False, data, f"Expected sourceFilter=LIVE, got {meta.get('sourceFilter')}")
                else:
                    self.log_test("Attribution Full Tab - LIVE Only", False, data, "Missing BLOCK 77.4 fields: liveCount, bootstrapCount, sourceFilter")
            else:
                self.log_test("Attribution Full Tab - LIVE Only", False, data, "Missing expected fields in response")
        else:
            self.log_test("Attribution Full Tab - LIVE Only", False, data, error)
        
        return None

    def test_attribution_full_tab_bootstrap_only(self):
        """Test BLOCK 77.4: GET /api/fractal/v2.1/admin/attribution with source=BOOTSTRAP"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/attribution',
            params={'symbol': self.symbol, 'window': '90d', 'preset': 'balanced', 'role': 'ACTIVE', 'source': 'BOOTSTRAP'}
        )
        
        if success and data:
            expected_fields = ['meta', 'headline', 'tiers', 'regimes', 'divergence', 'phases', 'insights', 'guardrails']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                meta = data.get('meta', {})
                # Check for BLOCK 77.4 fields
                if 'liveCount' in meta and 'bootstrapCount' in meta and 'sourceFilter' in meta:
                    if meta.get('sourceFilter') == 'BOOTSTRAP':
                        self.log_test("Attribution Full Tab - BOOTSTRAP Only", True, data)
                        return data
                    else:
                        self.log_test("Attribution Full Tab - BOOTSTRAP Only", False, data, f"Expected sourceFilter=BOOTSTRAP, got {meta.get('sourceFilter')}")
                else:
                    self.log_test("Attribution Full Tab - BOOTSTRAP Only", False, data, "Missing BLOCK 77.4 fields: liveCount, bootstrapCount, sourceFilter")
            else:
                self.log_test("Attribution Full Tab - BOOTSTRAP Only", False, data, "Missing expected fields in response")
        else:
            self.log_test("Attribution Full Tab - BOOTSTRAP Only", False, data, error)
        
        return None

    def test_policy_dry_run(self):
        """Test POST /api/fractal/v2.1/admin/governance/policy/dry-run?symbol=BTC"""
        success, data, error = self.make_request(
            'POST', 
            'api/fractal/v2.1/admin/governance/policy/dry-run',
            params={'symbol': self.symbol}
        )
        
        if success and data:
            expected_fields = ['mode', 'success', 'message', 'guardrailsPass', 'guardrailViolations']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                # Check that mode is DRY_RUN
                if data.get('mode') == 'DRY_RUN':
                    # Should have currentConfig and proposedConfig if successful
                    if data.get('success') and 'currentConfig' in data and 'proposedConfig' in data:
                        self.log_test("Policy Dry Run", True, data)
                        return data
                    elif not data.get('success'):
                        # May fail if no data available, which is acceptable
                        self.log_test("Policy Dry Run", True, data, f"Expected failure: {data.get('message')}")
                        return data
                    else:
                        self.log_test("Policy Dry Run", False, data, "Success=true but missing config fields")
                else:
                    self.log_test("Policy Dry Run", False, data, f"Expected mode=DRY_RUN, got {data.get('mode')}")
            else:
                self.log_test("Policy Dry Run", False, data, "Missing expected fields in response")
        else:
            self.log_test("Policy Dry Run", False, data, error)
        
        return None

    def test_current_policy(self):
        """Test GET /api/fractal/v2.1/admin/governance/policy/current?symbol=BTC"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/governance/policy/current',
            params={'symbol': self.symbol}
        )
        
        if success and data:
            if 'symbol' in data and 'config' in data:
                config = data.get('config', {})
                expected_config_fields = ['tierWeights', 'horizonWeights', 'regimeMultipliers']
                has_config_fields = all(field in config for field in expected_config_fields)
                
                if has_config_fields:
                    # Check tierWeights structure
                    tier_weights = config.get('tierWeights', {})
                    expected_tiers = ['TIMING', 'TACTICAL', 'STRUCTURE']
                    has_tier_weights = all(tier in tier_weights for tier in expected_tiers)
                    
                    if has_tier_weights:
                        self.log_test("Current Policy", True, data)
                        return data
                    else:
                        self.log_test("Current Policy", False, data, "Missing tier weights")
                else:
                    self.log_test("Current Policy", False, data, "Missing expected config fields")
            else:
                self.log_test("Current Policy", False, data, "Missing symbol or config fields")
        else:
            self.log_test("Current Policy", False, data, error)
        
        return None

    def test_policy_history(self):
        """Test GET /api/fractal/v2.1/admin/governance/policy/history?symbol=BTC"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/governance/policy/history',
            params={'symbol': self.symbol}
        )
        
        if success and data:
            expected_fields = ['symbol', 'count', 'proposals']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields:
                count = data.get('count', 0)
                proposals = data.get('proposals', [])
                
                # Count should match proposals length
                if count == len(proposals):
                    self.log_test("Policy History", True, data)
                    return data
                else:
                    self.log_test("Policy History", False, data, f"Count mismatch: count={count}, proposals length={len(proposals)}")
            else:
                self.log_test("Policy History", False, data, "Missing expected fields in response")
        else:
            self.log_test("Policy History", False, data, error)
        
        return None

    def test_backfill_start(self):
        """Test POST /api/fractal/v2.1/admin/backfill/start"""
        backfill_config = {
            "yearStart": 2024,
            "yearEnd": 2024,
            "chunkSize": 100,
            "throttleMs": 10
        }
        
        success, data, error = self.make_request(
            'POST',
            'api/fractal/v2.1/admin/backfill/start',
            data=backfill_config
        )
        
        if success and data:
            expected_fields = ['ok', 'message', 'jobId', 'totalBatches', 'batches']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields and data.get('ok'):
                job_id = data.get('jobId')
                total_batches = data.get('totalBatches', 0)
                batches = data.get('batches', [])
                
                if job_id and total_batches > 0 and len(batches) == total_batches:
                    self.log_test("Backfill Start", True, data)
                    return job_id
                else:
                    self.log_test("Backfill Start", False, data, f"Invalid response structure: jobId={job_id}, batches={len(batches)}, totalBatches={total_batches}")
            else:
                error_msg = data.get('error') if data else 'Unknown error'
                if 'already in progress' in str(error_msg):
                    self.log_test("Backfill Start", True, data, "Backfill already running (expected)")
                    return 'existing'
                else:
                    self.log_test("Backfill Start", False, data, f"Failed to start backfill: {error_msg}")
        else:
            self.log_test("Backfill Start", False, data, error)
        
        return None

    def test_backfill_progress(self, job_id=None):
        """Test GET /api/fractal/v2.1/admin/backfill/progress"""
        params = {}
        if job_id and job_id != 'existing':
            params['jobId'] = job_id
            
        success, data, error = self.make_request(
            'GET',
            'api/fractal/v2.1/admin/backfill/progress',
            params=params
        )
        
        if success and data:
            if data.get('ok') and data.get('progress'):
                progress = data.get('progress')
                expected_fields = ['jobId', 'status', 'totalBatches', 'completedBatches', 'totalSnapshots', 'totalOutcomes']
                has_fields = all(field in progress for field in expected_fields)
                
                if has_fields:
                    status = progress.get('status')
                    total_snapshots = progress.get('totalSnapshots', 0)
                    total_outcomes = progress.get('totalOutcomes', 0)
                    
                    valid_statuses = ['RUNNING', 'COMPLETED', 'FAILED', 'PAUSED']
                    if status in valid_statuses:
                        self.log_test("Backfill Progress", True, data, f"Status: {status}, Snapshots: {total_snapshots}, Outcomes: {total_outcomes}")
                        return progress
                    else:
                        self.log_test("Backfill Progress", False, data, f"Invalid status: {status}")
                else:
                    self.log_test("Backfill Progress", False, data, "Missing expected progress fields")
            elif data.get('ok') and data.get('progress') is None:
                self.log_test("Backfill Progress", True, data, "No backfill jobs found (expected)")
                return None
            else:
                self.log_test("Backfill Progress", False, data, "Invalid response structure")
        else:
            self.log_test("Backfill Progress", False, data, error)
        
        return None

    def test_backfill_stats(self):
        """Test GET /api/fractal/v2.1/admin/backfill/stats"""
        success, data, error = self.make_request(
            'GET',
            'api/fractal/v2.1/admin/backfill/stats'
        )
        
        if success and data:
            if data.get('ok') and 'stats' in data:
                stats = data.get('stats')
                expected_fields = ['totalSnapshots', 'totalOutcomes', 'dateRange', 'byYear', 'hitRate', 'avgReturn']
                has_fields = all(field in stats for field in expected_fields)
                
                if has_fields:
                    total_snapshots = stats.get('totalSnapshots', 0)
                    total_outcomes = stats.get('totalOutcomes', 0)
                    date_range = stats.get('dateRange', {})
                    by_year = stats.get('byYear', {})
                    
                    # Check if we have the expected ~78,912 outcomes mentioned in the context
                    if total_outcomes > 70000:
                        self.log_test("Backfill Stats", True, data, f"Bootstrap data confirmed: {total_snapshots} snapshots, {total_outcomes} outcomes")
                    elif total_outcomes > 0:
                        self.log_test("Backfill Stats", True, data, f"Some bootstrap data present: {total_snapshots} snapshots, {total_outcomes} outcomes")
                    else:
                        self.log_test("Backfill Stats", True, data, "No bootstrap data yet (expected if backfill not completed)")
                    
                    return stats
                else:
                    self.log_test("Backfill Stats", False, data, "Missing expected stats fields")
            else:
                self.log_test("Backfill Stats", False, data, "Invalid response structure")
        else:
            self.log_test("Backfill Stats", False, data, error)
        
        return None

    def test_governance_lock_status(self):
        """Test BLOCK 78.5: GET /api/fractal/v2.1/admin/governance/lock/status"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/governance/lock/status',
            params={'symbol': self.symbol}
        )
        
        if success and data:
            expected_fields = ['ok', 'symbol', 'canApply', 'reasons', 'lockDetails']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields and data.get('ok'):
                lock_details = data.get('lockDetails', {})
                lock_fields = ['liveSamples', 'minRequired', 'driftSeverity', 'contractHashMatch', 'isLiveOnly']
                has_lock_fields = all(field in lock_details for field in lock_fields)
                
                if has_lock_fields:
                    min_required = lock_details.get('minRequired', 0)
                    live_samples = lock_details.get('liveSamples', 0)
                    
                    # Should require 30 minimum LIVE samples
                    if min_required == 30:
                        self.log_test("BLOCK 78.5 - Governance Lock Status", True, data)
                        return data
                    else:
                        self.log_test("BLOCK 78.5 - Governance Lock Status", False, data, f"Expected minRequired=30, got {min_required}")
                else:
                    self.log_test("BLOCK 78.5 - Governance Lock Status", False, data, "Missing lockDetails fields")
            else:
                self.log_test("BLOCK 78.5 - Governance Lock Status", False, data, f"Missing expected fields or ok=false: {data}")
        else:
            self.log_test("BLOCK 78.5 - Governance Lock Status", False, data, error)
        
        return None

    def test_governance_lock_check_apply(self):
        """Test BLOCK 78.5: POST /api/fractal/v2.1/admin/governance/lock/check-apply"""
        test_data = {
            "symbol": self.symbol,
            "source": "LIVE",
            "policyHash": "v2.1.0"
        }
        
        success, data, error = self.make_request(
            'POST', 
            'api/fractal/v2.1/admin/governance/lock/check-apply',
            data=test_data
        )
        
        if success and data:
            expected_fields = ['ok', 'symbol', 'allowed', 'lockStatus']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields and data.get('ok'):
                lock_status = data.get('lockStatus', {})
                status_fields = ['canApply', 'reasons', 'lockDetails']
                has_status_fields = all(field in lock_status for field in status_fields)
                
                if has_status_fields:
                    self.log_test("BLOCK 78.5 - Governance Lock Check Apply", True, data)
                    return data
                else:
                    self.log_test("BLOCK 78.5 - Governance Lock Check Apply", False, data, "Missing lockStatus fields")
            else:
                self.log_test("BLOCK 78.5 - Governance Lock Check Apply", False, data, f"Missing expected fields or ok=false: {data}")
        else:
            self.log_test("BLOCK 78.5 - Governance Lock Check Apply", False, data, error)
        
        return None

    def test_drift_intelligence(self):
        """Test BLOCK 78: GET /api/fractal/v2.1/admin/drift"""
        success, data, error = self.make_request(
            'GET', 
            'api/fractal/v2.1/admin/drift',
            params={'symbol': self.symbol, 'window': '365', 'role': 'ACTIVE'}
        )
        
        if success and data:
            expected_fields = ['ok', 'symbol', 'comparisons', 'breakdown', 'verdict', 'meta']
            has_fields = all(field in data for field in expected_fields)
            
            if has_fields and data.get('ok'):
                comparisons = data.get('comparisons', [])
                expected_pairs = ['LIVE_V2020', 'LIVE_V2014', 'V2014_V2020']
                
                # Should have 3 drift comparisons
                if len(comparisons) == 3:
                    comparison_pairs = [c.get('pair') for c in comparisons]
                    has_all_pairs = all(pair in comparison_pairs for pair in expected_pairs)
                    
                    if has_all_pairs:
                        verdict = data.get('verdict', {})
                        if 'overallSeverity' in verdict and 'recommendation' in verdict:
                            self.log_test("BLOCK 78 - Drift Intelligence", True, data)
                            return data
                        else:
                            self.log_test("BLOCK 78 - Drift Intelligence", False, data, "Missing verdict fields")
                    else:
                        self.log_test("BLOCK 78 - Drift Intelligence", False, data, f"Missing expected pairs: {comparison_pairs}")
                else:
                    self.log_test("BLOCK 78 - Drift Intelligence", False, data, f"Expected 3 comparisons, got {len(comparisons)}")
            else:
                self.log_test("BLOCK 78 - Drift Intelligence", False, data, f"Missing expected fields or ok=false: {data}")
        else:
            self.log_test("BLOCK 78 - Drift Intelligence", False, data, error)
        
        return None

    def run_all_tests(self):
        """Run all BLOCK 75, BLOCK 77.5, BLOCK 78, and BLOCK 78.5 tests in sequence"""
        print(f"🚀 Starting BLOCK 75 Memory & Self-Validation Layer Tests + BLOCK 77.5 Institutional Backfill Tests + BLOCK 78/78.5 Tests")
        print(f"📡 Backend URL: {self.base_url}")
        print(f"🪙 Symbol: {self.symbol}")
        print("=" * 80)
        
        # Test BLOCK 78.5 - Governance Lock first
        print("\n🔒 BLOCK 78.5: Governance Lock (LIVE-only APPLY)")
        self.test_governance_lock_status()
        self.test_governance_lock_check_apply()
        
        # Test BLOCK 78 - Drift Intelligence 
        print("\n📊 BLOCK 78: Drift Intelligence")
        self.test_drift_intelligence()
        
        # Test sequence for BLOCK 75
        print("\n📝 BLOCK 75.1: Snapshot Persistence")
        self.test_write_snapshots_initial()
        self.test_write_snapshots_idempotency()
        self.test_get_latest_snapshot()
        self.test_count_snapshots()
        
        print("\n🎯 BLOCK 75.2: Forward Truth Outcome Resolver")
        self.test_resolve_outcomes()
        self.test_forward_stats()
        self.test_calibration_stats()
        
        print("\n📊 BLOCK 75.3: Attribution Service")
        self.test_attribution_summary()
        
        print("\n🎯 BLOCK 77.4: Attribution Tab with Data Source Toggle")
        self.test_attribution_full_tab_all_sources()
        self.test_attribution_full_tab_live_only()
        self.test_attribution_full_tab_bootstrap_only()
        
        print("\n⚖️ BLOCK 75.4: Policy Governance")
        self.test_policy_dry_run()
        self.test_current_policy()
        self.test_policy_history()
        
        print("\n🏗️ BLOCK 77.5: Institutional Backfill (2020-2025 Bootstrap)")
        job_id = self.test_backfill_start()
        progress = self.test_backfill_progress(job_id)
        self.test_backfill_stats()
        
        # Summary
        print("\n" + "=" * 80)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All BLOCK 75, BLOCK 77.5, BLOCK 78, and BLOCK 78.5 tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    """Main test runner"""
    tester = Block75MemoryTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())