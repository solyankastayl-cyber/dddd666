/**
 * BLOCK 74.2 + 74.3 — Consensus Panel Component
 * 
 * Institutional consensus display with:
 * - Consensus Index (0-100)
 * - Conflict Level visualization
 * - BLOCK 74.3: Structural Dominance Lock indicator
 * - Vote breakdown by horizon
 * - Resolved decision (BUY/SELL/HOLD + mode + size)
 * - Adaptive meta information
 */

import React, { useState } from 'react';

const CONFLICT_COLORS = {
  NONE: { bg: '#dcfce7', text: '#166534', label: 'Aligned' },
  LOW: { bg: '#d1fae5', text: '#047857', label: 'Minor Conflict' },
  MODERATE: { bg: '#fef3c7', text: '#92400e', label: 'Moderate' },
  HIGH: { bg: '#fed7aa', text: '#c2410c', label: 'High Conflict' },
  SEVERE: { bg: '#fecaca', text: '#991b1b', label: 'Severe' },
  STRUCTURAL_LOCK: { bg: '#e0e7ff', text: '#3730a3', label: 'Structural Lock' },
};

const ACTION_COLORS = {
  BUY: { bg: '#dcfce7', text: '#166534' },
  SELL: { bg: '#fecaca', text: '#991b1b' },
  HOLD: { bg: '#f3f4f6', text: '#374151' },
};

const MODE_LABELS = {
  TREND_FOLLOW: 'Trend Follow',
  COUNTER_TREND: 'Counter-Trend',
  COUNTER_SIGNAL_BLOCKED: 'Counter Blocked',
  WAIT: 'Wait',
};

const DIRECTION_ICONS = {
  BULLISH: { symbol: '↑', color: '#16a34a' },
  BEARISH: { symbol: '↓', color: '#dc2626' },
  FLAT: { symbol: '→', color: '#6b7280' },
};

