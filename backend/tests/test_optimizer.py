"""Unit tests for the battery optimizer and API endpoints."""

import pytest
from fastapi.testclient import TestClient

import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from optimizer import run_optimization
from main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
HEADERS = {"x-api-key": "dev-key-abc123"}

LOAD = [0.4, 0.3, 0.3, 0.3, 0.4, 0.6, 1.2, 1.5, 1.3, 1.0, 0.9, 0.8,
        0.9, 0.8, 0.8, 1.0, 1.4, 2.0, 2.5, 2.2, 1.8, 1.4, 1.0, 0.6]

PRICE = [0.06, 0.06, 0.06, 0.06, 0.06, 0.08, 0.12, 0.18, 0.20, 0.18, 0.15, 0.14,
         0.14, 0.13, 0.14, 0.16, 0.20, 0.25, 0.28, 0.26, 0.22, 0.18, 0.12, 0.08]

BATTERY = {
    "capacity_kwh": 10,
    "max_charge_kw": 3,
    "max_discharge_kw": 3,
    "efficiency": 0.92,
    "initial_soc_kwh": 2,
}

PAYLOAD = {"load_kwh": LOAD, "price_per_kwh": PRICE, "battery": BATTERY}


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Optimizer unit tests
# ---------------------------------------------------------------------------
class TestOptimizer:
    def test_returns_correct_structure(self):
        result = run_optimization(LOAD, PRICE, **BATTERY)
        assert "charge_kw" in result
        assert "discharge_kw" in result
        assert "soc_kwh" in result
        assert "total_cost_before" in result
        assert "total_cost_after" in result
        assert "savings" in result
        assert "explanation" in result

    def test_24_values_each(self):
        result = run_optimization(LOAD, PRICE, **BATTERY)
        assert len(result["charge_kw"]) == 24
        assert len(result["discharge_kw"]) == 24
        assert len(result["soc_kwh"]) == 24

    def test_soc_within_bounds(self):
        result = run_optimization(LOAD, PRICE, **BATTERY)
        cap = BATTERY["capacity_kwh"]
        for soc in result["soc_kwh"]:
            assert -1e-4 <= soc <= cap + 1e-4, f"SoC {soc} out of [0, {cap}]"

    def test_charge_within_limits(self):
        result = run_optimization(LOAD, PRICE, **BATTERY)
        for c in result["charge_kw"]:
            assert c >= -1e-6
            assert c <= BATTERY["max_charge_kw"] + 1e-6

    def test_discharge_within_limits(self):
        result = run_optimization(LOAD, PRICE, **BATTERY)
        for d in result["discharge_kw"]:
            assert d >= -1e-6
            assert d <= BATTERY["max_discharge_kw"] + 1e-6

    def test_no_simultaneous_charge_discharge(self):
        result = run_optimization(LOAD, PRICE, **BATTERY)
        for t in range(24):
            c = result["charge_kw"][t]
            d = result["discharge_kw"][t]
            assert not (c > 1e-4 and d > 1e-4), f"Simultaneous at hour {t}"

    def test_savings_positive_for_tou_pricing(self):
        result = run_optimization(LOAD, PRICE, **BATTERY)
        assert result["savings"] >= 0

    def test_cost_identity(self):
        result = run_optimization(LOAD, PRICE, **BATTERY)
        assert abs(
            result["total_cost_before"] - result["total_cost_after"] - result["savings"]
        ) < 1e-3

    def test_explanation_string(self):
        result = run_optimization(LOAD, PRICE, **BATTERY)
        assert isinstance(result["explanation"], str)
        assert len(result["explanation"]) > 20


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------
class TestHealthEndpoint:
    def test_health_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_health_no_auth_needed(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200


class TestOptimizeEndpoint:
    def test_optimize_success(self, client):
        resp = client.post("/optimize", json=PAYLOAD, headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "charge_kw" in data
        assert "savings" in data

    def test_optimize_missing_api_key(self, client):
        resp = client.post("/optimize", json=PAYLOAD)
        assert resp.status_code == 401

    def test_optimize_invalid_api_key(self, client):
        resp = client.post("/optimize", json=PAYLOAD, headers={"x-api-key": "bad-key"})
        assert resp.status_code == 401

    def test_optimize_wrong_length(self, client):
        bad = {**PAYLOAD, "load_kwh": LOAD[:23]}
        resp = client.post("/optimize", json=bad, headers=HEADERS)
        assert resp.status_code == 422

    def test_optimize_soc_exceeds_capacity(self, client):
        bad_battery = {**BATTERY, "initial_soc_kwh": 999}
        resp = client.post(
            "/optimize", json={**PAYLOAD, "battery": bad_battery}, headers=HEADERS
        )
        assert resp.status_code == 422

    def test_optimize_invalid_efficiency(self, client):
        bad_battery = {**BATTERY, "efficiency": 1.5}
        resp = client.post(
            "/optimize", json={**PAYLOAD, "battery": bad_battery}, headers=HEADERS
        )
        assert resp.status_code == 422


class TestVisualizeEndpoint:
    def test_visualize_success(self, client):
        resp = client.post("/visualize", json=PAYLOAD, headers=HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "charts" in data

    def test_visualize_chart_keys(self, client):
        resp = client.post("/visualize", json=PAYLOAD, headers=HEADERS)
        charts = resp.json()["charts"]
        assert "load_chart" in charts
        assert "dispatch_chart" in charts
        assert "soc_chart" in charts

    def test_visualize_summary_fields(self, client):
        resp = client.post("/visualize", json=PAYLOAD, headers=HEADERS)
        data = resp.json()
        s = data["summary"]
        for key in ("total_cost_before", "total_cost_after", "savings",
                    "peak_before_kw", "peak_after_kw"):
            assert key in s

    def test_visualize_has_explanation(self, client):
        resp = client.post("/visualize", json=PAYLOAD, headers=HEADERS)
        data = resp.json()
        assert "explanation" in data
        assert isinstance(data["explanation"], str)
        assert len(data["explanation"]) > 20
