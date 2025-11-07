import sys, json, argparse
from .counter import summarize_counter
from .gauge import summarize_gauge
from .histogram import summarize_histogram
from .summary import summarize_summary

def summarize(metric_type: str, payload: str) -> str:
    obj = json.loads(payload)
    mt = metric_type.lower()
    if mt == "counter":
        out = summarize_counter(obj)
    elif mt == "gauge":
        out = summarize_gauge(obj)
    elif mt == "histogram":
        out = summarize_histogram(obj)
    elif mt == "summary":
        out = summarize_summary(obj)
    else:
        raise SystemExit(f"Unsupported metric_type: {metric_type}")
    return json.dumps(out, indent=2, sort_keys=False)

def main():
    p = argparse.ArgumentParser(description="Prometheus range JSON -> compact summaries")
    p.add_argument("--metric-type", required=True, choices=["counter", "gauge", "histogram", "summary"])
    p.add_argument("--input", help="Path to JSON file (defaults to stdin)")
    args = p.parse_args()

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            payload = f.read()
    else:
        payload = sys.stdin.read()

    print(summarize(args.metric_type, payload))

if __name__ == "__main__":
    main()
