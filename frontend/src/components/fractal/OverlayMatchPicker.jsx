import React from "react";

export function OverlayMatchPicker({ matches, value, onChange }) {
  const top = matches.slice(0, 5);
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      {top.map((m, i) => {
        const active = i === value;
        return (
          <button
            key={m.id}
            onClick={() => onChange(i)}
            data-testid={`match-picker-${i}`}
            style={{
              padding: "8px 12px",
              border: active ? "2px solid #000" : "1px solid #e6e6e6",
              background: active ? "#000" : "#fff",
              color: active ? "#fff" : "#000",
              borderRadius: 10,
              cursor: "pointer",
              fontSize: 12,
              fontWeight: active ? 600 : 400,
              transition: "all 0.15s ease"
            }}
          >
            #{i + 1} {m.id} · {(m.similarity * 100).toFixed(0)}% · {m.phase}
          </button>
        );
      })}
    </div>
  );
}
