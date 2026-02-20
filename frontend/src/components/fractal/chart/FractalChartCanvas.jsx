import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { drawBackground } from "./layers/drawBackground";
import { drawGrid } from "./layers/drawGrid";
import { drawCandles } from "./layers/drawCandles";
import { drawSMA } from "./layers/drawSMA";
import { drawPhases } from "./layers/drawPhases";
import { drawForecast } from "./layers/drawForecast";
import { draw7dArrow } from "./layers/draw7dArrow";
import { drawHybridForecast } from "./layers/drawHybridForecast";
import { makeIndexXScale, makeYScale, paddedMinMax } from "./math/scale";
import { PhaseTooltip } from "./PhaseTooltip";

function Tooltip({ candle, sma, phase }) {
  const date = new Date(candle.t).toLocaleDateString();
  const up = candle.c >= candle.o;

  return (
    <div
      style={{
        position: "absolute",
        top: 12,
        right: 12,
        background: "#fff",
        border: "1px solid #e5e5e5",
        padding: "12px 14px",
        fontSize: 12,
        boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
        borderRadius: 8,
        minWidth: 140,
        zIndex: 10
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 6 }}>{date}</div>
      <div style={{ display: "grid", gap: 2 }}>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span style={{ color: "rgba(0,0,0,0.5)" }}>Open</span>
          <span>{candle.o.toLocaleString()}</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span style={{ color: "rgba(0,0,0,0.5)" }}>High</span>
          <span>{candle.h.toLocaleString()}</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span style={{ color: "rgba(0,0,0,0.5)" }}>Low</span>
          <span>{candle.l.toLocaleString()}</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span style={{ color: "rgba(0,0,0,0.5)" }}>Close</span>
          <span style={{ color: up ? "#22c55e" : "#ef4444", fontWeight: 600 }}>
            {candle.c.toLocaleString()}
          </span>
        </div>
        {sma && (
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span style={{ color: "rgba(0,0,0,0.5)" }}>SMA200</span>
            <span style={{ color: "#3b82f6" }}>{sma.toLocaleString()}</span>
          </div>
        )}
        {phase && (
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
            <span style={{ color: "rgba(0,0,0,0.5)" }}>Phase</span>
            <span style={{ fontWeight: 500 }}>{phase}</span>
          </div>
        )}
      </div>
    </div>
  );
}

