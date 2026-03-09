from pydantic import BaseModel, Field, validator
from typing import List, Optional


class Battery(BaseModel):
    capacity_kwh: float = Field(..., gt=0, description="Maximum energy capacity in kWh")
    max_charge_kw: float = Field(..., gt=0, description="Maximum charging power in kW")
    max_discharge_kw: float = Field(..., gt=0, description="Maximum discharging power in kW")
    efficiency: float = Field(..., gt=0, le=1, description="Charging efficiency (0 < η ≤ 1)")
    initial_soc_kwh: float = Field(..., ge=0, description="Initial state of charge in kWh")

    @validator("initial_soc_kwh")
    def soc_within_capacity(cls, v, values):
        if "capacity_kwh" in values and v > values["capacity_kwh"]:
            raise ValueError("initial_soc_kwh cannot exceed capacity_kwh")
        return v


class OptimizeRequest(BaseModel):
    load_kwh: List[float] = Field(..., min_items=24, max_items=24, description="24 hourly load values in kWh")
    price_per_kwh: List[float] = Field(..., min_items=24, max_items=24, description="24 hourly electricity prices in $/kWh")
    battery: Battery

    @validator("load_kwh", each_item=True)
    def load_non_negative(cls, v):
        if v < 0:
            raise ValueError("load_kwh values must be non-negative")
        return v

    @validator("price_per_kwh", each_item=True)
    def price_non_negative(cls, v):
        if v < 0:
            raise ValueError("price_per_kwh values must be non-negative")
        return v


class OptimizeResponse(BaseModel):
    charge_kw: List[float]
    discharge_kw: List[float]
    soc_kwh: List[float]
    total_cost_before: float
    total_cost_after: float
    savings: float
    explanation: str


class Summary(BaseModel):
    total_cost_before: float
    total_cost_after: float
    savings: float
    peak_before_kw: float
    peak_after_kw: float


class ChartTrace(BaseModel):
    name: str
    y: List[float]
    type: str = "bar"
    mode: Optional[str] = None
    marker: Optional[dict] = None
    line: Optional[dict] = None


class Chart(BaseModel):
    title: str
    hours: List[str]
    traces: List[dict]
    xaxis_label: str
    yaxis_label: str


class Charts(BaseModel):
    load_chart: Chart
    dispatch_chart: Chart
    soc_chart: Chart


class VisualizeResponse(BaseModel):
    summary: Summary
    charts: Charts
    explanation: str
