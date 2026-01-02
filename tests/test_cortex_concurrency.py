"""Concurrency Tests for CORTEX Knowledge Scanner.

This module tests the thread-safety of the KnowledgeScanner when processing
files in parallel using ThreadPoolExecutor. It validates that:
- Parallel processing returns identical results to sequential processing
- The MemoryFileSystem is thread-safe under concurrent access
- The parallelization threshold (10 files) works correctly
- Results are deterministic across multiple runs

Author: SRE & QA Engineering Team
License: MIT
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from scripts.core.cortex.knowledge_scanner import KnowledgeScanner
from scripts.core.cortex.models import DocStatus, KnowledgeEntry
from scripts.utils.filesystem import MemoryFileSystem


@pytest.fixture
def large_knowledge_base() -> tuple[MemoryFileSystem, int, Path]:
    """Create in-memory filesystem with 50 valid knowledge files.

    Returns:
        Tuple of (filesystem, expected_count, workspace_root)
    """
    fs = MemoryFileSystem()
    workspace_root = Path("/test_workspace")
    knowledge_dir = workspace_root / "docs" / "knowledge"

    # Create 50 valid knowledge entries
    for i in range(50):
        content = f"""---
id: kno-{i:03d}
status: active
tags: [test, concurrency, batch-{i // 10}]
golden_paths: [/docs/knowledge/entry_{i:03d}.md]
sources:
  - type: documentation
    url: https://example.com/doc-{i}
    reliability: high
---
# Knowledge Entry {i}

This is test content for concurrent scanning validation.
Entry number: {i}

## Related Entries
- [[kno-{max(0, i - 1):03d}]] (Previous)
- [[kno-{min(49, i + 1):03d}]] (Next)
"""
        fs.write_text(knowledge_dir / f"entry_{i:03d}.md", content)

    return fs, 50, workspace_root


@pytest.fixture
def small_knowledge_base() -> tuple[MemoryFileSystem, int, Path]:
    """Create in-memory filesystem with 9 files (below parallel threshold).

    Returns:
        Tuple of (filesystem, expected_count, workspace_root)
    """
    fs = MemoryFileSystem()
    workspace_root = Path("/test_workspace")
    knowledge_dir = workspace_root / "docs" / "knowledge"

    # Create 9 files to test sequential processing
    for i in range(9):
        content = f"""---
id: kno-seq-{i:03d}
status: active
tags: [test, sequential]
---
# Sequential Entry {i}
"""
        fs.write_text(knowledge_dir / f"seq_{i:03d}.md", content)

    return fs, 9, workspace_root


class TestKnowledgeScannerConcurrency:
    """Test suite for KnowledgeScanner parallelization and thread-safety."""

    def test_parallel_integrity(
        self,
        large_knowledge_base: tuple[MemoryFileSystem, int, Path],
    ) -> None:
        """Validate that parallel scan returns correct number of entries.

        This test ensures that the ThreadPoolExecutor-based scanning
        processes all files exactly once, with no duplicates or missing entries.
        """
        fs, expected_count, workspace_root = large_knowledge_base
        scanner = KnowledgeScanner(workspace_root=workspace_root, fs=fs)

        # Run parallel scan (triggers when >= 10 files)
        entries = scanner.scan()

        # Validations
        assert len(entries) == expected_count, (
            f"Expected {expected_count} entries, got {len(entries)}"
        )

        # Verify all IDs are unique (no duplicates from race conditions)
        entry_ids = [e.id for e in entries]
        assert len(entry_ids) == len(set(entry_ids)), (
            "Duplicate entries detected in parallel scan"
        )

        # Verify all expected IDs are present
        expected_ids = {f"kno-{i:03d}" for i in range(50)}
        actual_ids = {e.id for e in entries}
        assert actual_ids == expected_ids, (
            f"Missing or extra IDs. Difference: {expected_ids ^ actual_ids}"
        )

    def test_concurrent_scans_shared_filesystem(
        self,
        large_knowledge_base: tuple[MemoryFileSystem, int, Path],
    ) -> None:
        """Stress test: Multiple concurrent scans on the same MemoryFileSystem.

        This validates that the MemoryFileSystem's RLock prevents race conditions
        when multiple threads read simultaneously.
        """
        fs, expected_count, workspace_root = large_knowledge_base

        def run_scan() -> list[KnowledgeEntry]:
            """Execute a single scan and return entries."""
            scanner = KnowledgeScanner(workspace_root=workspace_root, fs=fs)
            return scanner.scan()

        # Run 4 parallel scans using the SAME filesystem instance
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(run_scan) for _ in range(4)]
            results = [future.result() for future in futures]

        # All 4 scans should return the same count
        for i, result in enumerate(results):
            assert len(result) == expected_count, (
                f"Scan {i} returned {len(result)} entries, expected {expected_count}"
            )

        # All scans should return the same set of IDs
        id_sets = [set(e.id for e in result) for result in results]
        assert len(set(map(frozenset, id_sets))) == 1, (
            "Different scans returned different sets of IDs (race condition detected)"
        )

    def test_parallel_determinism(
        self,
        large_knowledge_base: tuple[MemoryFileSystem, int, Path],
    ) -> None:
        """Verify that parallel scanning produces deterministic results.

        Running the same scan multiple times should always return the same
        set of entries (order may vary due to parallel processing).
        """
        fs, expected_count, workspace_root = large_knowledge_base
        scanner = KnowledgeScanner(workspace_root=workspace_root, fs=fs)

        # Run scan 10 times
        results = [scanner.scan() for _ in range(10)]

        # Extract ID sets from each run
        id_sets = [set(e.id for e in result) for result in results]

        # All runs should produce the same set of IDs
        assert len(set(map(frozenset, id_sets))) == 1, (
            "Scan results are non-deterministic across multiple runs"
        )

        # All runs should have the same count
        assert all(len(result) == expected_count for result in results), (
            "Different runs returned different entry counts"
        )

    def test_threshold_sequential_processing(
        self,
        small_knowledge_base: tuple[MemoryFileSystem, int, Path],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Validate that files below threshold use sequential processing.

        With 9 files (< 10), the scanner should log "sequential processing"
        and avoid ThreadPoolExecutor overhead.
        """
        fs, expected_count, workspace_root = small_knowledge_base

        # Enable DEBUG logging to capture processing mode
        caplog.set_level(logging.DEBUG)

        scanner = KnowledgeScanner(workspace_root=workspace_root, fs=fs)
        entries = scanner.scan()

        # Verify sequential processing was used
        assert any(
            "sequential processing" in record.message.lower()
            for record in caplog.records
        ), "Expected 'sequential processing' log message for 9 files"

        # Verify correct count
        assert len(entries) == expected_count, (
            f"Sequential scan should return {expected_count} entries"
        )

    def test_threshold_parallel_processing(
        self,
        large_knowledge_base: tuple[MemoryFileSystem, int, Path],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Validate that parallel processing is DISABLED (performance fix).

        As of v0.1.0, parallel processing is disabled due to GIL overhead
        causing 34% performance regression. All workloads use sequential mode.

        This test now verifies that even with 50 files (previously >= 10
        triggered parallel), sequential processing is used.
        """
        fs, expected_count, workspace_root = large_knowledge_base

        # Enable DEBUG logging to capture processing mode
        caplog.set_level(logging.DEBUG)

        scanner = KnowledgeScanner(workspace_root=workspace_root, fs=fs)
        entries = scanner.scan()

        # Verify SEQUENTIAL processing is now used (parallel disabled)
        assert any(
            "sequential processing" in record.message.lower()
            for record in caplog.records
        ), "Expected 'sequential processing' log (parallel disabled in v0.1.0)"

        # Verify NO worker count is mentioned (no parallel execution)
        assert not any(
            "workers" in record.message.lower() for record in caplog.records
        ), "Workers should NOT be mentioned (parallel mode disabled)"

        # Verify correct count
        assert len(entries) == expected_count, (
            f"Sequential scan should return {expected_count} entries"
        )

    def test_malformed_files_dont_block_parallel_scan(
        self,
        large_knowledge_base: tuple[MemoryFileSystem, int, Path],
    ) -> None:
        """Verify that malformed files are skipped without stopping parallel scan.

        Adding invalid files should not prevent successful parsing of valid ones.
        """
        fs, expected_valid_count, workspace_root = large_knowledge_base
        knowledge_dir = workspace_root / "docs" / "knowledge"

        # Add 5 malformed files
        for i in range(5):
            malformed_content = f"""---
# BROKEN YAML - missing closing ---
id: malformed-{i}
status: invalid
This is not valid frontmatter
# Some content
"""
            fs.write_text(knowledge_dir / f"malformed_{i}.md", malformed_content)

        scanner = KnowledgeScanner(workspace_root=workspace_root, fs=fs)
        entries = scanner.scan()

        # Should still get all 50 valid entries (malformed are logged but skipped)
        assert len(entries) == expected_valid_count, (
            f"Expected {expected_valid_count} valid entries despite malformed files"
        )

    def test_parallel_scan_with_mixed_statuses(
        self,
        large_knowledge_base: tuple[MemoryFileSystem, int, Path],
    ) -> None:
        """Test parallel scanning with files having different status values.

        Ensures that status enum conversion works correctly in parallel.
        """
        fs, _, workspace_root = large_knowledge_base
        knowledge_dir = workspace_root / "docs" / "knowledge"

        # Add files with different statuses
        statuses = ["active", "draft", "deprecated", "archived"]
        for i, status in enumerate(statuses):
            content = f"""---
id: status-test-{i}
status: {status}
tags: [test]
---
# Status Test {i}
"""
            fs.write_text(knowledge_dir / f"status_{status}.md", content)

        scanner = KnowledgeScanner(workspace_root=workspace_root, fs=fs)
        entries = scanner.scan()

        # Find the status test entries
        status_entries = [e for e in entries if e.id.startswith("status-test-")]

        assert len(status_entries) == 4, "Should find all 4 status test entries"

        # Verify statuses were parsed correctly
        found_statuses = {e.status for e in status_entries}
        expected_statuses = {
            DocStatus.ACTIVE,
            DocStatus.DRAFT,
            DocStatus.DEPRECATED,
            DocStatus.ARCHIVED,
        }
        assert found_statuses == expected_statuses, (
            "Not all status types were parsed correctly"
        )


class TestMemoryFileSystemThreadSafety:
    """Direct tests for MemoryFileSystem thread-safety guarantees."""

    def test_concurrent_writes_different_files(self) -> None:
        """Verify concurrent writes to different files don't interfere.

        Multiple threads writing different files simultaneously should
        all succeed without data loss.
        """
        fs = MemoryFileSystem()

        def write_file(index: int) -> None:
            """Write a unique file."""
            fs.write_text(Path(f"file_{index}.txt"), f"content_{index}")

        # Write 100 files concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(write_file, i) for i in range(100)]
            # Wait for all writes to complete
            for future in futures:
                future.result()

        # Verify all 100 files were written
        for i in range(100):
            assert fs.exists(Path(f"file_{i}.txt")), f"File {i} was not written"
            assert fs.read_text(Path(f"file_{i}.txt")) == f"content_{i}", (
                f"File {i} has incorrect content"
            )

    def test_concurrent_reads_same_file(self) -> None:
        """Verify concurrent reads of the same file are safe.

        Multiple threads reading the same file simultaneously should
        all get consistent data.
        """
        fs = MemoryFileSystem()
        test_content = "shared content for concurrent reads"
        fs.write_text(Path("shared.txt"), test_content)

        def read_file() -> str:
            """Read the shared file."""
            return fs.read_text(Path("shared.txt"))

        # Read same file 50 times concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(read_file) for _ in range(50)]
            results = [future.result() for future in futures]

        # All reads should return the same content
        assert all(r == test_content for r in results), (
            "Concurrent reads returned inconsistent data"
        )

    def test_concurrent_glob_operations(self) -> None:
        """Verify concurrent glob operations don't cause race conditions.

        Multiple threads searching for files simultaneously should
        all get consistent results.
        """
        fs = MemoryFileSystem()

        # Create 20 Python files
        for i in range(20):
            fs.write_text(Path(f"src/module_{i}.py"), f"# Module {i}")

        def search_files() -> list[Path]:
            """Search for Python files."""
            return list(fs.rglob(Path("src"), "*.py"))

        # Run 10 concurrent searches
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(search_files) for _ in range(10)]
            results = [future.result() for future in futures]

        # All searches should return the same 20 files
        assert all(len(r) == 20 for r in results), (
            "Concurrent glob operations returned inconsistent counts"
        )

        # All searches should return the same set of paths
        path_sets = [set(r) for r in results]
        assert len(set(map(frozenset, path_sets))) == 1, (
            "Concurrent glob operations returned different file sets"
        )
