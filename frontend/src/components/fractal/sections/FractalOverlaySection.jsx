import React, { useEffect, useMemo, useState } from "react";
import { useFractalOverlay } from "../hooks/useFractalOverlay";
import { selectDefaultMatchIndex } from "../utils/selectDefaultMatch";
import { OverlayCanvas } from "../OverlayCanvas";
import { OverlayMatchPicker } from "../OverlayMatchPicker";

export function FractalOverlaySection({ symbol }) {
  const { data, loading, err } = useFractalOverlay(symbol);
  const [matchIndex, setMatchIndex] = useState(0);

  const defaultIdx = useMemo(() => selectDefaultMatchIndex(data), [data]);

  useEffect(() => {
    setMatchIndex(defaultIdx);
  }, [defaultIdx]);

  const match = data?.matches?.[matchIndex];

  return (
    <div data-testid="fractal-overlay-section" style={{ display: "grid", gridTemplateColumns: "1.4fr 0.6fr", gap: 18 }}>
      {/* Left: Canvas */}
      <div style={{ border: "1px solid #eee", borderRadius: 14, padding: 16, background: "#fff" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 12 }}>
          <div style={{ fontSize: 15, fontWeight: 700 }}>Fractal Overlay</div>
          <div style={{ fontSize: 12, color: "rgba(0,0,0,0.5)" }}>
            1D · window=60 · aftermath=30
          </div>
        </div>

        <div>
          <OverlayCanvas data={data} matchIndex={matchIndex} width={680} height={340} />
        </div>

        <div style={{ marginTop: 14 }}>
          {data?.matches?.length ? (
            <OverlayMatchPicker
              matches={data.matches.map((m) => ({ id: m.id, similarity: m.similarity, phase: m.phase }))}
              value={matchIndex}
              onChange={setMatchIndex}
            />
          ) : (
            <div style={{ fontSize: 12, color: "rgba(0,0,0,0.55)" }}>
              {loading ? "Loading…" : err ? `Error: ${err}` : "No matches"}
            </div>
          )}
        </div>
      </div>

      {/* Right: Metrics */}
      <div style={{ border: "1px solid #eee", borderRadius: 14, padding: 16, background: "#fff" }}>
        <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 12 }}>Match Metrics</div>

        {!match ? (
          <div style={{ fontSize: 12, color: "rgba(0,0,0,0.55)" }}>
            {loading ? "Loading…" : err ? `Error: ${err}` : "Select a match"}
          </div>
        ) : (
          <div style={{ display: "grid", gap: 10 }}>
            <Row k="Match ID" v={match.id} />
            <Row k="Phase" v={match.phase} highlight />
            <Row k="Similarity" v={`${(match.similarity * 100).toFixed(1)}%`} />
            <Row k="Volatility Match" v={fmtPct(match.volatilityMatch)} />
            <Row k="Drawdown Shape" v={fmtPct(match.drawdownShape)} />
            <Row k="Stability (PSS)" v={fmtPct(match.stability)} />

            <hr style={{ border: 0, borderTop: "1px solid #eee", margin: "6px 0" }} />

            <Row k="Return 7d" v={fmtSignedPct(match.return7d)} color={getReturnColor(match.return7d)} />
            <Row k="Return 14d" v={fmtSignedPct(match.return14d)} color={getReturnColor(match.return14d)} />
            <Row k="Return 30d" v={fmtSignedPct(match.return30d)} color={getReturnColor(match.return30d)} />

            <hr style={{ border: 0, borderTop: "1px solid #eee", margin: "6px 0" }} />

            <Row k="Max Drawdown" v={fmtSignedPct(match.maxDrawdown)} color="#ef4444" />
            <Row k="Max Excursion" v={fmtSignedPct(match.maxExcursion)} color="#22c55e" />

            <div style={{ marginTop: 10, fontSize: 11, color: "rgba(0,0,0,0.45)", lineHeight: 1.5 }}>
              — Current (solid) · History/Aftermath (dashed) · Fan = P10–P90
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Row({ k, v, highlight, color }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
      <div style={{ fontSize: 12, color: "rgba(0,0,0,0.55)" }}>{k}</div>
      <div style={{ 
        fontSize: 12, 
        fontWeight: highlight ? 700 : 600,
        color: color || (highlight ? "#000" : "inherit")
      }}>{v}</div>
    </div>
  );
}

function fmtPct(x) {
  if (x == null || Number.isNaN(x)) return "—";
  return `${(x * 100).toFixed(0)}%`;
}

function fmtSignedPct(x) {
  if (x == null || Number.isNaN(x)) return "—";
  const s = x >= 0 ? "+" : "";
  return `${s}${(x * 100).toFixed(1)}%`;
}

function getReturnColor(x) {
  if (x == null) return undefined;
  return x >= 0 ? "#22c55e" : "#ef4444";
}
