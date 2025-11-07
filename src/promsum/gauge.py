from typing import Any, Dict, List
from statistics import mean, median, pstdev
from .core import parse_prom_range_json, coerce_values, linear_regression_slope, classify_trend

def summarize_gauge(obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    results = []
    for series in parse_prom_range_json(obj):
        labels = dict(series.get("metric", {}))
        ts, vs = coerce_values(series.get("values", []))
        mn, mx = min(vs), max(vs)
        mu = mean(vs)
        med = median(vs)
        sd = pstdev(vs) if len(vs) > 1 else 0.0
        change = vs[-1] - vs[0]
        slope = linear_regression_slope(ts, vs)
        trend = classify_trend(vs[0], vs[-1], mx - mn, slope)
        start_ts, end_ts = ts[0], ts[-1]
        duration = max(1e-9, end_ts - start_ts)
        results.append({
            "labels": labels,
            "metric_type": "gauge",
            "stats": {
                "count": len(vs),
                "start_timestamp": start_ts,
                "end_timestamp": end_ts,
                "duration_seconds": duration,
                "start_value": vs[0],
                "end_value": vs[-1],
                "min": round(mn, 12),
                "max": round(mx, 12),
                "mean": round(mu, 12),
                "median": round(med, 12),
                "stddev": round(sd, 12),
                "trend": trend,
                "change_over_window": round(change, 12),
            },
        })
    return results
