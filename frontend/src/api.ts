import type { OptimizeRequest, VisualizeResponse } from "./types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY ?? "dev-key-abc123";

async function apiFetch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": API_KEY,
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(
      typeof err.detail === "string"
        ? err.detail
        : JSON.stringify(err.detail) ?? `HTTP ${res.status}`
    );
  }
  return res.json() as Promise<T>;
}

export const apiVisualize = (req: OptimizeRequest): Promise<VisualizeResponse> =>
  apiFetch<VisualizeResponse>("/visualize", req);
