from typing import Any, Dict, List, DefaultDict
from collections import defaultdict
from .core import parse_prom_range_json, coerce_values
from .scrape_analysis import analyze_scrape_intervals

def summarize_summary(obj: Dict[str, Any], include_scrape_analysis: bool = False) -> List[Dict[str, Any]]:
    grouped: DefaultDict[tuple, Dict[str, Any]] = defaultdict(lambda: {
        "labels": {}, "quantiles": {}, "sum": None, "count": None, "starts": [], "ends": []
    })
    for series in parse_prom_range_json(obj):
        metric = dict(series.get("metric", {}))
        values = series.get("values", [])
        base_labels = {k: v for k, v in metric.items() if k not in ("quantile",)}
        key = tuple(sorted(base_labels.items()))
        rec = grouped[key]
        rec["labels"] = base_labels
        if "quantile" in metric:
            q = str(metric["quantile"])
            ts, vs = coerce_values(values)
            rec["quantiles"][q] = vs[-1]
            rec["starts"].append(ts[0]); rec["ends"].append(ts[-1])
        else:
            name = metric.get("__name__", "")
            if name.endswith("_sum"):
                rec["sum"] = values
            elif name.endswith("_count"):
                rec["count"] = values

    results = []
    for key, rec in grouped.items():
        total_sum = total_count = None
        if rec["sum"] is not None:
            ts, vs = coerce_values(rec["sum"])
            total_sum = max(0.0, vs[-1] - vs[0])
            rec["starts"].append(ts[0]); rec["ends"].append(ts[-1])
        if rec["count"] is not None:
            ts, vs = coerce_values(rec["count"])
            total_count = max(0.0, vs[-1] - vs[0])
            rec["starts"].append(ts[0]); rec["ends"].append(ts[-1])
        avg = (total_sum / total_count) if (total_sum is not None and total_count and total_count > 0) else None
        start_ts = min(rec["starts"]) if rec["starts"] else None
        end_ts = max(rec["ends"]) if rec["ends"] else None
        duration = (end_ts - start_ts) if (start_ts is not None and end_ts is not None) else None

        # Count of data points (from the first quantile or count series)
        num_values = 0
        if rec["count"] is not None:
            num_values = len(coerce_values(rec["count"])[1])
        elif rec["sum"] is not None:
            num_values = len(coerce_values(rec["sum"])[1])
        elif rec["quantiles"]:
            # Get from any quantile series (they should all have the same number of points)
            for q_key, q_val in rec.items():
                if isinstance(q_val, dict) and "quantiles" in q_key:
                    break

        result = {
            "labels": rec["labels"],
            "metric_type": "summary",
            "stats": {
                "num_data_points": num_values,
                "start_timestamp": start_ts,
                "end_timestamp": end_ts,
                "duration_seconds": duration,
                "count": total_count,
                "sum": total_sum,
                "avg": avg,
                "quantiles": rec["quantiles"],
            },
        }
        
        # Scrape interval analysis (use count series if available, else sum)
        if include_scrape_analysis:
            if rec["count"] is not None:
                ts, vs = coerce_values(rec["count"])
                result["scrape_analysis"] = analyze_scrape_intervals(ts, vs, is_counter=True)
            elif rec["sum"] is not None:
                ts, vs = coerce_values(rec["sum"])
                result["scrape_analysis"] = analyze_scrape_intervals(ts, vs, is_counter=True)
        
        results.append(result)
    return results
