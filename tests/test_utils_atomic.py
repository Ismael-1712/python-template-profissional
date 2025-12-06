"""Unit tests for atomic file operations.

Tests cover:
- Happy path: successful atomic writes
- Sad path: exception handling and cleanup
- Race condition prevention
- POSIX compliance (fsync)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts.utils.atomic import AtomicFileWriter, atomic_write_json


class TestAtomicFileWriter:
    """Test suite for AtomicFileWriter context manager."""

    def test_atomic_write_success(self, tmp_path: Path) -> None:
        """Test successful atomic write operation."""
        target = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42}

        with AtomicFileWriter(target) as f:
            json.dump(test_data, f)

        # Verify file exists and contains correct data
        assert target.exists()
        with target.open() as f:
            loaded_data = json.load(f)
        assert loaded_data == test_data

    def test_atomic_write_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Test that parent directories are created automatically."""
        target = tmp_path / "subdir" / "nested" / "test.txt"

        with AtomicFileWriter(target) as f:
            f.write("test content")

        assert target.exists()
        assert target.read_text() == "test content"

    def test_atomic_write_replaces_existing_file(self, tmp_path: Path) -> None:
        """Test that existing files are replaced atomically."""
        target = tmp_path / "test.txt"
        target.write_text("old content")

        with AtomicFileWriter(target) as f:
            f.write("new content")

        assert target.read_text() == "new content"

    def test_temp_file_cleanup_on_exception(self, tmp_path: Path) -> None:
        """Test that temporary files are cleaned up on exceptions."""
        target = tmp_path / "test.txt"

        with pytest.raises(ValueError, match="Simulated error"):
            with AtomicFileWriter(target) as f:
                f.write("partial content")
                raise ValueError("Simulated error")

        # Original file should not exist (was never created)
        assert not target.exists()

        # Temporary file should be cleaned up
        temp_files = list(tmp_path.glob("*.tmp.*"))
        assert len(temp_files) == 0

    def test_original_file_unchanged_on_exception(self, tmp_path: Path) -> None:
        """Test that original file remains unchanged if write fails."""
        target = tmp_path / "test.txt"
        original_content = "original content"
        target.write_text(original_content)

        with pytest.raises(RuntimeError, match="Write failed"):
            with AtomicFileWriter(target) as f:
                f.write("new content")
                raise RuntimeError("Write failed")

        # Original file should be unchanged
        assert target.read_text() == original_content

    def test_fsync_called_when_enabled(self, tmp_path: Path, monkeypatch) -> None:
        """Test that fsync is called when fsync=True."""
        target = tmp_path / "test.txt"
        fsync_called = []

        original_fsync = os.fsync

        def mock_fsync(fd: int) -> None:
            fsync_called.append(fd)
            original_fsync(fd)

        monkeypatch.setattr(os, "fsync", mock_fsync)

        with AtomicFileWriter(target, fsync=True) as f:
            f.write("test")

        assert len(fsync_called) == 1

    def test_fsync_not_called_when_disabled(
        self,
        tmp_path: Path,
        monkeypatch,
    ) -> None:
        """Test that fsync is not called when fsync=False."""
        target = tmp_path / "test.txt"
        fsync_called = []

        def mock_fsync(fd: int) -> None:
            fsync_called.append(fd)

        monkeypatch.setattr(os, "fsync", mock_fsync)

        with AtomicFileWriter(target, fsync=False) as f:
            f.write("test")

        assert len(fsync_called) == 0

    def test_pid_based_temp_file_naming(self, tmp_path: Path) -> None:
        """Test that temporary files use PID to avoid race conditions."""
        target = tmp_path / "test.txt"

        # Start write but don't close
        writer = AtomicFileWriter(target)
        file_handle = writer.__enter__()
        file_handle.write("test")

        # Verify temp file exists with PID in name
        # The pattern is: filename.suffix.tmp.{PID} -> test.txt.tmp.{PID}
        # But with_suffix replaces, so it's actually: test.tmp.{PID}
        all_temp_files = list(tmp_path.glob("*.tmp.*"))
        assert len(all_temp_files) == 1
        assert str(os.getpid()) in str(all_temp_files[0])

        # Cleanup
        writer.__exit__(None, None, None)


class TestAtomicWriteJson:
    """Test suite for atomic_write_json convenience function."""

    def test_write_json_success(self, tmp_path: Path) -> None:
        """Test successful JSON write."""
        target = tmp_path / "data.json"
        test_data = {"status": "success", "count": 10}

        atomic_write_json(target, test_data)

        assert target.exists()
        with target.open() as f:
            loaded_data = json.load(f)
        assert loaded_data == test_data

    def test_write_json_with_unicode(self, tmp_path: Path) -> None:
        """Test JSON write with Unicode characters."""
        target = tmp_path / "unicode.json"
        test_data = {"message": "Olá Mundo! 你好世界"}

        atomic_write_json(target, test_data)

        with target.open(encoding="utf-8") as f:
            loaded_data = json.load(f)
        assert loaded_data == test_data

    def test_write_json_posix_newline(self, tmp_path: Path) -> None:
        """Test that JSON files end with newline (POSIX compliance)."""
        target = tmp_path / "data.json"
        atomic_write_json(target, {"key": "value"})

        content = target.read_text()
        assert content.endswith("\n")

    def test_write_json_fsync_enabled_by_default(
        self,
        tmp_path: Path,
        monkeypatch,
    ) -> None:
        """Test that fsync is enabled by default."""
        target = tmp_path / "data.json"
        fsync_called = []

        original_fsync = os.fsync

        def mock_fsync(fd: int) -> None:
            fsync_called.append(fd)
            original_fsync(fd)

        monkeypatch.setattr(os, "fsync", mock_fsync)

        atomic_write_json(target, {"test": "data"})

        assert len(fsync_called) == 1

    def test_write_json_fsync_can_be_disabled(
        self,
        tmp_path: Path,
        monkeypatch,
    ) -> None:
        """Test that fsync can be disabled."""
        target = tmp_path / "data.json"
        fsync_called = []

        def mock_fsync(fd: int) -> None:
            fsync_called.append(fd)

        monkeypatch.setattr(os, "fsync", mock_fsync)

        atomic_write_json(target, {"test": "data"}, fsync=False)

        assert len(fsync_called) == 0


class TestRaceConditionPrevention:
    """Test suite for race condition scenarios."""

    def test_concurrent_writes_different_files(self, tmp_path: Path) -> None:
        """Test that concurrent writes to different files don't interfere."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"

        with AtomicFileWriter(file1) as f1:
            f1.write("content1")
            # Simulate concurrent write
            with AtomicFileWriter(file2) as f2:
                f2.write("content2")

        assert file1.read_text() == "content1"
        assert file2.read_text() == "content2"

    def test_exception_doesnt_affect_other_writes(self, tmp_path: Path) -> None:
        """Test that exception in one write doesn't affect others."""
        successful_file = tmp_path / "success.txt"
        failed_file = tmp_path / "failed.txt"

        # Successful write
        with AtomicFileWriter(successful_file) as f:
            f.write("success")

        # Failed write
        with pytest.raises(ValueError), AtomicFileWriter(failed_file) as f:
            f.write("partial")
            raise ValueError("Simulated error")

        # Successful file should be intact
        assert successful_file.exists()
        assert successful_file.read_text() == "success"

        # Failed file should not exist
        assert not failed_file.exists()
