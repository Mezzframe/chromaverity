"""The input gate. These are the tests that keep agents and strangers out of places they shouldn't be."""

from pathlib import Path

import pytest

from chromaverity.safety import UnsafeInput, checked_media_path, ffmpeg_input


@pytest.mark.parametrize("bad", ["http://example.com/x.mp4", "concat:a.mp4|b.mp4", "pipe:0", "x\x00.mp4"])
def test_urls_protocols_and_nul_are_refused(bad):
    with pytest.raises(UnsafeInput):
        checked_media_path(bad)


def test_directories_and_missing_files_are_refused(tmp_path: Path):
    with pytest.raises(UnsafeInput):
        checked_media_path(tmp_path)
    with pytest.raises(UnsafeInput):
        checked_media_path(tmp_path / "nope.mp4")


def test_allowed_root_blocks_escape(tmp_path: Path):
    inside = tmp_path / "clips"
    inside.mkdir()
    ok = inside / "a.mp4"
    ok.write_bytes(b"x")
    outside = tmp_path / "secret.mp4"
    outside.write_bytes(b"x")
    assert checked_media_path(ok, allowed_root=inside) == ok.resolve()
    with pytest.raises(UnsafeInput):
        checked_media_path(outside, allowed_root=inside)
    with pytest.raises(UnsafeInput):
        checked_media_path(inside / ".." / "secret.mp4", allowed_root=inside)


def test_filenames_with_shell_characters_are_just_names(tmp_path: Path):
    weird = tmp_path / "a; rm -rf ~ $(whoami).mp4"
    weird.write_bytes(b"x")
    p = checked_media_path(weird)
    assert ffmpeg_input(p).startswith("file:/")


def test_mcp_refuses_paths_outside_root(tmp_path: Path):
    pytest.importorskip("mcp")
    import asyncio

    from chromaverity.mcp_server import build_server

    server = build_server(tmp_path)
    result = asyncio.run(server.call_tool("chromaverity_inspect", {"path": "/etc/passwd"}))
    assert "outside the allowed folder" in str(result)
