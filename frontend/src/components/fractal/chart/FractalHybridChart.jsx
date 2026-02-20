import React, { useEffect, useMemo, useState, useCallback } from "react";
import { FractalChartCanvas } from "./FractalChartCanvas";

/**
 * STEP A — Hybrid Projection Chart (MVP)
 * BLOCK 73.4 — Interactive Match Replay
 * BLOCK 73.5.2 — Phase Click Drilldown
 * 
 * Shows both projections on same chart:
 * - Synthetic (green) - model forecast
 * - Replay (purple) - selected historical match aftermath
 * 
 * User can click on match chips to switch replay line
 * User can click on phase zones to filter matches by phase type
 */

export function FractalHybridChart({ 
  symbol = "BTC", 
  width = 1100, 
  height = 420,
  focus = '30d',
  focusPack = null,
  // BLOCK 73.5.2: Callback to refetch focusPack with phaseId
  onPhaseFilter
}) {
  const [chart, setChart] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // BLOCK 73.4: Selected match state
  const [selectedMatchId, setSelectedMatchId] = useState(null);
  const [customReplayPack, setCustomReplayPack] = useState(null);
  const [replayLoading, setReplayLoading] = useState(false);
  
  // BLOCK 73.5.2: Selected phase state
  const [selectedPhaseId, setSelectedPhaseId] = useState(null);
  const [selectedPhaseStats, setSelectedPhaseStats] = useState(null);

  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  // Fetch chart data (candles, sma200, phases)
  useEffect(() => {
    let alive = true;
    setLoading(true);

    fetch(`${API_URL}/api/fractal/v2.1/chart?symbol=${symbol}&limit=365`)
      .then(r => r.json())
      .then(chartData => {
        if (alive) {
          setChart(chartData);
          setLoading(false);
        }
      })
      .catch(() => {
        if (alive) setLoading(false);
      });

    return () => { alive = false; };
  }, [symbol, API_URL]);
  
  // Reset selection when focus changes
  useEffect(() => {
    setSelectedMatchId(null);
    setCustomReplayPack(null);
    setSelectedPhaseId(null);
    setSelectedPhaseStats(null);
  }, [focus]);
  
  // BLOCK 73.5.2: Handle phase click drilldown
  const handlePhaseClick = useCallback((phaseId, phaseStats) => {
    console.log('[PhaseClick]', phaseId, phaseStats);
    
    if (!phaseId) {
      // Clear phase filter
      setSelectedPhaseId(null);
      setSelectedPhaseStats(null);
      if (onPhaseFilter) {
        onPhaseFilter(null);
      }
      return;
    }
    
    setSelectedPhaseId(phaseId);
    setSelectedPhaseStats(phaseStats);
    
    // Notify parent to refetch focusPack with phaseId filter
    if (onPhaseFilter) {
      onPhaseFilter(phaseId);
    }
  }, [onPhaseFilter]);
  
  // BLOCK 73.4: Fetch replay pack when user selects a match
  const handleMatchSelect = useCallback(async (matchId) => {
    if (!matchId || matchId === selectedMatchId) return;
    
    setSelectedMatchId(matchId);
    setReplayLoading(true);
    
    try {
      const res = await fetch(`${API_URL}/api/fractal/v2.1/replay-pack?symbol=${symbol}&focus=${focus}&matchId=${matchId}`);
      const data = await res.json();
      
      if (data.ok && data.replayPack) {
        setCustomReplayPack(data.replayPack);
      }
    } catch (err) {
      console.error('[ReplayPack] Fetch error:', err);
    } finally {
      setReplayLoading(false);
    }
  }, [API_URL, symbol, focus, selectedMatchId]);

  // Build forecast from focusPack
  const forecast = useMemo(() => {
    const candles = chart?.candles;
    if (!candles?.length) return null;
    if (!focusPack?.forecast) return null;

    const currentPrice = candles[candles.length - 1].c;
    const fp = focusPack.forecast;
    const meta = focusPack.meta;
    const overlay = focusPack.overlay;
    
    const aftermathDays = meta?.aftermathDays || 30;
    const markers = fp.markers || [];
    
    // Get distribution series
    const distributionSeries = overlay?.distributionSeries || {};
    const lastIdx = (distributionSeries.p50?.length || 1) - 1;
    const distribution7d = {
      p10: distributionSeries.p10?.[lastIdx] ?? -0.15,
      p25: distributionSeries.p25?.[lastIdx] ?? -0.05,
      p50: distributionSeries.p50?.[lastIdx] ?? 0,
      p75: distributionSeries.p75?.[lastIdx] ?? 0.05,
      p90: distributionSeries.p90?.[lastIdx] ?? 0.15,
    };
    
    return {
      pricePath: fp.path || [],
      upperBand: fp.upperBand || [],
      lowerBand: fp.lowerBand || [],
      tailFloor: fp.tailFloor,
      confidenceDecay: fp.confidenceDecay || [],
      markers: markers.map(m => ({
        day: m.dayIndex + 1,
        horizon: m.horizon,
        price: m.price,
        expectedReturn: m.expectedReturn
      })),
      aftermathDays,
      currentPrice,
      distribution7d,
      stats: overlay?.stats || {}
    };
  }, [chart, focusPack]);
  
  // Get primary replay match - BLOCK 73.1: Use weighted primaryMatch
  // BLOCK 73.4: Override with custom replay pack if selected
  const primaryMatch = useMemo(() => {
    if (!chart?.candles?.length) return null;
    
    const currentPrice = chart.candles[chart.candles.length - 1].c;
    
    // BLOCK 73.4: Use custom replay pack if user selected a match
    if (customReplayPack) {
      return {
        id: customReplayPack.matchId,
        date: customReplayPack.matchMeta.date,
        similarity: customReplayPack.matchMeta.similarity,
        phase: customReplayPack.matchMeta.phase,
        replayPath: customReplayPack.replayPath.slice(1).map(p => p.price), // Skip t=0
        selectionScore: customReplayPack.matchMeta.score / 100,
        selectionReason: 'User selected',
        // Custom divergence for this match
        customDivergence: customReplayPack.divergence
      };
    }
    
    // BLOCK 73.1: Prefer primarySelection.primaryMatch from backend
    const match = focusPack?.primarySelection?.primaryMatch 
      || focusPack?.overlay?.matches?.[0]; // Fallback for backward compat
    
    if (!match?.aftermathNormalized?.length) return null;
    
    // Convert normalized aftermath to price series
    const replayPath = match.aftermathNormalized.map(r => currentPrice * (1 + r));
    
    return {
      id: match.id,
      date: match.date,
      similarity: match.similarity || 0.75,
      phase: match.phase,
      replayPath,
      // BLOCK 73.1: Include selection metadata
      selectionScore: match.selectionScore,
      selectionReason: match.selectionReason,
      scores: match.scores,
      // For future divergence calculation
      returns: match.aftermathNormalized
    };
  }, [focusPack, chart, customReplayPack]);
  
  // BLOCK 73.4: Get divergence - use custom if available
  const activeDivergence = useMemo(() => {
    if (customReplayPack?.divergence) {
      return customReplayPack.divergence;
    }
    return focusPack?.divergence;
  }, [focusPack, customReplayPack]);
  
  // BLOCK 73.5.2: Get phase filter info from focusPack
  const phaseFilter = focusPack?.phaseFilter;

  if (loading || !chart?.candles) {
    return (
      <div style={{ width, height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: '#888' }}>Loading hybrid projection...</div>
      </div>
    );
  }

  const currentPrice = chart.candles[chart.candles.length - 1].c || 0;
  const matches = focusPack?.overlay?.matches || [];
  const primaryMatchId = focusPack?.primarySelection?.primaryMatch?.id || matches[0]?.id;

  return (
    <div style={{ width, background: "#fff", borderRadius: 12, overflow: "hidden" }}>
      {/* BLOCK 73.5.2: Phase Filter Indicator */}
      {phaseFilter?.active && (
        <PhaseFilterBar 
          phaseFilter={phaseFilter}
          phaseStats={selectedPhaseStats}
          onClear={() => handlePhaseClick(null)}
        />
      )}
      
      {/* Chart Canvas with hybrid mode */}
      <FractalChartCanvas 
        chart={chart} 
        forecast={forecast} 
        focus={focus}
        mode="hybrid"
        primaryMatch={primaryMatch}
        normalizedSeries={focusPack?.normalizedSeries}
        width={width} 
        height={height}
        // BLOCK 73.5.2: Phase click handler
        onPhaseClick={handlePhaseClick}
        selectedPhaseId={selectedPhaseId}
      />
      
      {/* BLOCK 73.4: Interactive Match Picker */}
      {matches.length > 1 && (
        <MatchPicker 
          matches={matches}
          selectedId={selectedMatchId || primaryMatchId}
          primaryId={primaryMatchId}
          onSelect={handleMatchSelect}
          loading={replayLoading}
        />
      )}
      
      {/* Hybrid Summary Panel */}
      <HybridSummaryPanel 
        forecast={forecast}
        primaryMatch={primaryMatch}
        currentPrice={currentPrice}
        focus={focus}
        divergence={activeDivergence}
      />
    </div>
  );
}

