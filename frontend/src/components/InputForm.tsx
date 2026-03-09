import React, { useState } from "react";
import type { OptimizeRequest, Battery } from "../types";
import { DEFAULT_LOAD, DEFAULT_PRICE } from "../hooks/useOptimizer";

const s: Record<string, React.CSSProperties> = {
  form: { display: "flex", flexDirection: "column", gap: "20px" },
  section: {
    background: "#1e293b",
    borderRadius: "12px",
    border: "1px solid #334155",
    padding: "16px",
  },
  sectionTitle: {
    fontSize: "13px",
    fontWeight: 700,
    color: "#94a3b8",
    textTransform: "uppercase" as const,
    letterSpacing: "0.08em",
    marginBottom: "12px",
  },
  label: { fontSize: "12px", color: "#94a3b8", marginBottom: "4px", display: "block" },
  input: {
    width: "100%",
    background: "#0f172a",
    border: "1px solid #334155",
    borderRadius: "8px",
    padding: "8px 10px",
    color: "#f1f5f9",
    fontSize: "13px",
    outline: "none",
    transition: "border-color 0.15s",
  },
  textarea: {
    width: "100%",
    background: "#0f172a",
    border: "1px solid #334155",
    borderRadius: "8px",
    padding: "8px 10px",
    color: "#f1f5f9",
    fontSize: "12px",
    fontFamily: "monospace",
    resize: "vertical" as const,
    outline: "none",
    minHeight: "72px",
  },
  row: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" },
  btn: {
    width: "100%",
    padding: "12px",
    background: "linear-gradient(135deg, #3b82f6, #2563eb)",
    color: "#fff",
    border: "none",
    borderRadius: "10px",
    fontSize: "14px",
    fontWeight: 700,
    cursor: "pointer",
    transition: "opacity 0.15s",
  },
  error: {
    background: "#450a0a",
    border: "1px solid #7f1d1d",
    borderRadius: "8px",
    padding: "10px 12px",
    color: "#fca5a5",
    fontSize: "12px",
  },
};

function parseArrayInput(raw: string): number[] | null {
  try {
    const arr = raw
      .split(/[\s,]+/)
      .filter(Boolean)
      .map(Number);
    if (arr.length !== 24 || arr.some(isNaN)) return null;
    return arr;
  } catch {
    return null;
  }
}

interface Props {
  initialRequest: OptimizeRequest;
  onSubmit: (req: OptimizeRequest) => void;
  loading: boolean;
}

export default function InputForm({ initialRequest, onSubmit, loading }: Props) {
  const [loadRaw, setLoadRaw] = useState(DEFAULT_LOAD.join(", "));
  const [priceRaw, setPriceRaw] = useState(DEFAULT_PRICE.join(", "));
  const [battery, setBattery] = useState<Battery>(initialRequest.battery);
  const [validationError, setValidationError] = useState<string | null>(null);

  function handleBattery(field: keyof Battery, value: string) {
    setBattery((prev) => ({ ...prev, [field]: parseFloat(value) || 0 }));
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setValidationError(null);

    const load = parseArrayInput(loadRaw);
    const price = parseArrayInput(priceRaw);

    if (!load) {
      setValidationError("Load profile must have exactly 24 numeric values.");
      return;
    }
    if (!price) {
      setValidationError("Price profile must have exactly 24 numeric values.");
      return;
    }
    if (battery.initial_soc_kwh > battery.capacity_kwh) {
      setValidationError("Initial SoC cannot exceed battery capacity.");
      return;
    }
    if (battery.efficiency <= 0 || battery.efficiency > 1) {
      setValidationError("Efficiency must be between 0 (exclusive) and 1 (inclusive).");
      return;
    }

    onSubmit({ load_kwh: load, price_per_kwh: price, battery });
  }

  return (
    <form style={s.form} onSubmit={handleSubmit}>
      {/* Load profile */}
      <div style={s.section}>
        <div style={s.sectionTitle}>Load Profile (24 h)</div>
        <label style={s.label}>load_kwh — 24 comma-separated values</label>
        <textarea
          style={s.textarea}
          value={loadRaw}
          onChange={(e) => setLoadRaw(e.target.value)}
          rows={3}
        />
      </div>

      {/* Price profile */}
      <div style={s.section}>
        <div style={s.sectionTitle}>Price Profile (24 h)</div>
        <label style={s.label}>price_per_kwh — 24 comma-separated values</label>
        <textarea
          style={s.textarea}
          value={priceRaw}
          onChange={(e) => setPriceRaw(e.target.value)}
          rows={3}
        />
      </div>

      {/* Battery config */}
      <div style={s.section}>
        <div style={s.sectionTitle}>Battery Configuration</div>
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <div style={s.row}>
            <div>
              <label style={s.label}>capacity_kwh</label>
              <input
                style={s.input}
                type="number"
                min={0.1}
                step={0.1}
                value={battery.capacity_kwh}
                onChange={(e) => handleBattery("capacity_kwh", e.target.value)}
              />
            </div>
            <div>
              <label style={s.label}>initial_soc_kwh</label>
              <input
                style={s.input}
                type="number"
                min={0}
                step={0.1}
                value={battery.initial_soc_kwh}
                onChange={(e) => handleBattery("initial_soc_kwh", e.target.value)}
              />
            </div>
          </div>
          <div style={s.row}>
            <div>
              <label style={s.label}>max_charge_kw</label>
              <input
                style={s.input}
                type="number"
                min={0.1}
                step={0.1}
                value={battery.max_charge_kw}
                onChange={(e) => handleBattery("max_charge_kw", e.target.value)}
              />
            </div>
            <div>
              <label style={s.label}>max_discharge_kw</label>
              <input
                style={s.input}
                type="number"
                min={0.1}
                step={0.1}
                value={battery.max_discharge_kw}
                onChange={(e) => handleBattery("max_discharge_kw", e.target.value)}
              />
            </div>
          </div>
          <div>
            <label style={s.label}>efficiency (0–1)</label>
            <input
              style={s.input}
              type="number"
              min={0.01}
              max={1}
              step={0.01}
              value={battery.efficiency}
              onChange={(e) => handleBattery("efficiency", e.target.value)}
            />
          </div>
        </div>
      </div>

      {validationError && <div style={s.error}>{validationError}</div>}

      <button
        type="submit"
        style={{ ...s.btn, opacity: loading ? 0.6 : 1 }}
        disabled={loading}
      >
        {loading ? "Optimizing…" : "Run Optimization"}
      </button>
    </form>
  );
}
