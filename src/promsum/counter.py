from typing import Any, Dict, List
from .core import parse_prom_range_json, coerce_values

def summarize_counter(obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    results = []
    for series in parse_prom_range_json(obj):
        labels = dict(series.get("metric", {}))
        ts, vs = coerce_values(series.get("values", []))
        start_ts, end_ts = ts[0], ts[-1]
        total_start, total_end = vs[0], vs[-1]
        delta = max(0.0, total_end - total_start)
        duration = max(1e-9, end_ts - start_ts)
        rps = delta / duration
        rpm = rps * 60.0
        results.append({
            "labels": labels,
            "metric_type": "counter",
            "stats": {
                "count": len(vs),
                "start_timestamp": start_ts,
                "end_timestamp": end_ts,
                "duration_seconds": duration,
                "start_value": total_start,
                "end_value": total_end,
                "total": total_end,
                "delta": delta,
                "rate_per_second": rps,
                "rate_per_minute": rpm
            },
        })
    return results