/**
 * BLOCK 73.2 — Hybrid Summary Panel with Divergence Engine
 * 
 * Shows: Synthetic, Replay, and full Divergence metrics from backend
 */
function HybridSummaryPanel({ forecast, primaryMatch, currentPrice, focus, divergence }) {
  if (!forecast || !currentPrice) return null;
  
  const syntheticReturn = forecast.pricePath?.length 
    ? ((forecast.pricePath[forecast.pricePath.length - 1] - currentPrice) / currentPrice * 100)
    : 0;
    
  const replayReturn = primaryMatch?.replayPath?.length
    ? ((primaryMatch.replayPath[primaryMatch.replayPath.length - 1] - currentPrice) / currentPrice * 100)
    : null;
  
  // Use backend divergence metrics if available
  const div = divergence || {};
  const score = div.score ?? null;
  const grade = div.grade ?? 'N/A';
  const flags = div.flags ?? [];
  
  // Grade colors
  const gradeColors = {
    'A': '#22c55e',
    'B': '#84cc16',
    'C': '#f59e0b',
    'D': '#f97316',
    'F': '#ef4444',
    'N/A': '#888',
  };
  
  const gradeColor = gradeColors[grade] || '#888';
  
  // Has warnings?
  const hasWarnings = flags.length > 0 && !flags.includes('PERFECT_MATCH');

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.title}>HYBRID PROJECTION</span>
        <span style={styles.subtitle}>{focus.toUpperCase()} Horizon</span>
        {/* Grade badge */}
        {score !== null && (
          <span style={{
            ...styles.gradeBadge,
            backgroundColor: gradeColor,
          }}>
            {grade} ({score})
          </span>
        )}
      </div>
      
      <div style={styles.grid}>
        {/* Synthetic Column */}
        <div style={styles.column}>
          <div style={styles.columnHeader}>
            <span style={{ ...styles.dot, backgroundColor: '#22c55e' }}></span>
            SYNTHETIC
          </div>
          <div style={{ ...styles.value, color: syntheticReturn >= 0 ? '#22c55e' : '#ef4444' }}>
            {syntheticReturn >= 0 ? '+' : ''}{syntheticReturn.toFixed(1)}%
          </div>
          <div style={styles.label}>Model Projection</div>
        </div>
        
        {/* Replay Column */}
        <div style={styles.column}>
          <div style={styles.columnHeader}>
            <span style={{ ...styles.dot, backgroundColor: '#8b5cf6' }}></span>
            REPLAY
          </div>
          {replayReturn !== null ? (
            <>
              <div style={{ ...styles.value, color: replayReturn >= 0 ? '#22c55e' : '#ef4444' }}>
                {replayReturn >= 0 ? '+' : ''}{replayReturn.toFixed(1)}%
              </div>
              <div style={styles.label}>
                {primaryMatch?.id || 'Historical'} ({primaryMatch?.selectionScore 
                  ? (primaryMatch.selectionScore * 100).toFixed(0) 
                  : (primaryMatch?.similarity ? (primaryMatch.similarity * 100).toFixed(0) : '—')}% match)
              </div>
            </>
          ) : (
            <div style={styles.noData}>No replay data</div>
          )}
        </div>
        
        {/* Divergence Column - Now from backend */}
        <div style={styles.column}>
          <div style={styles.columnHeader}>DIVERGENCE</div>
          <div style={{ ...styles.value, color: gradeColor }}>
            {div.rmse != null ? `${div.rmse.toFixed(1)}%` : '—'}
          </div>
          <div style={{ ...styles.label, color: gradeColor }}>
            RMSE
          </div>
        </div>
      </div>
      
      {/* BLOCK 73.2: Detailed Divergence Metrics */}
      {divergence && (
        <DivergenceDetails divergence={divergence} hasWarnings={hasWarnings} />
      )}
    </div>
  );
}

