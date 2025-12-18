---
id: cortex-parallel-mode-guide
title: Cortex Scanner - Parallel Processing Guide
description: Guide for using experimental parallel processing in Cortex Knowledge Scanner
type: guide
status: active
version: 1.0.0
author: Engineering Team
date: 2025-12-18
created: 2025-12-18
updated: 2025-12-18
tags:
  - cortex
  - performance
  - cli
  - knowledge-scanner
related:
  - docs/architecture/PERFORMANCE_NOTES.md
  - scripts/core/cortex/knowledge_scanner.py
  - scripts/cli/cortex.py
---

# Cortex Scanner - Parallel Processing Guide

## Overview

The Cortex Knowledge Scanner includes an **experimental parallel processing mode** that can be enabled via CLI flag. This guide explains when to use it, how it works, and its performance implications.

## Background: The "Tool Blindness" Problem

Previously, the parallel processing feature was **hardcoded to be disabled** (`parallel_threshold = sys.maxsize`) due to measured performance regressions on typical systems. However, this violated the principle of **user autonomy**:

- Users with high-performance hardware couldn't access the feature
- Users with large datasets (1000+ files) had no opt-in mechanism
- The feature existed in code but was invisible to end users

This update exposes the configuration to restore user control.

## Usage

### Enable Parallel Mode

```bash
cortex knowledge-scan --parallel
```

**Alternative flag:**

```bash
cortex knowledge-scan --experimental-parallel
```

### Standard Mode (Default)

```bash
cortex knowledge-scan
```

Runs in sequential mode (no parallelism).

## When to Use Parallel Mode

### ✅ **Use When:**

- Processing **500+ knowledge entries**
- Running on **high-performance hardware** (32+ cores, NVMe storage)
- Benchmarking or performance testing
- Working with datasets where I/O dominates CPU parsing time

### ❌ **Avoid When:**

- Processing **< 100 files** (thread overhead exceeds gains)
- Running on **low-core machines** (< 4 cores)
- Using **traditional HDDs** (GIL contention + slow I/O)
- In CI/CD pipelines where consistency > speed

## Performance Characteristics

### Benchmarks (Reference Hardware: WSL2, 16 cores)

| File Count | Sequential | Parallel | Speedup |
|------------|-----------|----------|---------|
| 10         | 0.05s     | 0.08s    | 0.62x   |
| 50         | 0.23s     | 0.35s    | 0.66x   |
| 100        | 0.46s     | 0.69s    | 0.67x   |
| 500        | 2.31s     | 3.48s    | 0.66x   |

**Key Finding:** Parallel mode shows **~34% performance regression** due to:

1. **GIL (Global Interpreter Lock)** contention
2. **CPU-bound parsing** (YAML frontmatter, Markdown)
3. **Thread overhead** exceeds I/O gains

### Why Is It Slower?

Python's GIL prevents true parallelism for CPU-bound tasks. Since:

- Parsing YAML frontmatter is **CPU-bound**
- Markdown content extraction is **CPU-bound**
- File I/O is already buffered and fast (modern SSDs)

→ Threading adds overhead without reducing wall-clock time.

## Visual Feedback

### Sequential Mode (Default)

```
🧠 Knowledge Base Scanner
Workspace: /home/user/project
Knowledge Directory: docs/knowledge/

📋 Mode: Standard Sequential

✅ Found 42 knowledge entries
```

### Parallel Mode (--parallel)

```
🧠 Knowledge Base Scanner
Workspace: /home/user/project
Knowledge Directory: docs/knowledge/

⚡ Mode: EXPERIMENTAL PARALLEL
   (GIL may impact performance on some systems)

🚀 Running in EXPERIMENTAL PARALLEL mode (4 workers)
✅ Found 42 knowledge entries
```

## Technical Implementation

### Scanner API

```python
from scripts.core.cortex.knowledge_scanner import KnowledgeScanner
from pathlib import Path

# Sequential mode (default)
scanner = KnowledgeScanner(workspace_root=Path.cwd())
entries = scanner.scan()

# Parallel mode
scanner = KnowledgeScanner(
    workspace_root=Path.cwd(),
    force_parallel=True  # Enable experimental parallel processing
)
entries = scanner.scan()
```

### Threshold Logic

```python
if self.force_parallel:
    parallel_threshold = 10  # Use parallelism for 10+ files
else:
    parallel_threshold = sys.maxsize  # Never use parallelism (sequential)
```

### Worker Count

```python
max_workers = min(4, os.cpu_count() or 1)
```

Capped at **4 workers** to limit GIL contention.

## Logging Behavior

### Sequential Mode

```
DEBUG: Running in standard sequential mode (42 files)
```

### Parallel Mode

```
INFO: 🚀 Running in EXPERIMENTAL PARALLEL mode (4 workers)
DEBUG: Processing 42 files with 4 workers (GIL may impact performance)
```

## Future Improvements

See [PERFORMANCE_NOTES.md](../architecture/PERFORMANCE_NOTES.md) for roadmap:

1. **P0:** Keep parallel mode opt-in (✅ Done)
2. **P1:** Implement `multiprocessing` instead of `threading`
3. **P2:** Use Rust extension for YAML parsing (bypasses GIL)
4. **P3:** Implement adaptive mode selection based on file count

## FAQ

### Q: Why is parallel mode slower?

**A:** Python's GIL prevents true parallelism. YAML parsing is CPU-bound, so threads compete for the lock.

### Q: Will this ever be faster?

**A:** Yes, if we migrate to `multiprocessing.Pool` (bypasses GIL) or Rust extensions.

### Q: Should I use --parallel in CI?

**A:** No. Sequential mode is faster and more predictable.

### Q: Can I force parallel mode for testing?

**A:** Yes, that's exactly what `--parallel` is for. Useful for benchmarking different hardware.

## References

- [Performance Benchmarks](../architecture/PERFORMANCE_NOTES.md)
- [KnowledgeScanner Source](../../scripts/core/cortex/knowledge_scanner.py)
- [CLI Implementation](../../scripts/cli/cortex.py)
- [Python GIL Documentation](https://docs.python.org/3/c-api/init.html#thread-state-and-the-global-interpreter-lock)

---

**Last Updated:** 2025-12-18
**Status:** Active
**Maintainer:** Engineering Team
