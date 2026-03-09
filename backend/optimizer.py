"""
Battery dispatch optimizer using Mixed-Integer Linear Programming (MILP).

Formulation
-----------
Minimize:  Σ_t  price[t] * (charge[t] - discharge[t])
           (we minimise the net cost delta; base load cost is constant)

Subject to:
  ∀t ∈ {0..23}:
    0 ≤ charge[t]    ≤ max_charge_kw  * z[t]       (binary z: 1 = charging)
    0 ≤ discharge[t] ≤ max_discharge_kw * (1 - z[t]) (mutually exclusive)
    soc[t] = initial_soc + Σ_{s≤t} (charge[s]*η - discharge[s])
    0 ≤ soc[t] ≤ capacity_kwh

Efficiency model: energy stored = charge_kw * η  (one-way charging loss).
Discharging is assumed loss-free on the way out, matching a common
convention where η represents the charge efficiency factor.
"""

import pulp
from typing import List, Dict


def run_optimization(
    load_kwh: List[float],
    price_per_kwh: List[float],
    capacity_kwh: float,
    max_charge_kw: float,
    max_discharge_kw: float,
    efficiency: float,
    initial_soc_kwh: float,
) -> Dict:
    T = 24
    prob = pulp.LpProblem("battery_dispatch", pulp.LpMinimize)

    charge = [
        pulp.LpVariable(f"charge_{t}", lowBound=0, upBound=max_charge_kw)
        for t in range(T)
    ]
    discharge = [
        pulp.LpVariable(f"discharge_{t}", lowBound=0, upBound=max_discharge_kw)
        for t in range(T)
    ]
    # Binary: z[t]=1 → charging, z[t]=0 → discharging (or idle)
    z = [pulp.LpVariable(f"z_{t}", cat="Binary") for t in range(T)]

    prob += pulp.lpSum(
        price_per_kwh[t] * (charge[t] - discharge[t]) for t in range(T)
    )

    for t in range(T):
        # No simultaneous charge & discharge (big-M via binary variable)
        prob += charge[t] <= max_charge_kw * z[t]
        prob += discharge[t] <= max_discharge_kw * (1 - z[t])

        soc_t = initial_soc_kwh + pulp.lpSum(
            charge[s] * efficiency - discharge[s] for s in range(t + 1)
        )
        prob += soc_t >= 0
        prob += soc_t <= capacity_kwh

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    status = pulp.LpStatus[prob.status]
    if prob.status != 1:
        raise ValueError(f"Optimization infeasible or unbounded (status: {status})")

    charge_kw = [max(0.0, pulp.value(charge[t]) or 0.0) for t in range(T)]
    discharge_kw = [max(0.0, pulp.value(discharge[t]) or 0.0) for t in range(T)]

    # Recompute from decision variable values to avoid floating-point drift
    soc_kwh: List[float] = []
    soc = initial_soc_kwh
    for t in range(T):
        soc += charge_kw[t] * efficiency - discharge_kw[t]
        soc_kwh.append(round(max(0.0, soc), 6))

    total_cost_before = sum(price_per_kwh[t] * load_kwh[t] for t in range(T))
    total_cost_after = sum(
        price_per_kwh[t] * (load_kwh[t] + charge_kw[t] - discharge_kw[t])
        for t in range(T)
    )
    savings = total_cost_before - total_cost_after

    explanation = _build_explanation(price_per_kwh, charge_kw, discharge_kw)

    return {
        "charge_kw": [round(v, 4) for v in charge_kw],
        "discharge_kw": [round(v, 4) for v in discharge_kw],
        "soc_kwh": [round(v, 4) for v in soc_kwh],
        "total_cost_before": round(total_cost_before, 4),
        "total_cost_after": round(total_cost_after, 4),
        "savings": round(savings, 4),
        "explanation": explanation,
    }


