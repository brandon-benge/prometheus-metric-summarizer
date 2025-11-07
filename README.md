# Prometheus Metric Summarizer

Apache-2.0 licensed Python library that converts **Prometheus range query** JSON
(`GET /api/v1/query_range`) into compact, metric-type–aware summaries for **agentic
pipelines** and AI-Ops.

> **Scope:** Only *range* (`matrix`) responses are supported. Instant/vector queries are out of scope.

## Quickstart
```bash
# Using the convenience script (venv at ../venv)
./run_venv.sh

# Or manually
python -m venv ../venv && source ../venv/bin/activate
pip install -r requirements.txt
python -m promsum.cli --metric-type gauge --input examples/sample_gauge.json
```

## Development

### Installing for Development
```bash
# Activate your virtual environment
source ../venv/bin/activate  # or ./run_venv.sh

# Install in editable mode
pip install -e .

# Now you can use the command directly
promsum --metric-type gauge --input examples/sample_gauge.json
```

### Building the Package
```bash
# Install build tools
pip install build twine

# Build source distribution and wheel
python -m build

# Output will be in dist/
# - prometheus_metric_summarizer-0.1.0-py3-none-any.whl
# - prometheus_metric_summarizer-0.1.0.tar.gz
# and it will be in your venv 
which promsum     # shows you the location
```

### Testing
```bash
# Test with example files
promsum --metric-type counter --input examples/sample_counter.json
promsum --metric-type gauge --input examples/sample_gauge.json
promsum --metric-type histogram --input examples/sample_histogram.json
promsum --metric-type summary --input examples/sample_summary.json

# Or using the module directly
python -m promsum.cli --metric-type gauge --input examples/sample_gauge.json
```

### Installing from Built Package
```bash
# Install the wheel
pip install dist/prometheus_metric_summarizer-0.1.0-py3-none-any.whl

# Or install the source distribution
pip install dist/prometheus-metric-summarizer-0.1.0.tar.gz
```

## Input format (exact Prometheus range-query shape)
```json
{
  "status": "success",
  "data": {
    "resultType": "matrix",
    "result": [ { "metric": {...}, "values": [[ts, "val"], ...] } ]
  }
}
```

## Output (per unique label set)
All metric types include *time anchors*:
- `start_timestamp`, `end_timestamp`, `duration_seconds`
- For `counter` and `gauge`: `start_value`, `end_value`, `count` (number of data points)
- For `histogram` and `summary`: `num_data_points` (number of scrape samples)

### Gauge Example
```json
[{
  "labels": {"namespace": "payments", "pod": "worker-1"},
  "metric_type": "gauge",
  "stats": {
    "count": 9,
    "start_timestamp": 1731003000,
    "end_timestamp": 1731003120,
    "duration_seconds": 120,
    "start_value": 0.42,
    "end_value": 0.55,
    "min": 0.42, "max": 0.55, "mean": 0.48, "median": 0.47, "stddev": 0.06,
    "trend": "rising", "change_over_window": 0.13
  }
}]
```

### Reductions
- **Counter**: `count` (data points), `start/end timestamps & values`, `delta`, `rate_per_second`, `rate_per_minute`, `total=end_value`.
- **Gauge**: `count` (data points), `start/end timestamps & values`, `min`, `max`, `mean`, `median`, `stddev`, `trend`, `change_over_window`.
- **Histogram**: `num_data_points` (scrape samples), `start/end timestamps`, `duration`, window deltas from buckets, `count` (observations), `sum`, `avg`,
  quantiles (`p50`, `p90`, `p95`, `p99`) via bucket reconstruction, `dominant_bucket`.
- **Summary**: `num_data_points` (scrape samples), `start/end timestamps`, `duration`, deltas for `_sum`/`_count`, `count` (observations), `avg=sum/count`, and
  quantiles grouped under `stats.quantiles`.

## License
Apache License 2.0.