/**
 * Detailed divergence metrics panel
 */
function DivergenceDetails({ divergence, hasWarnings }) {
  const { rmse, mape, corr, terminalDelta, directionalMismatch, flags, samplePoints } = divergence;
  
  return (
    <div style={styles.detailsContainer}>
      <div style={styles.detailsGrid}>
        <MetricItem label="Correlation" value={corr?.toFixed(2)} warning={corr < 0.3} />
        <MetricItem label="Terminal Δ" value={`${terminalDelta >= 0 ? '+' : ''}${terminalDelta?.toFixed(1)}%`} warning={Math.abs(terminalDelta) > 20} />
        <MetricItem label="Dir Mismatch" value={`${directionalMismatch?.toFixed(0)}%`} warning={directionalMismatch > 55} />
        <MetricItem label="Sample" value={samplePoints} />
      </div>
      
      {/* Warning flags */}
      {hasWarnings && flags.length > 0 && (
        <div style={styles.flagsRow}>
          {flags.filter(f => f !== 'PERFECT_MATCH').map((flag, i) => (
            <span key={i} style={styles.flag}>
              {formatFlag(flag)}
            </span>
          ))}
        </div>
      )}
      
      {/* Perfect match indicator */}
      {flags.includes('PERFECT_MATCH') && (
        <div style={styles.perfectMatch}>
          ✓ PERFECT ALIGNMENT
        </div>
      )}
    </div>
  );
}

