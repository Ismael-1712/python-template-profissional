#!/usr/bin/env python3
"""Performance Benchmark Script for CORTEX KnowledgeScanner.

This script measures the real-world performance of KnowledgeScanner's
parallel processing implementation across different dataset sizes.

Methodology:
    - Creates temporary isolated environment with tempfile.TemporaryDirectory
    - Generates realistic Markdown files with YAML frontmatter
    - Measures scan time using time.perf_counter() for precision
    - Tests scenarios: 10, 50, 100, and 500 files
    - Compares sequential vs parallel processing when applicable

Metrics:
    - Total scan time (seconds)
    - Files per second throughput
    - Speedup factor (when both modes available)

Usage:
    python scripts/benchmark_cortex_perf.py

Author: Performance Engineering Team
Date: 2025-12-17
"""

from __future__ import annotations

import os
import platform
import tempfile
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch

from scripts.core.cortex.knowledge_scanner import KnowledgeScanner
from scripts.utils.filesystem import RealFileSystem


def generate_dataset(root: Path, count: int) -> Path:
    """Generate a dataset of valid Markdown files with frontmatter.

    Creates a knowledge directory structure with the specified number
    of Markdown files, each containing realistic YAML frontmatter and content.

    Args:
        root: Root directory for dataset generation
        count: Number of Markdown files to create

    Returns:
        Path to the generated knowledge directory
    """
    knowledge_dir = root / "docs" / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)

    for i in range(count):
        file_path = knowledge_dir / f"article_{i:04d}.md"

        # Generate realistic frontmatter
        content = f"""---
id: kno-{i:04d}
title: Knowledge Article {i}
description: Performance benchmark test article number {i}
type: guide
version: 1.0.0
status: active
tags: [benchmark, testing, performance, cortex]
author: Benchmark Generator
date: 2025-12-17
---

# Article {i}

This is a test article for performance benchmarking of the CORTEX KnowledgeScanner.

## Overview

The KnowledgeScanner implements parallel processing for scanning large knowledge bases.
This article is part of a synthetic dataset used to measure real-world performance.

## Links for Testing

- [Internal Link](./article_{(i + 1) % count:04d}.md)
- [External Link](https://example.com/article-{i})
- [Documentation](../../architecture/PERFORMANCE_NOTES.md)

## Content

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris.

### Section {i}.1

Additional content to make the file more realistic and test parsing performance
with a reasonable amount of text.

### Section {i}.2

More content to simulate real documentation files with multiple sections and
varying content lengths.

---

**Last Updated:** 2025-12-17
**Article ID:** kno-{i:04d}
"""
        file_path.write_text(content, encoding="utf-8")

    return knowledge_dir