def _build_explanation(
    price_per_kwh: List[float],
    charge_kw: List[float],
    discharge_kw: List[float],
) -> str:
    """Return a plain-language summary of the top-3 savings hours."""
    hourly_savings = [
        (price_per_kwh[t] * (discharge_kw[t] - charge_kw[t]), t)
        for t in range(24)
    ]
    hourly_savings.sort(key=lambda x: x[0], reverse=True)
    top3 = hourly_savings[:3]

    parts = []
    for saving, hour in top3:
        action = "discharge" if discharge_kw[hour] > charge_kw[hour] else "charge"
        parts.append(
            f"hour {hour:02d}:00 ({action}, ${saving:.2f} saved)"
        )

    return (
        f"The 3 hours generating the most savings were: {', '.join(parts)}. "
        f"Total optimized savings: ${sum(s for s, _ in top3):.2f} from these hours alone."
    )


def build_visualize_data(
    load_kwh: List[float],
    price_per_kwh: List[float],
    charge_kw: List[float],
    discharge_kw: List[float],
    soc_kwh: List[float],
    total_cost_before: float,
    total_cost_after: float,
    savings: float,
) -> Dict:
    hours = list(range(24))
    hour_labels = [f"{h:02d}:00" for h in hours]

    net_load_after = [
        load_kwh[t] + charge_kw[t] - discharge_kw[t] for t in range(24)
    ]
    peak_before = max(load_kwh)
    peak_after = max(net_load_after)

    summary = {
        "total_cost_before": round(total_cost_before, 4),
        "total_cost_after": round(total_cost_after, 4),
        "savings": round(savings, 4),
        "peak_before_kw": round(peak_before, 4),
        "peak_after_kw": round(peak_after, 4),
    }

    load_chart = {
        "title": "Electricity Load Profile — Before vs After Optimization",
        "hours": hour_labels,
        "xaxis_label": "Hour of Day",
        "yaxis_label": "Load (kWh)",
        "traces": [
            {
                "name": "Load Before (kWh)",
                "x": hour_labels,
                "y": [round(v, 4) for v in load_kwh],
                "type": "bar",
                "marker": {"color": "#ef4444"},
            },
            {
                "name": "Net Load After (kWh)",
                "x": hour_labels,
                "y": [round(v, 4) for v in net_load_after],
                "type": "bar",
                "marker": {"color": "#22c55e"},
            },
            {
                "name": "Price ($/kWh)",
                "x": hour_labels,
                "y": [round(v, 4) for v in price_per_kwh],
                "type": "scatter",
                "mode": "lines+markers",
                "yaxis": "y2",
                "line": {"color": "#f59e0b", "width": 2},
                "marker": {"color": "#f59e0b", "size": 5},
            },
        ],
    }

    dispatch_chart = {
        "title": "Battery Dispatch — Charge & Discharge Schedule",
        "hours": hour_labels,
        "xaxis_label": "Hour of Day",
        "yaxis_label": "Power (kW)",
        "traces": [
            {
                "name": "Charge (kW)",
                "x": hour_labels,
                "y": [round(v, 4) for v in charge_kw],
                "type": "bar",
                "marker": {"color": "#3b82f6"},
            },
            {
                "name": "Discharge (kW)",
                "x": hour_labels,
                "y": [-round(v, 4) for v in discharge_kw],
                "type": "bar",
                "marker": {"color": "#a855f7"},
            },
        ],
    }

    soc_chart = {
        "title": "Battery State of Charge (SoC) Over 24 Hours",
        "hours": hour_labels,
        "xaxis_label": "Hour of Day",
        "yaxis_label": "State of Charge (kWh)",
        "traces": [
            {
                "name": "SoC (kWh)",
                "x": hour_labels,
                "y": [round(v, 4) for v in soc_kwh],
                "type": "scatter",
                "mode": "lines+markers",
                "fill": "tozeroy",
                "line": {"color": "#06b6d4", "width": 2},
                "marker": {"color": "#06b6d4", "size": 5},
            }
        ],
    }

    return {
        "summary": summary,
        "charts": {
            "load_chart": load_chart,
            "dispatch_chart": dispatch_chart,
            "soc_chart": soc_chart,
        },
    }
