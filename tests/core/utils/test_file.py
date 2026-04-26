import os
import time
from pathlib import Path

import pytest

from viu_media.core.utils.file import AtomicWriter, FileLock, check_file_modified, sanitize_filename


def test_atomic_writer_writes_atomically(tmp_path: Path):
    target = tmp_path / "data.txt"

    with AtomicWriter(target, mode="w", encoding="utf-8") as handle:
        handle.write("hello world")

    assert target.read_text(encoding="utf-8") == "hello world"


def test_atomic_writer_cleans_temp_file_on_exception(tmp_path: Path):
    target = tmp_path / "data.txt"
    target.write_text("original", encoding="utf-8")

    with pytest.raises(RuntimeError, match="boom"):
        with AtomicWriter(target, mode="w", encoding="utf-8") as handle:
            handle.write("new")
            raise RuntimeError("boom")

    assert target.read_text(encoding="utf-8") == "original"
    assert list(tmp_path.glob("*.tmp")) == []


def test_file_lock_acquire_release_non_blocking(tmp_path: Path):
    lock_path = tmp_path / "my.lock"
    lock = FileLock(lock_path, timeout=0, stale_timeout=10)

    lock.acquire()
    assert lock_path.exists()

    lock.release()
    assert not lock_path.exists()


def test_file_lock_breaks_stale_lock(tmp_path: Path):
    lock_path = tmp_path / "stale.lock"
    lock_path.write_text("999999\n0", encoding="utf-8")
    stale_timestamp = time.time() - 100
    os.utime(lock_path, (stale_timestamp, stale_timestamp))

    lock = FileLock(lock_path, timeout=0.5, stale_timeout=0.01)
    lock.acquire()

    assert lock_path.exists()
    lock.release()
    assert not lock_path.exists()


def test_check_file_modified_detects_changes(tmp_path: Path):
    target = tmp_path / "track.txt"
    target.write_text("a", encoding="utf-8")
    previous_mtime = target.stat().st_mtime

    time.sleep(0.01)
    target.write_text("b", encoding="utf-8")

    current_mtime, modified = check_file_modified(target, previous_mtime)

    assert modified is True
    assert current_mtime > previous_mtime


def test_sanitize_filename_removes_invalid_characters():
    result = sanitize_filename('My:/Invalid*"Name?', restricted=False)

    assert "?" not in result
    assert "*" not in result
    assert result
