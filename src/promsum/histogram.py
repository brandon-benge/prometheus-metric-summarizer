from typing import Any, Dict, List, Tuple
from .core import parse_prom_range_json, coerce_values
from .scrape_analysis import analyze_scrape_intervals

def _group_histogram_series(result: List[Dict[str, Any]]) -> Dict[Tuple[Tuple[str,str], ...], Dict[str, Any]]:
    groups: Dict[Tuple[Tuple[str,str], ...], Dict[str, Any]] = {}
    for series in result:
        metric = dict(series.get("metric", {}))
        values = series.get("values", [])
        is_bucket = "le" in metric
        le = metric.get("le")
        base_labels = {k: v for k, v in metric.items() if k not in ("le", "quantile")}
        key = tuple(sorted(base_labels.items()))
        if key not in groups:
            groups[key] = {"buckets": [], "sum": None, "count": None, "labels": base_labels}
        if is_bucket:
            groups[key]["buckets"].append({"le": le, "values": values})
        else:
            name = metric.get("__name__", "")
            if name.endswith("_sum"):
                groups[key]["sum"] = values
            elif name.endswith("_count"):
                groups[key]["count"] = values
    return groups

def _last_delta(values):
    ts, vs = coerce_values(values)
    return vs[-1] - vs[0], ts[0], ts[-1]

def _reconstruct_quantiles(bucket_edges: List[float], bucket_counts: List[float]) -> Dict[str, float]:
    import math
    total = sum(bucket_counts)
    if total <= 0:
        return {"p50": math.nan, "p90": math.nan, "p95": math.nan, "p99": math.nan}
    cum = []
    c = 0.0
    for cnt in bucket_counts:
        c += cnt
        cum.append(c)
    def quantile(q: float) -> float:
        target = q * total
        for i, cval in enumerate(cum):
            if cval >= target:
                left_cum = cum[i-1] if i > 0 else 0.0
                within = (target - left_cum) / max(1e-12, (cval - left_cum))
                left_edge = bucket_edges[i-1] if i > 0 else float("-inf")
                right_edge = bucket_edges[i]
                if left_edge == float("-inf"):
                    return right_edge * within
                return left_edge + within * (right_edge - left_edge)
        return bucket_edges[-1]
    return {"p50": quantile(0.50), "p90": quantile(0.90), "p95": quantile(0.95), "p99": quantile(0.99)}

def summarize_histogram(obj: Dict[str, Any], include_scrape_analysis: bool = False) -> List[Dict[str, Any]]:
    raw = parse_prom_range_json(obj)
    groups = _group_histogram_series(raw)
    results = []

    for key, g in groups.items():
        labels = g["labels"]
        buckets = g["buckets"]
        if not buckets:
            continue

        def parse_le(x):
            le = x["le"]
            return float("inf") if le in ("+Inf", "Inf", "inf") else float(le)
        buckets.sort(key=parse_le)

        edges = []
        counts = []
        start_ts_all = []
        end_ts_all = []
        for b in buckets:
            le_str = b["le"]
            edge = float("inf") if le_str in ("+Inf", "Inf", "inf") else float(le_str)
            edges.append(edge)
            d, s_ts, e_ts = _last_delta(b["values"])
            counts.append(max(0.0, d))
            start_ts_all.append(s_ts)
            end_ts_all.append(e_ts)

        total_count = None
        total_sum = None
        if g.get("count") is not None:
            d, s_ts, e_ts = _last_delta(g["count"])
            total_count = max(0.0, d)
            start_ts_all.append(s_ts); end_ts_all.append(e_ts)
        if g.get("sum") is not None:
            d, s_ts, e_ts = _last_delta(g["sum"])
            total_sum = max(0.0, d)
            start_ts_all.append(s_ts); end_ts_all.append(e_ts)

        if total_count is None:
            total_count = counts[-1] if edges and edges[-1] == float("inf") else sum(counts)

        if total_sum is None:
            mids = []
            last_edge = 0.0
            for i, e in enumerate(edges):
                if e == float("inf"):
                    approx = (last_edge * 1.25) if last_edge > 0 else 0.0
                    mids.append(approx)
                else:
                    approx = (last_edge + e) / 2.0
                    mids.append(approx)
                    last_edge = e
            total_sum = sum(m * c for m, c in zip(mids, counts))

        start_ts = min(start_ts_all) if start_ts_all else None
        end_ts = max(end_ts_all) if end_ts_all else None
        duration = (end_ts - start_ts) if (start_ts is not None and end_ts is not None) else None

        avg = (total_sum / total_count) if total_count > 0 else 0.0
        quants = _reconstruct_quantiles(edges, counts)
        if counts:
            idx = max(range(len(counts)), key=lambda i: counts[i])
            dom_bucket = edges[idx]
            dom_bucket = "+Inf" if dom_bucket == float("inf") else dom_bucket
        else:
            dom_bucket = None

        # Count of data points (use the first bucket's value count)
        num_values = len(coerce_values(buckets[0]["values"])[1]) if buckets else 0

        result = {
            "labels": labels,
            "metric_type": "histogram",
            "stats": {
                "num_data_points": num_values,
                "start_timestamp": start_ts,
                "end_timestamp": end_ts,
                "duration_seconds": duration,
                "count": total_count,
                "sum": total_sum,
                "avg": avg,
                "p50": quants["p50"],
                "p90": quants["p90"],
                "p95": quants["p95"],
                "p99": quants["p99"],
                "dominant_bucket": dom_bucket,
            },
        }
        
        # Scrape interval analysis (use count series if available, else sum, else first bucket)
        if include_scrape_analysis:
            if g.get("count") is not None:
                ts, vs = coerce_values(g["count"])
                result["scrape_analysis"] = analyze_scrape_intervals(ts, vs, is_counter=True)
            elif g.get("sum") is not None:
                ts, vs = coerce_values(g["sum"])
                result["scrape_analysis"] = analyze_scrape_intervals(ts, vs, is_counter=True)
            elif buckets:
                ts, vs = coerce_values(buckets[0]["values"])
                result["scrape_analysis"] = analyze_scrape_intervals(ts, vs, is_counter=True)
        
        results.append(result)
    return results
