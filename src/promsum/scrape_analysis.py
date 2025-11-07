"""Scrape interval analysis utilities."""
from typing import List, Dict, Any, Optional
import statistics


def analyze_scrape_intervals(
    timestamps: List[float],
    values: List[float],
    is_counter: bool = False
) -> Dict[str, Any]:
    """
    Analyze scrape intervals and detect missed scrapes.
    
    Args:
        timestamps: List of Unix timestamps
        values: List of metric values
        is_counter: Whether this is a counter metric (for reset detection)
    
    Returns:
        Dictionary with:
        - expected_interval_seconds: Median interval between scrapes
        - missed_scrapes: Estimated number of missed scrapes
        - scrape_regularity: Classification of scrape regularity
        - scrape_regularity_cv: Coefficient of variation of intervals
        - counter_resets_detected: (counter only) Whether resets were found
        - total_gaps: Number of gaps analyzed
        - irregular_gaps: Number of gaps exceeding threshold
    """
    if len(timestamps) < 2:
        return {
            "expected_interval_seconds": None,
            "missed_scrapes": None,
            "scrape_regularity": "insufficient_data",
            "scrape_regularity_cv": None,
            "counter_resets_detected": None if is_counter else None,
            "total_gaps": 0,
            "irregular_gaps": 0,
        }
    
    # Calculate all intervals
    intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps) - 1)]
    
    # Detect counter resets (value decreases)
    counter_resets = 0
    if is_counter:
        for i in range(len(values) - 1):
            if values[i+1] < values[i]:
                counter_resets += 1
    
    # Calculate median interval (robust against outliers)
    median_interval = statistics.median(intervals)
    
    # Calculate scrape regularity using coefficient of variation
    if len(intervals) > 1:
        mean_interval = statistics.mean(intervals)
        stddev_interval = statistics.stdev(intervals)
        cv = stddev_interval / mean_interval if mean_interval > 0 else 0
        
        if cv < 0.1:
            regularity = "regular"
        elif cv < 0.3:
            regularity = "mostly_regular"
        else:
            regularity = "irregular"
    else:
        regularity = "single_interval"
        cv = 0.0
    
    # Detect missed scrapes
    # Threshold: gap is considered irregular if > 1.5x median
    threshold = 1.5
    missed_scrapes = 0
    irregular_gaps = 0
    
    for interval in intervals:
        if interval > (median_interval * threshold):
            irregular_gaps += 1
            # Estimate missed scrapes in this gap
            estimated_missed = int((interval - median_interval) / median_interval)
            missed_scrapes += estimated_missed
    
    return {
        "expected_interval_seconds": round(median_interval, 2),
        "missed_scrapes": missed_scrapes,
        "scrape_regularity": regularity,
        "scrape_regularity_cv": round(cv, 3),
        "counter_resets_detected": counter_resets if is_counter else None,
        "total_gaps": len(intervals),
        "irregular_gaps": irregular_gaps,
    }