def measure_scan(
    count: int,
    force_sequential: bool = False,
) -> dict[str, Any]:
    """Measure KnowledgeScanner performance for a given file count.

    Creates a temporary environment, generates dataset, and measures
    the time taken to scan all files.

    Args:
        count: Number of files to generate and scan
        force_sequential: Force sequential processing (bypass parallel threshold)

    Returns:
        Dictionary with metrics:
            - file_count: Number of files processed
            - total_time: Total scan time in seconds
            - files_per_second: Throughput metric
            - mode: 'sequential' or 'parallel'
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)

        # Generate dataset
        knowledge_dir = generate_dataset(tmp_root, count)

        # Initialize scanner with real filesystem
        scanner = KnowledgeScanner(
            workspace_root=tmp_root,
            fs=RealFileSystem(),
        )

        # Measure scan time
        if force_sequential:
            # Patch os.cpu_count to force sequential mode
            # (only 1 CPU means ThreadPoolExecutor creates 1 worker = sequential)
            with patch("os.cpu_count", return_value=1):
                start = time.perf_counter()
                entries = scanner.scan(knowledge_dir)
                end = time.perf_counter()
        else:
            start = time.perf_counter()
            entries = scanner.scan(knowledge_dir)
            end = time.perf_counter()

        total_time = end - start
        files_per_second = count / total_time if total_time > 0 else 0

        # Determine actual mode used
        mode = "sequential" if (force_sequential or count < 10) else "parallel"

        return {
            "file_count": count,
            "entries_parsed": len(entries),
            "total_time": total_time,
            "files_per_second": files_per_second,
            "mode": mode,
        }


def run_benchmarks() -> None:
    """Run comprehensive performance benchmarks and display results."""
    print("=" * 80)
    print("CORTEX KnowledgeScanner - Performance Benchmark Suite")
    print("=" * 80)
    print()
    print("System Information:")
    print(f"  Platform: {platform.system()} {platform.release()}")
    print(f"  Machine: {platform.machine()}")
    print(f"  Processor: {platform.processor()}")
    print(f"  CPU Count: {os.cpu_count()}")
    print(f"  Python: {platform.python_version()}")
    print()
    print("Running benchmarks (5 iterations per scenario)...")
    print()

    # Test scenarios
    scenarios: list[dict[str, int | str]] = [
        {"count": 10, "desc": "Small dataset (threshold test)"},
        {"count": 50, "desc": "Medium dataset"},
        {"count": 100, "desc": "Large dataset"},
        {"count": 500, "desc": "Very large dataset"},
    ]

    results: list[dict[str, Any]] = []

    for scenario in scenarios:
        count = scenario["count"]
        desc = scenario["desc"]

        # Type narrowing for mypy
        assert isinstance(count, int)
        assert isinstance(desc, str)

        print(f"📊 Benchmarking: {desc} ({count} files)")

        # Run 5 iterations and take average
        iterations = 5
        parallel_times: list[float] = []
        sequential_times: list[float] = []

        for i in range(iterations):
            print(f"  ⏱️  Iteration {i + 1}/{iterations}...", end=" ", flush=True)

            # Measure parallel (or auto-selected mode)
            result_parallel = measure_scan(count, force_sequential=False)
            parallel_times.append(result_parallel["total_time"])

            # For datasets >= 10, also measure forced sequential for comparison
            if count >= 10:
                result_sequential = measure_scan(count, force_sequential=True)
                sequential_times.append(result_sequential["total_time"])
                print(
                    f"Parallel: {result_parallel['total_time']:.4f}s, "
                    f"Sequential: {result_sequential['total_time']:.4f}s"
                )
            else:
                print(f"Sequential: {result_parallel['total_time']:.4f}s")

        # Calculate averages
        avg_parallel = sum(parallel_times) / len(parallel_times)
        avg_sequential = (
            sum(sequential_times) / len(sequential_times)
            if sequential_times
            else avg_parallel
        )

        speedup = avg_sequential / avg_parallel if avg_parallel > 0 else 1.0
        overhead = (avg_parallel - avg_sequential) if count < 10 else 0.0

        results.append(
            {
                "count": count,
                "sequential_ms": avg_sequential * 1000,
                "parallel_ms": avg_parallel * 1000,
                "speedup": speedup,
                "overhead_ms": overhead * 1000,
            }
        )

        print()

    # Display results table
    print("=" * 80)
    print("RESULTS - Average over 5 iterations")
    print("=" * 80)
    print()
    print("| File Count | Sequential | Parallel (4 workers) | Speedup | Overhead |")
    print("|------------|-----------|----------------------|---------|----------|")

    for result in results:
        count = result["count"]
        seq_ms = result["sequential_ms"]
        par_ms = result["parallel_ms"]
        speedup = result["speedup"]
        overhead = result["overhead_ms"]

        if count < 10:
            # Sequential mode only
            print(
                f"| {count:>10} files | {seq_ms:>7.2f} ms | "
                f"{'N/A (sequential)':^20} | {'N/A':^7} | {overhead:>6.2f} ms |"
            )
        else:
            # Both modes
            print(
                f"| {count:>10} files | {seq_ms:>7.2f} ms | {par_ms:>18.2f} ms | "
                f"{speedup:>6.2f}x | {overhead:>6.2f} ms |"
            )

    print()
    print("=" * 80)
    print("Benchmark complete!")
    print()
    print("Notes:")
    print("  - Speedup = Sequential Time / Parallel Time")
    print(
        "  - Overhead = Additional cost of parallel processing (negative for <10 files)"
    )
    print("  - Files < 10 use sequential mode automatically (threshold optimization)")
    print()
    print("📝 Copy the table above to docs/architecture/PERFORMANCE_NOTES.md")
    print("=" * 80)


if __name__ == "__main__":
    run_benchmarks()
