import sys, json, argparse
from .counter import summarize_counter
from .gauge import summarize_gauge
from .histogram import summarize_histogram
from .summary import summarize_summary

def summarize(metric_type: str, payload: str, include_scrape_analysis: bool = False) -> str:
    obj = json.loads(payload)
    mt = metric_type.lower()
    if mt == "counter":
        out = summarize_counter(obj, include_scrape_analysis=include_scrape_analysis)
    elif mt == "gauge":
        out = summarize_gauge(obj, include_scrape_analysis=include_scrape_analysis)
    elif mt == "histogram":
        out = summarize_histogram(obj, include_scrape_analysis=include_scrape_analysis)
    elif mt == "summary":
        out = summarize_summary(obj, include_scrape_analysis=include_scrape_analysis)
    else:
        raise SystemExit(f"Unsupported metric_type: {metric_type}")
    return json.dumps(out, indent=2, sort_keys=False)

def main():
    p = argparse.ArgumentParser(description="Prometheus range JSON -> compact summaries")
    p.add_argument("--metric-type", required=True, choices=["counter", "gauge", "histogram", "summary"])
    p.add_argument("--input", help="Path to JSON file (defaults to stdin)")
    p.add_argument("--include-scrape-analysis", action="store_true", 
                   help="Include scrape interval analysis (missed scrapes, regularity, etc.)")
    args = p.parse_args()

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            payload = f.read()
    else:
        payload = sys.stdin.read()

    print(summarize(args.metric_type, payload, include_scrape_analysis=args.include_scrape_analysis))

if __name__ == "__main__":
    main()
