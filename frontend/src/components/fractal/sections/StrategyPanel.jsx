import React, { useEffect, useState } from 'react';

/**
 * BLOCK 55 — Strategy Engine Panel with Presets (Institutional)
 * 
 * Features:
 * - Preset selector (Conservative / Balanced / Aggressive)
 * - Policy-aware decision framework
 * - Edge diagnostics with preset-relative thresholds
 */

export function StrategyPanel({ symbol = 'BTC' }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [preset, setPreset] = useState('balanced');

  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    setLoading(true);
    fetch(`${API_URL}/api/fractal/v2.1/strategy?symbol=${symbol}&preset=${preset}`)
      .then(r => r.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [symbol, preset, API_URL]);

  if (loading && !data) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading Strategy Engine...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div style={styles.container}>
        <div style={styles.error}>Failed to load strategy data</div>
      </div>
    );
  }

  const { decision, edge, diagnostics, regime, appliedPreset } = data;

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <div style={styles.title}>STRATEGY ENGINE</div>
          <div style={styles.version}>v2 · Presets</div>
        </div>
        
        {/* Preset Selector */}
        <PresetSelector 
          value={preset} 
          onChange={setPreset}
          loading={loading}
        />
      </div>

      {/* Preset Summary */}
      {appliedPreset && (
        <div style={styles.presetSummary}>
          <span style={styles.presetLabel}>{appliedPreset.label}:</span>
          <span style={styles.presetDesc}>{appliedPreset.description}</span>
          <span style={styles.presetThresholds}>
            minConf: {(appliedPreset.thresholds.minConfidence * 100).toFixed(0)}% · 
            maxEntropy: {(appliedPreset.thresholds.maxEntropy * 100).toFixed(0)}% · 
            maxTail: {(appliedPreset.thresholds.maxTailP95DD * 100).toFixed(0)}%
          </span>
        </div>
      )}

      {/* Main Grid */}
      <div style={styles.grid}>
        {/* Left: Decision Summary */}
        <div style={styles.card}>
          <div style={styles.cardTitle}>Decision</div>
          
          <div style={styles.row}>
            <span style={styles.label}>MODE</span>
            <span style={{
              ...styles.value,
              ...styles.modeBadge,
              backgroundColor: getModeColor(decision.mode)
            }}>
              {decision.mode}
            </span>
          </div>

          <div style={styles.row}>
            <span style={styles.label}>REGIME</span>
            <span style={styles.value}>{regime}</span>
          </div>

          <div style={styles.row}>
            <span style={styles.label}>EDGE</span>
            <span style={{
              ...styles.value,
              color: getEdgeColor(edge.grade)
            }}>
              {edge.score}/100 · {edge.grade}
            </span>
          </div>

          {/* Blockers */}
          {decision.blockers && decision.blockers.length > 0 && (
            <div style={styles.blockers}>
              {decision.blockers.map((b, i) => (
                <span key={i} style={styles.blockerBadge}>{b}</span>
              ))}
            </div>
          )}

          <div style={styles.reason}>{decision.reason}</div>
        </div>

        {/* Middle: Position & Risk */}
        <div style={styles.card}>
          <div style={styles.cardTitle}>Position & Risk</div>
          
          <div style={styles.row}>
            <span style={styles.label}>Position Size</span>
            <span style={styles.value}>{(decision.positionSize * 100).toFixed(1)}%</span>
          </div>

          <div style={styles.row}>
            <span style={styles.label}>Risk/Reward</span>
            <span style={{
              ...styles.value,
              color: getRRColor(decision.riskReward)
            }}>
              {decision.riskReward.toFixed(2)}
            </span>
          </div>

          <div style={styles.row}>
            <span style={styles.label}>Expected Return</span>
            <span style={{
              ...styles.value,
              color: decision.expectedReturn >= 0 ? '#1F7A4D' : '#B42318'
            }}>
              {decision.expectedReturn >= 0 ? '+' : ''}{(decision.expectedReturn * 100).toFixed(1)}%
            </span>
          </div>

          <div style={styles.row}>
            <span style={styles.label}>Soft Stop</span>
            <span style={{ ...styles.value, color: '#C68A00' }}>
              {(decision.softStop * 100).toFixed(1)}%
            </span>
          </div>

          <div style={styles.row}>
            <span style={styles.label}>Tail Risk (P95)</span>
            <span style={{ ...styles.value, color: '#B42318' }}>
              {(decision.tailRisk * 100).toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Right: Edge Diagnostics */}
        <div style={styles.card}>
          <div style={styles.cardTitle}>Edge Diagnostics</div>
          
          <DiagnosticRow 
            label="Confidence" 
            value={diagnostics.confidence.value}
            status={diagnostics.confidence.status}
            threshold={diagnostics.confidence.threshold}
            format="percent"
          />
          
          <DiagnosticRow 
            label="Reliability" 
            value={diagnostics.reliability.value}
            status={diagnostics.reliability.status}
            threshold={diagnostics.reliability.threshold}
            format="percent"
          />
          
          <DiagnosticRow 
            label="Entropy" 
            value={diagnostics.entropy.value}
            status={diagnostics.entropy.status}
            threshold={diagnostics.entropy.threshold}
            format="percent"
            inverse
          />
          
          <DiagnosticRow 
            label="Stability" 
            value={diagnostics.stability.value}
            status={diagnostics.stability.status}
            threshold={diagnostics.stability.threshold}
            format="percent"
          />

          <div style={styles.edgeStatus}>
            <span style={styles.label}>Statistical Edge</span>
            <span style={{
              ...styles.value,
              color: edge.hasStatisticalEdge ? '#1F7A4D' : '#B42318'
            }}>
              {edge.hasStatisticalEdge ? '✓ VALID' : '✗ WEAK'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// PRESET SELECTOR COMPONENT
// ═══════════════════════════════════════════════════════════════

function PresetSelector({ value, onChange, loading }) {
  const presets = [
    { key: 'conservative', label: 'Conservative', color: '#3B82F6' },
    { key: 'balanced', label: 'Balanced', color: '#8B5CF6' },
    { key: 'aggressive', label: 'Aggressive', color: '#F59E0B' },
  ];

  return (
    <div style={styles.presetSelector}>
      {presets.map(p => (
        <button
          key={p.key}
          onClick={() => onChange(p.key)}
          disabled={loading}
          style={{
            ...styles.presetBtn,
            ...(value === p.key ? {
              backgroundColor: p.color,
              color: '#fff',
              borderColor: p.color,
            } : {})
          }}
        >
          {p.label}
        </button>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// DIAGNOSTIC ROW COMPONENT
// ═══════════════════════════════════════════════════════════════

function DiagnosticRow({ label, value, status, threshold, format, inverse }) {
  const displayValue = format === 'percent' 
    ? `${(value * 100).toFixed(1)}%`
    : value.toFixed(2);
    
  const thresholdDisplay = format === 'percent'
    ? `${(threshold * 100).toFixed(0)}%`
    : threshold.toFixed(2);

  const statusColor = getStatusColor(status);

  return (
    <div style={styles.diagnosticRow}>
      <span style={styles.label}>{label}</span>
      <div style={styles.diagnosticValue}>
        <span style={styles.value}>{displayValue}</span>
        <span style={styles.thresholdHint}>({inverse ? '≤' : '≥'}{thresholdDisplay})</span>
        <span style={{
          ...styles.statusDot,
          backgroundColor: statusColor
        }} />
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════

function getModeColor(mode) {
  switch (mode) {
    case 'FULL': return '#1F7A4D';
    case 'PARTIAL': return '#C68A00';
    case 'MICRO': return '#3B82F6';
    case 'NO_TRADE': return '#666666';
    default: return '#666666';
  }
}

function getEdgeColor(grade) {
  switch (grade) {
    case 'INSTITUTIONAL': return '#1F7A4D';
    case 'STRONG': return '#22C55E';
    case 'NEUTRAL': return '#C68A00';
    case 'WEAK': return '#B42318';
    default: return '#666666';
  }
}

function getRRColor(rr) {
  if (rr >= 2) return '#1F7A4D';
  if (rr >= 1) return '#C68A00';
  return '#B42318';
}

function getStatusColor(status) {
  switch (status) {
    case 'ok': return '#1F7A4D';
    case 'warn': return '#C68A00';
    case 'block': return '#B42318';
    default: return '#666666';
  }
}

// ═══════════════════════════════════════════════════════════════
// STYLES (Institutional, White Background)
// ═══════════════════════════════════════════════════════════════

const styles = {
  container: {
    backgroundColor: '#FFFFFF',
    border: '1px solid #EAEAEA',
    borderRadius: 12,
    padding: 20,
    marginTop: 20,
  },

  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    paddingBottom: 12,
    borderBottom: '1px solid #EAEAEA',
  },

  headerLeft: {
    display: 'flex',
    alignItems: 'baseline',
    gap: 8,
  },

  title: {
    fontSize: 14,
    fontWeight: 700,
    color: '#1a1a1a',
    letterSpacing: '0.5px',
  },

  version: {
    fontSize: 11,
    color: '#888',
  },

  presetSelector: {
    display: 'flex',
    gap: 4,
    padding: 3,
    backgroundColor: '#F5F5F5',
    borderRadius: 8,
  },

  presetBtn: {
    padding: '6px 14px',
    fontSize: 12,
    fontWeight: 600,
    border: '1px solid transparent',
    borderRadius: 6,
    backgroundColor: 'transparent',
    color: '#666',
    cursor: 'pointer',
    transition: 'all 0.15s ease',
  },

  presetSummary: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '8px 12px',
    marginBottom: 16,
    backgroundColor: '#FAFAFA',
    borderRadius: 6,
    fontSize: 11,
  },

  presetLabel: {
    fontWeight: 600,
    color: '#333',
  },

  presetDesc: {
    color: '#666',
  },

  presetThresholds: {
    marginLeft: 'auto',
    color: '#888',
    fontFamily: 'monospace',
    fontSize: 10,
  },

  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: 16,
  },

  card: {
    backgroundColor: '#FAFAFA',
    border: '1px solid #EAEAEA',
    borderRadius: 8,
    padding: 14,
  },

  cardTitle: {
    fontSize: 11,
    fontWeight: 600,
    color: '#666',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    marginBottom: 12,
  },

  row: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },

  diagnosticRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },

  diagnosticValue: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },

  thresholdHint: {
    fontSize: 9,
    color: '#999',
    fontFamily: 'monospace',
  },

  label: {
    fontSize: 12,
    color: '#666',
  },

  value: {
    fontSize: 12,
    fontWeight: 600,
    color: '#1a1a1a',
  },

  modeBadge: {
    padding: '2px 8px',
    borderRadius: 4,
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: 600,
  },

  blockers: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 4,
    marginTop: 8,
    marginBottom: 4,
  },

  blockerBadge: {
    padding: '2px 6px',
    backgroundColor: '#FEE2E2',
    color: '#B42318',
    borderRadius: 3,
    fontSize: 9,
    fontWeight: 600,
  },

  reason: {
    marginTop: 12,
    paddingTop: 10,
    borderTop: '1px solid #EAEAEA',
    fontSize: 11,
    color: '#888',
    fontStyle: 'italic',
  },

  statusDot: {
    width: 8,
    height: 8,
    borderRadius: '50%',
  },

  edgeStatus: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 12,
    paddingTop: 10,
    borderTop: '1px solid #EAEAEA',
  },

  loading: {
    padding: 40,
    textAlign: 'center',
    color: '#888',
    fontSize: 13,
  },

  error: {
    padding: 40,
    textAlign: 'center',
    color: '#B42318',
    fontSize: 13,
  },
};

