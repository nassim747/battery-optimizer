import React from "react";
import InputForm from "./components/InputForm";
import ChartPanel from "./components/ChartPanel";
import SummaryCard from "./components/SummaryCard";
import { useOptimizer } from "./hooks/useOptimizer";

const s: Record<string, React.CSSProperties> = {
  root: {
    minHeight: "100vh",
    background: "#0f172a",
    color: "#e2e8f0",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    padding: "18px 24px",
    borderBottom: "1px solid #1e293b",
    background: "#0f172a",
    position: "sticky" as const,
    top: 0,
    zIndex: 10,
  },
  logo: { fontSize: "24px" },
  headerTitle: { fontSize: "18px", fontWeight: 700, color: "#f1f5f9" },
  headerSub: { fontSize: "12px", color: "#64748b", marginTop: "2px" },
  layout: {
    display: "flex",
    gap: 0,
    minHeight: "calc(100vh - 65px)",
  },
  sidebar: {
    width: "340px",
    flexShrink: 0,
    borderRight: "1px solid #1e293b",
    padding: "20px",
    overflowY: "auto" as const,
    maxHeight: "calc(100vh - 65px)",
    position: "sticky" as const,
    top: "65px",
  },
  main: {
    flex: 1,
    padding: "24px",
    overflowY: "auto" as const,
  },
  mainTitle: {
    fontSize: "15px",
    fontWeight: 700,
    color: "#94a3b8",
    marginBottom: "16px",
  },
  idle: {
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    justifyContent: "center",
    height: "400px",
    color: "#475569",
    gap: "12px",
  },
  idleIcon: { fontSize: "56px" },
  idleText: { fontSize: "16px" },
  loading: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    height: "400px",
    color: "#64748b",
    gap: "12px",
    fontSize: "16px",
  },
  errorBox: {
    background: "#450a0a",
    border: "1px solid #7f1d1d",
    borderRadius: "12px",
    padding: "16px 20px",
    color: "#fca5a5",
    fontSize: "14px",
    marginBottom: "20px",
  },
  explanation: {
    background: "#1e293b",
    borderRadius: "12px",
    border: "1px solid #334155",
    padding: "16px 20px",
    marginBottom: "20px",
  },
  explanationLabel: {
    fontSize: "11px",
    fontWeight: 700,
    color: "#64748b",
    textTransform: "uppercase" as const,
    letterSpacing: "0.08em",
    marginBottom: "6px",
  },
  explanationText: { fontSize: "13px", color: "#cbd5e1", lineHeight: 1.6 },
  spinner: {
    width: "32px",
    height: "32px",
    border: "3px solid #1e293b",
    borderTop: "3px solid #3b82f6",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  },
};

const spinStyle = `@keyframes spin { to { transform: rotate(360deg); } }`;

export default function App() {
  const { state, run } = useOptimizer();

  return (
    <div style={s.root}>
      <style>{spinStyle}</style>

      <header style={s.header}>
        <span style={s.logo}>⚡</span>
        <div>
          <div style={s.headerTitle}>Battery Optimizer</div>
          <div style={s.headerSub}>24-hour MILP dispatch scheduling</div>
        </div>
      </header>

      <div style={s.layout}>
        <aside style={s.sidebar}>
          <InputForm
            initialRequest={state.request}
            onSubmit={run}
            loading={state.status === "loading"}
          />
        </aside>

        <main style={s.main}>
          {state.status === "idle" && (
            <div style={s.idle}>
              <span style={s.idleIcon}>🔋</span>
              <span style={s.idleText}>Configure parameters and run optimization</span>
            </div>
          )}

          {state.status === "loading" && (
            <div style={s.loading}>
              <div style={s.spinner} />
              Solving MILP…
            </div>
          )}

          {state.status === "error" && (
            <div style={s.errorBox}>
              <strong>Error: </strong>{state.error}
            </div>
          )}

          {state.status === "success" && state.visualizeData && (
            <>
              <div style={s.mainTitle}>Optimization Results</div>

              <SummaryCard summary={state.visualizeData.summary} />

              <div style={s.explanation}>
                <div style={s.explanationLabel}>Top Savings Hours</div>
                <div style={s.explanationText}>
                  {state.visualizeData.explanation}
                </div>
              </div>

              <ChartPanel charts={state.visualizeData.charts} />
            </>
          )}
        </main>
      </div>
    </div>
  );
}
