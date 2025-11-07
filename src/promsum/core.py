from typing import Any, Dict, List, Tuple, Iterable
from statistics import mean

def parse_prom_range_json(obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not obj or obj.get("status") != "success":
        raise ValueError("Expected Prometheus response with status=success")
    data = obj.get("data", {})
    if data.get("resultType") != "matrix":
        raise ValueError("Only matrix (range) resultType is supported")
    return data.get("result", [])

def coerce_values(values: Iterable[Tuple[float, str]]) -> Tuple[List[float], List[float]]:
    ts: List[float] = []
    vs: List[float] = []
    for t, v in values:
        try:
            fv = float(v)
        except Exception:
            continue
        if fv != fv or fv == float("inf") or fv == float("-inf"):
            continue
        ts.append(float(t))
        vs.append(fv)
    if not ts or not vs:
        raise ValueError("Empty or invalid values array")
    return ts, vs

def linear_regression_slope(ts: List[float], vs: List[float]) -> float:
    n = len(ts)
    if n < 2:
        return 0.0
    x_mean = mean(ts)
    y_mean = mean(vs)
    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(ts, vs))
    den = sum((x - x_mean) ** 2 for x in ts)
    return num / den if den != 0 else 0.0

def classify_trend(v0: float, v1: float, rng: float, slope: float) -> str:
    eps = max(1e-6, 0.01 * max(rng, abs(v0), abs(v1)))
    delta = v1 - v0
    if abs(delta) <= eps and abs(slope) <= eps / max(1.0, rng):
        return "stable"
    return "rising" if delta > 0 else "falling"
