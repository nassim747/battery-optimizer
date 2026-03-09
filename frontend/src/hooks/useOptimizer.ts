import { useReducer, useCallback } from "react";
import type { AppState, OptimizeRequest, VisualizeResponse } from "../types";
import { apiVisualize } from "../api";

export const DEFAULT_LOAD: number[] = [
  0.4, 0.3, 0.3, 0.3, 0.4, 0.6, 1.2, 1.5, 1.3, 1.0, 0.9, 0.8,
  0.9, 0.8, 0.8, 1.0, 1.4, 2.0, 2.5, 2.2, 1.8, 1.4, 1.0, 0.6,
];

export const DEFAULT_PRICE: number[] = [
  0.06, 0.06, 0.06, 0.06, 0.06, 0.08, 0.12, 0.18, 0.20, 0.18, 0.15, 0.14,
  0.14, 0.13, 0.14, 0.16, 0.20, 0.25, 0.28, 0.26, 0.22, 0.18, 0.12, 0.08,
];

const DEFAULT_REQUEST: OptimizeRequest = {
  load_kwh: DEFAULT_LOAD,
  price_per_kwh: DEFAULT_PRICE,
  battery: {
    capacity_kwh: 10,
    max_charge_kw: 3,
    max_discharge_kw: 3,
    efficiency: 0.92,
    initial_soc_kwh: 2,
  },
};

type Action =
  | { type: "SET_REQUEST"; payload: OptimizeRequest }
  | { type: "FETCH_START" }
  | { type: "FETCH_SUCCESS"; payload: VisualizeResponse }
  | { type: "FETCH_ERROR"; payload: string }
  | { type: "RESET" };

const initialState: AppState = {
  status: "idle",
  request: DEFAULT_REQUEST,
  visualizeData: null,
  error: null,
};

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case "SET_REQUEST":
      return { ...state, request: action.payload };
    case "FETCH_START":
      return { ...state, status: "loading", error: null };
    case "FETCH_SUCCESS":
      return { ...state, status: "success", visualizeData: action.payload };
    case "FETCH_ERROR":
      return { ...state, status: "error", error: action.payload };
    case "RESET":
      return initialState;
    default:
      return state;
  }
}

export function useOptimizer() {
  const [state, dispatch] = useReducer(reducer, initialState);

  const setRequest = useCallback((req: OptimizeRequest) => {
    dispatch({ type: "SET_REQUEST", payload: req });
  }, []);

  const run = useCallback(async (req: OptimizeRequest) => {
    dispatch({ type: "FETCH_START" });
    try {
      const data = await apiVisualize(req);
      dispatch({ type: "FETCH_SUCCESS", payload: data });
    } catch (err) {
      dispatch({
        type: "FETCH_ERROR",
        payload: err instanceof Error ? err.message : "Unknown error",
      });
    }
  }, []);

  const reset = useCallback(() => dispatch({ type: "RESET" }), []);

  return { state, setRequest, run, reset };
}
