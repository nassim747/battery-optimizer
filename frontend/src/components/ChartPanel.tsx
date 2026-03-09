import Plot from "react-plotly.js";
import type { Charts, Chart } from "../types";

const DARK_LAYOUT = {
  paper_bgcolor: "#1e293b",
  plot_bgcolor: "#0f172a",
  font: { color: "#cbd5e1", family: "system-ui, sans-serif", size: 12 },
  legend: { bgcolor: "rgba(0,0,0,0)", bordercolor: "#334155", borderwidth: 1 },
  margin: { t: 50, r: 20, b: 60, l: 60 },
};

function SingleChart({ chart }: { chart: Chart }) {
  const hasSecondAxis = chart.traces.some((t) => t.yaxis === "y2");

  const layout: Partial<Plotly.Layout> = {
    ...DARK_LAYOUT,
    title: {
      text: chart.title,
      font: { color: "#f1f5f9", size: 14 },
    },
    xaxis: {
      title: { text: chart.xaxis_label },
      gridcolor: "#1e293b",
      color: "#94a3b8",
      tickfont: { size: 10 },
    },
    yaxis: {
      title: { text: chart.yaxis_label },
      gridcolor: "#334155",
      color: "#94a3b8",
    },
    ...(hasSecondAxis
      ? {
          yaxis2: {
            title: { text: "Price ($/kWh)", font: { color: "#f59e0b" } },
            overlaying: "y" as const,
            side: "right" as const,
            color: "#f59e0b",
            gridcolor: "transparent",
            showgrid: false,
          },
        }
      : {}),
    barmode: "relative" as const,
  };

  return (
    <div
      style={{
        background: "#1e293b",
        borderRadius: "12px",
        border: "1px solid #334155",
        padding: "8px",
        marginBottom: "16px",
      }}
    >
      <Plot
        data={chart.traces as Plotly.Data[]}
        layout={layout}
        config={{ displayModeBar: true, responsive: true }}
        style={{ width: "100%", height: "320px" }}
        useResizeHandler
      />
    </div>
  );
}

interface Props {
  charts: Charts;
}

export default function ChartPanel({ charts }: Props) {
  return (
    <div>
      <SingleChart chart={charts.load_chart} />
      <SingleChart chart={charts.dispatch_chart} />
      <SingleChart chart={charts.soc_chart} />
    </div>
  );
}
