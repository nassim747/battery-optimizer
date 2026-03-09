export interface Battery {
  capacity_kwh: number;
  max_charge_kw: number;
  max_discharge_kw: number;
  efficiency: number;
  initial_soc_kwh: number;
}

export interface OptimizeRequest {
  load_kwh: number[];
  price_per_kwh: number[];
  battery: Battery;
}

export interface OptimizeResponse {
  charge_kw: number[];
  discharge_kw: number[];
  soc_kwh: number[];
  total_cost_before: number;
  total_cost_after: number;
  savings: number;
  explanation: string;
}

export interface Summary {
  total_cost_before: number;
  total_cost_after: number;
  savings: number;
  peak_before_kw: number;
  peak_after_kw: number;
}

export interface PlotlyTrace {
  name: string;
  x: string[];
  y: number[];
  type: string;
  mode?: string;
  fill?: string;
  yaxis?: string;
  marker?: { color: string; size?: number };
  line?: { color: string; width?: number };
}

export interface Chart {
  title: string;
  hours: string[];   // e.g. ["00:00", "01:00", ...]
  traces: PlotlyTrace[];
  xaxis_label: string;
  yaxis_label: string;
}

export interface Charts {
  load_chart: Chart;
  dispatch_chart: Chart;
  soc_chart: Chart;
}

export interface VisualizeResponse {
  summary: Summary;
  charts: Charts;
  explanation: string;
}

export type AppStatus = "idle" | "loading" | "success" | "error";

export interface AppState {
  status: AppStatus;
  request: OptimizeRequest;
  visualizeData: VisualizeResponse | null;
  error: string | null;
}