export function ConsensusPanel({ consensus74 }) {
  const [showDetails, setShowDetails] = useState(false);
  
  if (!consensus74) {
    return null;
  }
  
  const {
    consensusIndex,
    direction,
    conflictLevel,
    // BLOCK 74.3: Structural dominance fields
    dominance,
    structuralLock,
    timingOverrideBlocked,
    votes,
    conflictReasons,
    resolved,
    adaptiveMeta,
  } = consensus74;
  
  const conflictColor = CONFLICT_COLORS[conflictLevel] || CONFLICT_COLORS.MODERATE;
  const actionColor = ACTION_COLORS[resolved?.action] || ACTION_COLORS.HOLD;
  const dirIcon = DIRECTION_ICONS[direction] || DIRECTION_ICONS.FLAT;
  
  // Determine bias from consensus index
  const bias = consensusIndex > 60 ? 'BULLISH' : consensusIndex < 40 ? 'BEARISH' : 'NEUTRAL';
  const biasColor = bias === 'BULLISH' ? '#166534' : bias === 'BEARISH' ? '#dc2626' : '#6b7280';

  return (
    <div style={styles.container}>
      {/* Header with Structural Lock Indicator */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <span style={styles.title}>INSTITUTIONAL CONSENSUS</span>
          {/* BLOCK 74.3: Structural Dominance Badge */}
          {structuralLock && (
            <span style={styles.lockBadge} data-testid="structural-lock-badge">
              🔒 STRUCTURAL LOCK
            </span>
          )}
        </div>
        <span style={styles.regimeBadge}>
          {adaptiveMeta?.regime || 'NORMAL'}
        </span>
      </div>
      
      {/* BLOCK 74.3: Structural Dominance Alert */}
      {structuralLock && (
        <div style={styles.dominanceAlert} data-testid="dominance-alert">
          <span style={styles.alertIcon}>⚡</span>
          <span style={styles.alertText}>
            <strong>Structure ({adaptiveMeta?.structuralDirection})</strong> controls direction
            {timingOverrideBlocked && (
              <span style={styles.blockedText}> • Timing override blocked</span>
            )}
          </span>
        </div>
      )}
      
      {/* Main Metrics Row */}
      <div style={styles.metricsRow}>
        {/* Consensus Index */}
        <div style={styles.metricBlock}>
          <div style={styles.metricLabel}>Consensus Index</div>
          <div style={{
            ...styles.metricValue,
            color: biasColor,
          }}>
            {consensusIndex}
          </div>
          <div style={styles.metricSub}>
            <span style={{ color: biasColor }}>{bias}</span> BIAS
          </div>
        </div>
        
        {/* Conflict Level */}
        <div style={styles.metricBlock}>
          <div style={styles.metricLabel}>Conflict</div>
          <div style={{
            ...styles.conflictBadge,
            backgroundColor: conflictColor.bg,
            color: conflictColor.text,
          }}>
            {conflictColor.label}
          </div>
        </div>
        
        {/* Resolved Decision */}
        <div style={styles.metricBlock}>
          <div style={styles.metricLabel}>Resolved</div>
          <div style={{
            ...styles.actionBadge,
            backgroundColor: actionColor.bg,
            color: actionColor.text,
          }}>
            {resolved?.action || 'HOLD'}
          </div>
          <div style={styles.metricSub}>
            {MODE_LABELS[resolved?.mode] || 'Wait'} · {((resolved?.sizeMultiplier || 0) * 100).toFixed(0)}%
          </div>
        </div>
        
        {/* Dominant Tier */}
        <div style={styles.metricBlock}>
          <div style={styles.metricLabel}>Dominant</div>
          <div style={styles.tierBadge}>
            {resolved?.dominantTier || 'TACTICAL'}
          </div>
        </div>
      </div>
      
      {/* Expand/Collapse Button */}
      <button 
        style={styles.expandButton}
        onClick={() => setShowDetails(!showDetails)}
        data-testid="consensus-expand-btn"
      >
        {showDetails ? '▼ Hide Details' : '▶ Show Details'}
      </button>
      
      {/* Details Section */}
      {showDetails && (
        <div style={styles.detailsSection}>
          {/* Vote Breakdown */}
          <div style={styles.votesSection}>
            <div style={styles.sectionTitle}>Vote Breakdown</div>
            <div style={styles.votesGrid}>
              {votes?.map((vote) => (
                <div key={vote.horizon} style={styles.voteRow}>
                  <span style={styles.voteHorizon}>{vote.horizon}</span>
                  <span style={{
                    ...styles.voteDirection,
                    color: vote.direction === 'BULLISH' ? '#166534' : vote.direction === 'BEARISH' ? '#dc2626' : '#6b7280',
                  }}>
                    {vote.direction === 'BULLISH' ? '↑' : vote.direction === 'BEARISH' ? '↓' : '→'}
                  </span>
                  <div style={styles.voteBarContainer}>
                    <div style={{
                      ...styles.voteBar,
                      width: `${vote.weight * 100}%`,
                      backgroundColor: vote.contribution > 0 ? '#16a34a' : vote.contribution < 0 ? '#dc2626' : '#9ca3af',
                    }} />
                  </div>
                  <span style={styles.voteWeight}>{(vote.weight * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </div>
          
          {/* Conflict Reasons */}
          {conflictReasons && conflictReasons.length > 0 && (
            <div style={styles.reasonsSection}>
              <div style={styles.sectionTitle}>Conflict Analysis</div>
              <ul style={styles.reasonsList}>
                {conflictReasons.map((reason, i) => (
                  <li key={i} style={styles.reasonItem}>{reason}</li>
                ))}
              </ul>
            </div>
          )}
          
          {/* BLOCK 74.3: Tier Weight Breakdown */}
          <div style={styles.tierWeightsSection}>
            <div style={styles.sectionTitle}>Tier Weight Distribution</div>
            <div style={styles.tierWeightsGrid}>
              <div style={styles.tierWeightItem}>
                <div style={styles.tierWeightLabel}>STRUCTURE</div>
                <div style={styles.tierWeightBarContainer}>
                  <div style={{
                    ...styles.tierWeightBar,
                    width: `${(adaptiveMeta?.structureWeightSum || 0) * 100}%`,
                    backgroundColor: '#ef4444',
                  }} />
                </div>
                <span style={styles.tierWeightValue}>
                  {((adaptiveMeta?.structureWeightSum || 0) * 100).toFixed(0)}%
                </span>
                <span style={{
                  ...styles.tierDirection,
                  color: adaptiveMeta?.structuralDirection === 'BULLISH' ? '#16a34a' : 
                         adaptiveMeta?.structuralDirection === 'BEARISH' ? '#dc2626' : '#6b7280'
                }}>
                  {adaptiveMeta?.structuralDirection === 'BULLISH' ? '↑' : 
                   adaptiveMeta?.structuralDirection === 'BEARISH' ? '↓' : '→'}
                </span>
              </div>
              <div style={styles.tierWeightItem}>
                <div style={styles.tierWeightLabel}>TACTICAL</div>
                <div style={styles.tierWeightBarContainer}>
                  <div style={{
                    ...styles.tierWeightBar,
                    width: `${(adaptiveMeta?.tacticalWeightSum || 0) * 100}%`,
                    backgroundColor: '#8b5cf6',
                  }} />
                </div>
                <span style={styles.tierWeightValue}>
                  {((adaptiveMeta?.tacticalWeightSum || 0) * 100).toFixed(0)}%
                </span>
                <span style={{
                  ...styles.tierDirection,
                  color: adaptiveMeta?.tacticalDirection === 'BULLISH' ? '#16a34a' : 
                         adaptiveMeta?.tacticalDirection === 'BEARISH' ? '#dc2626' : '#6b7280'
                }}>
                  {adaptiveMeta?.tacticalDirection === 'BULLISH' ? '↑' : 
                   adaptiveMeta?.tacticalDirection === 'BEARISH' ? '↓' : '→'}
                </span>
              </div>
              <div style={styles.tierWeightItem}>
                <div style={styles.tierWeightLabel}>TIMING</div>
                <div style={styles.tierWeightBarContainer}>
                  <div style={{
                    ...styles.tierWeightBar,
                    width: `${(adaptiveMeta?.timingWeightSum || 0) * 100}%`,
                    backgroundColor: '#3b82f6',
                  }} />
                </div>
                <span style={styles.tierWeightValue}>
                  {((adaptiveMeta?.timingWeightSum || 0) * 100).toFixed(0)}%
                </span>
                <span style={{
                  ...styles.tierDirection,
                  color: adaptiveMeta?.timingDirection === 'BULLISH' ? '#16a34a' : 
                         adaptiveMeta?.timingDirection === 'BEARISH' ? '#dc2626' : '#6b7280'
                }}>
                  {adaptiveMeta?.timingDirection === 'BULLISH' ? '↑' : 
                   adaptiveMeta?.timingDirection === 'BEARISH' ? '↓' : '→'}
                </span>
              </div>
            </div>
          </div>
          
          {/* Adaptive Meta */}
          <div style={styles.metaSection}>
            <div style={styles.sectionTitle}>Adaptive Weighting 2.0</div>
            <div style={styles.metaGrid}>
              <div style={styles.metaItem}>
                <span style={styles.metaLabel}>Regime</span>
                <span style={styles.metaValue}>{adaptiveMeta?.regime || 'NORMAL'}</span>
              </div>
              <div style={styles.metaItem}>
                <span style={styles.metaLabel}>Dominance</span>
                <span style={{
                  ...styles.metaValue,
                  color: structuralLock ? '#3730a3' : '#374151',
                  fontWeight: structuralLock ? '700' : '600',
                }}>{dominance || 'TACTICAL'}</span>
              </div>
              <div style={styles.metaItem}>
                <span style={styles.metaLabel}>Struct Lock</span>
                <span style={{
                  ...styles.metaValue,
                  color: structuralLock ? '#3730a3' : '#6b7280',
                }}>{structuralLock ? 'ACTIVE' : 'OFF'}</span>
              </div>
              <div style={styles.metaItem}>
                <span style={styles.metaLabel}>Timing Block</span>
                <span style={{
                  ...styles.metaValue,
                  color: timingOverrideBlocked ? '#dc2626' : '#6b7280',
                }}>{timingOverrideBlocked ? 'BLOCKED' : 'NO'}</span>
              </div>
              <div style={styles.metaItem}>
                <span style={styles.metaLabel}>Div Penalties</span>
                <span style={styles.metaValue}>{adaptiveMeta?.divergencePenalties || 0}</span>
              </div>
              <div style={styles.metaItem}>
                <span style={styles.metaLabel}>Phase Penalties</span>
                <span style={styles.metaValue}>{adaptiveMeta?.phasePenalties || 0}</span>
              </div>
              {adaptiveMeta?.stabilityGuard && (
                <div style={{...styles.metaItem, gridColumn: 'span 2'}}>
                  <span style={{...styles.metaLabel, color: '#dc2626'}}>⚠ Stability Guard Active</span>
                </div>
              )}
            </div>
            {/* Regime Impact */}
            {adaptiveMeta?.weightAdjustments && (
              <div style={styles.regimeImpact}>
                <span style={styles.regimeImpactLabel}>Regime Impact:</span>
                <span style={styles.regimeImpactValues}>
                  Struct ×{adaptiveMeta.weightAdjustments.structureBoost?.toFixed(2)} | 
                  Tact ×{adaptiveMeta.weightAdjustments.tacticalBoost?.toFixed(2)} | 
                  Time ×{adaptiveMeta.weightAdjustments.timingClamp?.toFixed(2)}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    backgroundColor: '#ffffff',
    borderRadius: '12px',
    border: '1px solid #e5e7eb',
    padding: '16px',
    marginTop: '16px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  title: {
    fontSize: '12px',
    fontWeight: '600',
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  // BLOCK 74.3: Structural Lock Badge
  lockBadge: {
    fontSize: '10px',
    fontWeight: '700',
    padding: '4px 10px',
    borderRadius: '4px',
    backgroundColor: '#e0e7ff',
    color: '#3730a3',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  // BLOCK 74.3: Dominance Alert
  dominanceAlert: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '10px 14px',
    backgroundColor: '#eef2ff',
    borderRadius: '8px',
    border: '1px solid #c7d2fe',
    marginBottom: '16px',
  },
  alertIcon: {
    fontSize: '16px',
  },
  alertText: {
    fontSize: '12px',
    color: '#3730a3',
  },
  blockedText: {
    color: '#dc2626',
    fontWeight: '600',
  },
  regimeBadge: {
    fontSize: '10px',
    fontWeight: '700',
    padding: '3px 8px',
    borderRadius: '4px',
    backgroundColor: '#f3f4f6',
    color: '#374151',
  },
  metricsRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '16px',
    marginBottom: '16px',
  },
  metricBlock: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '4px',
  },
  metricLabel: {
    fontSize: '10px',
    color: '#9ca3af',
    textTransform: 'uppercase',
  },
  metricValue: {
    fontSize: '28px',
    fontWeight: '700',
    fontFamily: 'ui-monospace, monospace',
  },
  metricSub: {
    fontSize: '10px',
    color: '#6b7280',
  },
  conflictBadge: {
    fontSize: '12px',
    fontWeight: '600',
    padding: '6px 12px',
    borderRadius: '6px',
  },
  actionBadge: {
    fontSize: '14px',
    fontWeight: '700',
    padding: '8px 16px',
    borderRadius: '6px',
  },
  tierBadge: {
    fontSize: '11px',
    fontWeight: '600',
    padding: '4px 10px',
    borderRadius: '4px',
    backgroundColor: '#ede9fe',
    color: '#5b21b6',
  },
  expandButton: {
    width: '100%',
    padding: '8px',
    backgroundColor: '#f9fafb',
    border: '1px solid #e5e7eb',
    borderRadius: '6px',
    fontSize: '11px',
    color: '#6b7280',
    cursor: 'pointer',
    transition: 'background-color 0.15s',
  },
  detailsSection: {
    marginTop: '16px',
    paddingTop: '16px',
    borderTop: '1px solid #e5e7eb',
  },
  sectionTitle: {
    fontSize: '11px',
    fontWeight: '600',
    color: '#6b7280',
    textTransform: 'uppercase',
    marginBottom: '8px',
  },
  votesSection: {
    marginBottom: '16px',
  },
  votesGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  voteRow: {
    display: 'grid',
    gridTemplateColumns: '50px 24px 1fr 40px',
    gap: '8px',
    alignItems: 'center',
  },
  voteHorizon: {
    fontSize: '11px',
    fontWeight: '600',
    color: '#374151',
  },
  voteDirection: {
    fontSize: '14px',
    fontWeight: '700',
    textAlign: 'center',
  },
  voteBarContainer: {
    height: '8px',
    backgroundColor: '#f3f4f6',
    borderRadius: '4px',
    overflow: 'hidden',
  },
  voteBar: {
    height: '100%',
    borderRadius: '4px',
    transition: 'width 0.3s',
  },
  voteWeight: {
    fontSize: '10px',
    fontWeight: '600',
    color: '#6b7280',
    textAlign: 'right',
    fontFamily: 'ui-monospace, monospace',
  },
  reasonsSection: {
    marginBottom: '16px',
  },
  reasonsList: {
    margin: 0,
    paddingLeft: '16px',
  },
  reasonItem: {
    fontSize: '11px',
    color: '#6b7280',
    marginBottom: '4px',
  },
  // BLOCK 74.3: Tier Weight Distribution
  tierWeightsSection: {
    marginBottom: '16px',
  },
  tierWeightsGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  tierWeightItem: {
    display: 'grid',
    gridTemplateColumns: '70px 1fr 40px 24px',
    gap: '8px',
    alignItems: 'center',
  },
  tierWeightLabel: {
    fontSize: '10px',
    fontWeight: '600',
    color: '#6b7280',
  },
  tierWeightBarContainer: {
    height: '10px',
    backgroundColor: '#f3f4f6',
    borderRadius: '5px',
    overflow: 'hidden',
  },
  tierWeightBar: {
    height: '100%',
    borderRadius: '5px',
    transition: 'width 0.3s',
  },
  tierWeightValue: {
    fontSize: '11px',
    fontWeight: '600',
    color: '#374151',
    textAlign: 'right',
    fontFamily: 'ui-monospace, monospace',
  },
  tierDirection: {
    fontSize: '16px',
    fontWeight: '700',
    textAlign: 'center',
  },
  metaSection: {},
  metaGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '8px',
  },
  metaItem: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '6px 10px',
    backgroundColor: '#f9fafb',
    borderRadius: '4px',
  },
  metaLabel: {
    fontSize: '10px',
    color: '#6b7280',
  },
  metaValue: {
    fontSize: '10px',
    fontWeight: '600',
    color: '#374151',
  },
  // BLOCK 74.3: Regime Impact
  regimeImpact: {
    marginTop: '12px',
    padding: '8px 12px',
    backgroundColor: '#fef3c7',
    borderRadius: '6px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  regimeImpactLabel: {
    fontSize: '10px',
    fontWeight: '600',
    color: '#92400e',
  },
  regimeImpactValues: {
    fontSize: '10px',
    color: '#78350f',
    fontFamily: 'ui-monospace, monospace',
  },
};

export default ConsensusPanel;
