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

## LLM Prompt Examples

### Counter Metrics
```
Analyze this Prometheus counter metric summary:
{counter_output}

Fields explained:
- count: Number of data points scraped (e.g., 9 means Prometheus scraped this metric 9 times)
- start_timestamp/end_timestamp: Unix timestamps marking the query window
- duration_seconds: Total time span of the data
- start_value/end_value: Counter values at beginning and end (counters only increase)
- total: Final counter value (same as end_value)
- delta: How much the counter increased during the window (end_value - start_value)
- rate_per_second: Average rate of increase per second (delta / duration)
- rate_per_minute: Average rate of increase per minute (rate_per_second * 60)

Example interpretation: "The http_requests_total counter increased by {delta} requests over {duration_seconds} seconds, averaging {rate_per_second} requests/second or {rate_per_minute} requests/minute."
```

### Gauge Metrics
```
Analyze this Prometheus gauge metric summary:
{gauge_output}

Fields explained:
- count: Number of data points scraped
- start_timestamp/end_timestamp: Unix timestamps marking the query window
- duration_seconds: Total time span of the data
- start_value/end_value: Gauge values at beginning and end (gauges can go up or down)
- min/max: Lowest and highest values observed during the window
- mean: Average value across all data points
- median: Middle value when sorted (50th percentile)
- stddev: Standard deviation showing how much values vary
- trend: Classification of the gauge behavior (e.g., "rising", "falling", "stable", "fluctuating")
- change_over_window: Net change from start to end (end_value - start_value)

Example interpretation: "The memory_usage_bytes gauge ranged from {min} to {max} with an average of {mean}. It showed a {trend} pattern with a net {change_over_window} change."
```

### Histogram Metrics
```
Analyze this Prometheus histogram metric summary:
{histogram_output}

Fields explained:
- num_data_points: Number of times Prometheus scraped this metric
- start_timestamp/end_timestamp: Unix timestamps marking the query window
- duration_seconds: Total time span of the data
- count: Total number of observations (e.g., HTTP requests) recorded during the window
- sum: Sum of all observed values (e.g., total response time in seconds)
- avg: Average value per observation (sum / count)
- p50/p90/p95/p99: Percentiles showing distribution (e.g., p95=0.5 means 95% of requests took ≤0.5s)
- dominant_bucket: Bucket with the most observations (shows the most common value range)

Example interpretation: "Over {duration_seconds} seconds, {count} HTTP requests were observed with an average response time of {avg}s. 95% of requests completed in {p95}s or less, with most requests falling in the {dominant_bucket} bucket."
```

### Summary Metrics
```
Analyze this Prometheus summary metric summary:
{summary_output}

Fields explained:
- num_data_points: Number of times Prometheus scraped this metric
- start_timestamp/end_timestamp: Unix timestamps marking the query window
- duration_seconds: Total time span of the data
- count: Total number of observations recorded during the window
- sum: Sum of all observed values
- avg: Average value per observation (sum / count)
- quantiles: Pre-calculated percentiles from the application (e.g., {"0.5": 0.23, "0.9": 0.45, "0.99": 0.78})
  - Keys are quantile levels (0.5 = median, 0.9 = 90th percentile, etc.)
  - Values show that X% of observations were at or below this value

Example interpretation: "During {duration_seconds} seconds, {count} observations were recorded with an average of {avg}. The median (50th percentile) was {quantiles['0.5']}, and 99% of values were at or below {quantiles['0.99']}."
```

### Understanding count vs num_data_points
```
Key distinction for LLM analysis:

Counter/Gauge metrics:
- "count": How many times Prometheus scraped this metric (sampling frequency)
- Example: count=9 over 120 seconds means Prometheus scraped every ~13 seconds

Histogram/Summary metrics:
- "num_data_points": How many times Prometheus scraped the metric (sampling frequency)
- "count": How many observations/events were recorded (business metric)
- Example: num_data_points=9 (scraped 9 times), count=50000 (50k HTTP requests handled)

When analyzing: num_data_points/count tells you about the data collection frequency, while the "count" field in histograms/summaries tells you about actual system activity.
```

## License
Apache License 2.0.