function MetricItem({ label, value, warning }) {
  return (
    <div style={styles.metricItem}>
      <span style={styles.metricLabel}>{label}</span>
      <span style={{ ...styles.metricValue, color: warning ? '#f59e0b' : '#444' }}>
        {value ?? '—'}
      </span>
    </div>
  );
}

function formatFlag(flag) {
  const labels = {
    'HIGH_DIVERGENCE': 'High Divergence',
    'LOW_CORR': 'Low Correlation',
    'TERM_DRIFT': 'Terminal Drift',
    'DIR_MISMATCH': 'Direction Mismatch',
  };
  return labels[flag] || flag;
}

const styles = {
  container: {
    backgroundColor: '#FAFAFA',
    border: '1px solid #EAEAEA',
    borderRadius: 8,
    padding: '12px 16px',
    marginTop: 8,
  },
  header: {
    display: 'flex',
    alignItems: 'baseline',
    gap: 8,
    marginBottom: 12,
    paddingBottom: 8,
    borderBottom: '1px solid #EAEAEA',
  },
  title: {
    fontSize: 11,
    fontWeight: 700,
    color: '#444',
    letterSpacing: '0.5px',
  },
  subtitle: {
    fontSize: 10,
    color: '#888',
  },
  gradeBadge: {
    marginLeft: 'auto',
    padding: '2px 8px',
    borderRadius: 4,
    fontSize: 10,
    fontWeight: 700,
    color: '#fff',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr 1fr',
    gap: 16,
  },
  column: {
    textAlign: 'center',
  },
  columnHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    fontSize: 10,
    fontWeight: 600,
    color: '#666',
    marginBottom: 6,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: '50%',
  },
  value: {
    fontSize: 18,
    fontWeight: 700,
    fontFamily: 'monospace',
  },
  label: {
    fontSize: 10,
    color: '#888',
    marginTop: 2,
  },
  noData: {
    fontSize: 12,
    color: '#aaa',
    fontStyle: 'italic',
  },
  // BLOCK 73.2: Details styles
  detailsContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTop: '1px solid #EAEAEA',
  },
  detailsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: 8,
  },
  metricItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 2,
  },
  metricLabel: {
    fontSize: 9,
    color: '#888',
    textTransform: 'uppercase',
  },
  metricValue: {
    fontSize: 12,
    fontWeight: 600,
    fontFamily: 'monospace',
  },
  flagsRow: {
    display: 'flex',
    gap: 6,
    marginTop: 10,
    flexWrap: 'wrap',
  },
  flag: {
    padding: '3px 8px',
    backgroundColor: '#fef3c7',
    border: '1px solid #f59e0b',
    borderRadius: 4,
    fontSize: 9,
    fontWeight: 600,
    color: '#b45309',
  },
  perfectMatch: {
    marginTop: 10,
    padding: '4px 12px',
    backgroundColor: '#dcfce7',
    border: '1px solid #22c55e',
    borderRadius: 4,
    fontSize: 10,
    fontWeight: 600,
    color: '#166534',
    textAlign: 'center',
  },
};

