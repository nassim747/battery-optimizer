import React from "react";
import type { Summary } from "../types";

const s: Record<string, React.CSSProperties> = {
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
    gap: "12px",
    marginBottom: "24px",
  },
  card: {
    background: "#1e293b",
    borderRadius: "12px",
    padding: "16px 20px",
    border: "1px solid #334155",
  },
  label: {
    fontSize: "11px",
    fontWeight: 600,
    textTransform: "uppercase" as const,
    letterSpacing: "0.08em",
    color: "#64748b",
    marginBottom: "6px",
  },
  value: { fontSize: "22px", fontWeight: 700, color: "#f1f5f9" },
  savings: { fontSize: "22px", fontWeight: 700, color: "#22c55e" },
  sub: { fontSize: "11px", color: "#64748b", marginTop: "3px" },
};

interface Props {
  summary: Summary;
}

export default function SummaryCard({ summary }: Props) {
  const pct =
    summary.total_cost_before > 0
      ? ((summary.savings / summary.total_cost_before) * 100).toFixed(1)
      : "0.0";

  return (
    <div style={s.grid}>
      <div style={s.card}>
        <div style={s.label}>Cost Before</div>
        <div style={s.value}>${summary.total_cost_before.toFixed(2)}</div>
        <div style={s.sub}>Without battery</div>
      </div>
      <div style={s.card}>
        <div style={s.label}>Cost After</div>
        <div style={s.value}>${summary.total_cost_after.toFixed(2)}</div>
        <div style={s.sub}>With battery dispatch</div>
      </div>
      <div style={{ ...s.card, border: "1px solid #16a34a" }}>
        <div style={s.label}>Savings</div>
        <div style={s.savings}>${summary.savings.toFixed(2)}</div>
        <div style={s.sub}>{pct}% reduction</div>
      </div>
      <div style={s.card}>
        <div style={s.label}>Peak Load Before</div>
        <div style={s.value}>{summary.peak_before_kw.toFixed(2)} kW</div>
        <div style={s.sub}>Max hourly draw</div>
      </div>
      <div style={s.card}>
        <div style={s.label}>Peak Load After</div>
        <div style={s.value}>{summary.peak_after_kw.toFixed(2)} kW</div>
        <div style={s.sub}>Max net draw</div>
      </div>
    </div>
  );
}