export function FractalChartCanvas({ 
  chart, 
  forecast, 
  focus = '30d', 
  mode = 'price', 
  primaryMatch, 
  normalizedSeries, 
  width, 
  height,
  // BLOCK 73.5.2: Phase click callback
  onPhaseClick,
  selectedPhaseId
}) {
  const ref = useRef(null);
  const [hoverIndex, setHoverIndex] = useState(null);
  
  // BLOCK 73.5.1: Phase hover state
  const [hoveredPhase, setHoveredPhase] = useState(null);
  const [phaseTooltipPos, setPhaseTooltipPos] = useState({ x: 0, y: 0 });
  
  // BLOCK 73.1.1: Determine axis mode from backend normalizedSeries
  const renderMode = focus === '7d' ? 'CAPSULE_7D' : 'TRAJECTORY';
  const axisMode = normalizedSeries?.mode === 'PERCENT' ? 'PERCENT' : 'PRICE';
  const isPercentMode = axisMode === 'PERCENT';

  // Increased right margin for forecast zone (enough for full 30d + labels)
  const margins = useMemo(() => ({ left: 70, right: 320, top: 24, bottom: 36 }), []);
  
  // BLOCK 73.5.1: Phase zones from chart
  const phaseZones = useMemo(() => chart?.phaseZones || [], [chart]);
  const phaseStats = useMemo(() => chart?.phaseStats || [], [chart]);

  // Mouse handler

  // Mouse handler (BLOCK 73.5.1: Phase hover detection)
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !chart?.candles?.length) return;

    const handleMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;

      const plotW = width - margins.left - margins.right;
      const step = plotW / (chart.candles.length - 1);
      const index = Math.round((mx - margins.left) / step);

      if (index >= 0 && index < chart.candles.length) {
        setHoverIndex(index);
        
        // BLOCK 73.5.1: Detect phase under cursor
        const candle = chart.candles[index];
        const candleTs = candle.t;
        
        // Find phase zone containing this candle
        const zone = phaseZones.find(z => candleTs >= z.from && candleTs <= z.to);
        
        if (zone && phaseStats.length > 0) {
          // Find matching phase stats
          const stats = phaseStats.find(s => 
            s.from === new Date(zone.from).toISOString() || 
            new Date(s.from).getTime() === zone.from
          );
          
          if (stats) {
            setHoveredPhase(stats);
            setPhaseTooltipPos({ x: e.clientX, y: e.clientY });
          } else {
            setHoveredPhase(null);
          }
        } else {
          setHoveredPhase(null);
        }
      } else {
        setHoverIndex(null);
        setHoveredPhase(null);
      }
    };

    const handleLeave = () => {
      setHoverIndex(null);
      setHoveredPhase(null);
    };
    
    // BLOCK 73.5.2: Handle phase click
    const handleClick = (e) => {
      if (!onPhaseClick) return;
      
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const plotW = width - margins.left - margins.right;
      const step = plotW / (chart.candles.length - 1);
      const index = Math.round((mx - margins.left) / step);
      
      if (index >= 0 && index < chart.candles.length) {
        const candle = chart.candles[index];
        const candleTs = candle.t;
        
        // Find phase zone containing this candle
        const zone = phaseZones.find(z => candleTs >= z.from && candleTs <= z.to);
        
        if (zone && phaseStats.length > 0) {
          const stats = phaseStats.find(s => 
            s.from === new Date(zone.from).toISOString() || 
            new Date(s.from).getTime() === zone.from
          );
          
          if (stats) {
            // Toggle selection - if same phase clicked again, deselect
            if (selectedPhaseId === stats.phaseId) {
              onPhaseClick(null);
            } else {
              onPhaseClick(stats.phaseId, stats);
            }
          }
        }
      }
    };

    canvas.addEventListener("mousemove", handleMove);
    canvas.addEventListener("mouseleave", handleLeave);
    canvas.addEventListener("click", handleClick);

    return () => {
      canvas.removeEventListener("mousemove", handleMove);
      canvas.removeEventListener("mouseleave", handleLeave);
      canvas.removeEventListener("click", handleClick);
    };
  }, [chart, width, margins, phaseZones, phaseStats, onPhaseClick, selectedPhaseId]);

  // Render
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const dpr = Math.max(1, Math.floor(window.devicePixelRatio || 1));

    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    drawBackground(ctx, width, height);

    if (!chart?.candles?.length) {
      drawGrid(ctx, width, height, margins.left, margins.top, margins.right, margins.bottom);
      return;
    }

    const candles = chart.candles;
    const ts = candles.map(c => c.t);
    const currentPrice = candles[candles.length - 1]?.c || 0;

    // BLOCK 73.1.1: Y-scale depends on axis mode
    let minY, maxY, yScale;
    
    if (isPercentMode && normalizedSeries) {
      // PERCENT MODE: Use % range from backend
      minY = normalizedSeries.yRange?.minPercent ?? -50;
      maxY = normalizedSeries.yRange?.maxPercent ?? 50;
      
      // Add extra padding for visibility
      const range = maxY - minY;
      minY = Math.max(minY, -100); // Cap at -100%
      maxY = Math.min(maxY, 200);  // Cap at +200% for readability
      
    } else {
      // RAW PRICE MODE: Calculate from candles and forecast
      minY = Infinity;
      maxY = -Infinity;
      
      for (const c of candles) {
        if (c.l < minY) minY = c.l;
        if (c.h > maxY) maxY = c.h;
      }
      
      // Extend Y range to include forecast band
      if (forecast?.pricePath?.length) {
        for (let i = 0; i < forecast.pricePath.length; i++) {
          const upper = forecast.upperBand?.[i];
          const lower = forecast.lowerBand?.[i];
          if (upper && upper > maxY) maxY = upper;
          if (lower && lower < minY) minY = lower;
        }
        if (forecast.tailFloor && forecast.tailFloor < minY) {
          minY = forecast.tailFloor;
        }
      } else if (forecast?.points?.length) {
        for (const p of forecast.points) {
          if (p.lower < minY) minY = p.lower;
          if (p.upper > maxY) maxY = p.upper;
        }
        if (forecast.tailFloor && forecast.tailFloor < minY) {
          minY = forecast.tailFloor;
        }
      }
    }
    
    const mm = paddedMinMax(minY, maxY, 0.08);

    const { x, step, plotW } = makeIndexXScale(candles.length, margins.left, margins.right, width);
    
    // BLOCK 73.1.1: Create appropriate Y scale
    let y;
    if (isPercentMode) {
      // Y scale for percent values
      const { y: yPercent } = makeYScale(mm.minY, mm.maxY, margins.top, margins.bottom, height);
      // Wrapper that converts price to percent then maps
      y = (price) => {
        const pct = ((price / currentPrice) - 1) * 100;
        return yPercent(pct);
      };
      // Also expose percent scale directly
      y.percent = yPercent;
      y.isPercent = true;
      y.currentPrice = currentPrice;
    } else {
      const { y: yPrice } = makeYScale(mm.minY, mm.maxY, margins.top, margins.bottom, height);
      y = yPrice;
      y.isPercent = false;
    }

    // phases -> grid -> candles -> sma -> forecast
    drawPhases(ctx, chart.phaseZones, ts, x, margins.top, height, margins.bottom);
    drawGrid(ctx, width, height, margins.left, margins.top, margins.right, margins.bottom);
    drawCandles(ctx, candles, x, y, step, isPercentMode, currentPrice);
    drawSMA(ctx, chart.sma200, ts, x, y);

    // anchor at last candle x
    const xAnchor = x(candles.length - 1);
    
    // BLOCK 72.3: Choose forecast renderer based on focus and mode
    // BLOCK 73.3: Pass markers to hybrid renderer for 14D continuity
    if (mode === 'hybrid' && primaryMatch) {
      // Hybrid mode: draw both synthetic and replay
      drawHybridForecast(
        ctx,
        forecast,
        primaryMatch,
        xAnchor,
        y,
        plotW,
        margins.top,
        margins.bottom,
        height,
        forecast?.markers || [] // BLOCK 73.3: Pass markers for continuity
      );
    } else if (renderMode === 'CAPSULE_7D' && forecast?.distribution7d) {
      // 7D: Draw compact directional arrow + insight block
      draw7dArrow(
        ctx,
        forecast.distribution7d,
        forecast.currentPrice,
        xAnchor,
        y,
        margins.top,
        margins.bottom,
        height,
        forecast.stats || {}
      );
    } else {
      // 14D+: Draw aftermath-driven trajectory with fan
      drawForecast(ctx, forecast, xAnchor, y, plotW, margins.top, margins.bottom, height);
    }

    // Crosshair
    if (hoverIndex !== null && hoverIndex >= 0 && hoverIndex < candles.length) {
      const xi = x(hoverIndex);
      ctx.save();
      ctx.strokeStyle = "rgba(0,0,0,0.25)";
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(xi, margins.top);
      ctx.lineTo(xi, height - margins.bottom);
      ctx.stroke();
      ctx.restore();
    }

    // Y-axis labels
    ctx.save();
    ctx.fillStyle = "rgba(0,0,0,0.5)";
    ctx.font = "11px system-ui";
    const yTicks = 5;
    
    if (isPercentMode && y.percent) {
      // PERCENT MODE: Show % labels
      for (let i = 0; i <= yTicks; i++) {
        const pct = mm.minY + (i / yTicks) * (mm.maxY - mm.minY);
        const yPos = y.percent(pct);
        const label = pct >= 0 ? `+${pct.toFixed(0)}%` : `${pct.toFixed(0)}%`;
        ctx.fillText(label, 4, yPos + 4);
      }
      // Draw NOW reference line at 0%
      const nowY = y.percent(0);
      ctx.strokeStyle = 'rgba(34, 197, 94, 0.5)';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(margins.left, nowY);
      ctx.lineTo(width - margins.right, nowY);
      ctx.stroke();
      ctx.setLineDash([]);
      // NOW label
      ctx.fillStyle = '#22c55e';
      ctx.fillText('NOW', margins.left - 35, nowY + 4);
    } else {
      // PRICE MODE: Show $ labels
      for (let i = 0; i <= yTicks; i++) {
        const price = mm.minY + (i / yTicks) * (mm.maxY - mm.minY);
        const yPos = y(price);
        ctx.fillText(price.toLocaleString(undefined, { maximumFractionDigits: 0 }), 4, yPos + 4);
      }
    }
    ctx.restore();

  }, [chart, forecast, focus, mode, primaryMatch, normalizedSeries, isPercentMode, renderMode, width, height, margins, hoverIndex]);

  const hoverCandle = hoverIndex !== null && chart?.candles?.[hoverIndex];
  const hoverSma = hoverCandle && chart?.sma200?.find(s => s.t === hoverCandle.t)?.value;
  const hoverPhaseName = hoverCandle && chart?.phaseZones?.find(
    z => hoverCandle.t >= z.from && hoverCandle.t <= z.to
  )?.phase;

  return (
    <div style={{ position: "relative" }}>
      <canvas ref={ref} style={{ cursor: "crosshair" }} />
      {hoverCandle && (
        <Tooltip candle={hoverCandle} sma={hoverSma} phase={hoverPhaseName} />
      )}
      {/* BLOCK 73.5.1: Phase Tooltip */}
      <PhaseTooltip 
        phase={hoveredPhase}
        position={phaseTooltipPos}
        visible={!!hoveredPhase}
      />
    </div>
  );
}