/**
 * BLOCK 73.4 — Interactive Match Picker
 * 
 * Shows top matches as clickable chips.
 * Clicking switches the replay line and recalculates divergence.
 */
function MatchPicker({ matches, selectedId, primaryId, onSelect, loading }) {
  const topMatches = matches.slice(0, 5);
  
  return (
    <div style={matchPickerStyles.container}>
      <div style={matchPickerStyles.label}>
        <span style={matchPickerStyles.labelText}>SELECT REPLAY</span>
        {loading && <span style={matchPickerStyles.loading}>Loading...</span>}
      </div>
      <div style={matchPickerStyles.chips}>
        {topMatches.map((match, idx) => {
          const isSelected = match.id === selectedId;
          const isPrimary = match.id === primaryId;
          
          return (
            <button
              key={match.id}
              data-testid={`match-chip-${idx}`}
              onClick={() => onSelect(match.id)}
              style={{
                ...matchPickerStyles.chip,
                backgroundColor: isSelected ? '#000' : (isPrimary ? '#f0fdf4' : '#fff'),
                color: isSelected ? '#fff' : '#000',
                borderColor: isSelected ? '#000' : (isPrimary ? '#22c55e' : '#e6e6e6'),
                fontWeight: isSelected ? 600 : 400,
              }}
            >
              <span style={matchPickerStyles.chipRank}>#{idx + 1}</span>
              <span style={matchPickerStyles.chipDate}>{match.id}</span>
              <span style={{
                ...matchPickerStyles.chipSim,
                color: isSelected ? 'rgba(255,255,255,0.7)' : '#888'
              }}>
                {(match.similarity * 100).toFixed(0)}%
              </span>
              <span style={{
                ...matchPickerStyles.chipPhase,
                backgroundColor: isSelected ? 'rgba(255,255,255,0.2)' : getPhaseColor(match.phase),
                color: isSelected ? '#fff' : getPhaseTextColor(match.phase),
              }}>
                {match.phase.slice(0, 3).toUpperCase()}
              </span>
              {isPrimary && !isSelected && (
                <span style={matchPickerStyles.primaryBadge}>AUTO</span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function getPhaseColor(phase) {
  const colors = {
    'ACCUMULATION': '#dcfce7',
    'RECOVERY': '#cffafe',
    'DISTRIBUTION': '#fef3c7',
    'MARKDOWN': '#fce7f3',
  };
  return colors[phase] || '#f4f4f5';
}

function getPhaseTextColor(phase) {
  const colors = {
    'ACCUMULATION': '#166534',
    'RECOVERY': '#0891b2',
    'DISTRIBUTION': '#b45309',
    'MARKDOWN': '#9d174d',
  };
  return colors[phase] || '#444';
}

const matchPickerStyles = {
  container: {
    padding: '12px 16px',
    borderTop: '1px solid #EAEAEA',
    backgroundColor: '#FAFAFA',
  },
  label: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  labelText: {
    fontSize: 10,
    fontWeight: 600,
    color: '#888',
    letterSpacing: '0.5px',
  },
  loading: {
    fontSize: 10,
    color: '#8b5cf6',
    fontStyle: 'italic',
  },
  chips: {
    display: 'flex',
    gap: 8,
    flexWrap: 'wrap',
  },
  chip: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    padding: '6px 10px',
    border: '1px solid',
    borderRadius: 8,
    cursor: 'pointer',
    fontSize: 11,
    transition: 'all 0.15s ease',
    position: 'relative',
  },
  chipRank: {
    fontWeight: 700,
    fontSize: 10,
  },
  chipDate: {
    fontFamily: 'monospace',
    fontSize: 10,
  },
  chipSim: {
    fontSize: 10,
  },
  chipPhase: {
    fontSize: 8,
    padding: '2px 4px',
    borderRadius: 3,
    fontWeight: 600,
  },
  primaryBadge: {
    position: 'absolute',
    top: -6,
    right: -4,
    fontSize: 7,
    padding: '1px 4px',
    backgroundColor: '#22c55e',
    color: '#fff',
    borderRadius: 3,
    fontWeight: 700,
  },
};

/**
 * BLOCK 73.5.2 — Phase Filter Bar
 * 
 * Shows when a phase is selected (clicked).
 * Displays phase context and clear button.
 */
function PhaseFilterBar({ phaseFilter, phaseStats, onClear }) {
  if (!phaseFilter?.active) return null;
  
  const phaseColors = {
    'ACCUMULATION': { bg: '#dcfce7', border: '#22c55e', text: '#166534' },
    'MARKUP': { bg: '#dbeafe', border: '#3b82f6', text: '#1d4ed8' },
    'DISTRIBUTION': { bg: '#fef3c7', border: '#f59e0b', text: '#b45309' },
    'MARKDOWN': { bg: '#fce7f3', border: '#ec4899', text: '#9d174d' },
    'RECOVERY': { bg: '#cffafe', border: '#06b6d4', text: '#0891b2' },
    'CAPITULATION': { bg: '#fee2e2', border: '#ef4444', text: '#dc2626' },
  };
  
  const colors = phaseColors[phaseFilter.phaseType] || { bg: '#f4f4f5', border: '#a1a1aa', text: '#52525b' };
  
  return (
    <div 
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '10px 16px',
        backgroundColor: colors.bg,
        borderBottom: `2px solid ${colors.border}`,
      }}
      data-testid="phase-filter-bar"
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{
          backgroundColor: colors.border,
          color: '#fff',
          padding: '4px 10px',
          borderRadius: 4,
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: '0.5px',
        }}>
          {phaseFilter.phaseType}
        </span>
        <span style={{ fontSize: 12, color: colors.text }}>
          Phase Filter Active
        </span>
        <span style={{ fontSize: 11, color: '#666' }}>
          {phaseFilter.filteredMatchCount} matches in this phase type
        </span>
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {phaseStats && (
          <span style={{ fontSize: 11, color: '#666' }}>
            Return: <span style={{ 
              fontWeight: 600, 
              color: phaseStats.phaseReturnPct >= 0 ? '#16a34a' : '#dc2626' 
            }}>
              {phaseStats.phaseReturnPct >= 0 ? '+' : ''}{phaseStats.phaseReturnPct?.toFixed(1)}%
            </span>
            {' | '}
            Duration: {phaseStats.durationDays}d
          </span>
        )}
        <button
          onClick={onClear}
          data-testid="clear-phase-filter"
          style={{
            padding: '4px 12px',
            backgroundColor: '#fff',
            border: '1px solid #d4d4d4',
            borderRadius: 6,
            fontSize: 11,
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
          onMouseOver={(e) => { e.target.style.backgroundColor = '#f5f5f5'; }}
          onMouseOut={(e) => { e.target.style.backgroundColor = '#fff'; }}
        >
          Clear Filter
        </button>
      </div>
    </div>
  );
}

export default FractalHybridChart;
