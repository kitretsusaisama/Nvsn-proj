import pytest
import asyncio
from pathlib import Path
from nvsn.core.tools import FileSystem

@pytest.fixture
def temp_sandbox(tmp_path):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    (sandbox / "allowed.txt").write_text("allowed content")
    return sandbox

def run_async(coro):
    return asyncio.run(coro)

def test_file_system_read_allowed(temp_sandbox):
    fs = FileSystem(base_path=str(temp_sandbox))
    result = run_async(fs.run(operation="read", path="allowed.txt"))
    assert result == "allowed content"

def test_file_system_read_traversal_relative(temp_sandbox, tmp_path):
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("secret content")

    fs = FileSystem(base_path=str(temp_sandbox))
    # Attempt to go up to tmp_path
    result = run_async(fs.run(operation="read", path="../secret.txt"))
    assert "Error: Path traversal detected" in result

def test_file_system_read_traversal_absolute(temp_sandbox):
    fs = FileSystem(base_path=str(temp_sandbox))
    # This might vary depending on environment, but /etc/hostname should exist and be outside
    result = run_async(fs.run(operation="read", path="/etc/hostname"))
    assert "Error: Path traversal detected" in result

def test_file_system_write_allowed(temp_sandbox):
    fs = FileSystem(base_path=str(temp_sandbox))
    result = run_async(fs.run(operation="write", path="new_file.txt", content="new content"))
    assert result == "File written."
    assert (temp_sandbox / "new_file.txt").read_text() == "new content"

def test_file_system_write_traversal(temp_sandbox, tmp_path):
    fs = FileSystem(base_path=str(temp_sandbox))
    result = run_async(fs.run(operation="write", path="../malicious.txt", content="malicious"))
    assert "Error: Path traversal detected" in result
    assert not (tmp_path / "malicious.txt").exists()

def test_file_system_subdir_allowed(temp_sandbox):
    fs = FileSystem(base_path=str(temp_sandbox))
    result = run_async(fs.run(operation="write", path="subdir/file.txt", content="subdir content"))
    assert result == "File written."
    assert (temp_sandbox / "subdir" / "file.txt").read_text() == "subdir content"

    read_result = run_async(fs.run(operation="read", path="subdir/file.txt"))
    assert read_result == "subdir content"
