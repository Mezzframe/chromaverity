"""The input gate. These are the tests that keep agents and strangers out of places they shouldn't be."""

from pathlib import Path

import pytest

from chromaverity.safety import ToolError, UnsafeInput, checked_media_path, ffmpeg_input, run


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
    # Absolute path behind file:, whatever the OS ("file:/tmp/..." or "file:C:\\...").
    assert p.is_absolute()
    assert ffmpeg_input(p) == f"file:{p}"


def test_mcp_refuses_paths_outside_root(tmp_path: Path):
    pytest.importorskip("mcp")
    import asyncio

    from chromaverity.mcp_server import build_server

    server = build_server(tmp_path)
    result = asyncio.run(server.call_tool("chromaverity_inspect", {"path": "/etc/passwd"}))
    assert "outside the allowed folder" in str(result)


def test_symlink_inside_root_pointing_outside_is_refused(tmp_path: Path):
    inside = tmp_path / "clips"
    inside.mkdir()
    secret = tmp_path / "secret.mp4"
    secret.write_bytes(b"x")
    link = inside / "looks_fine.mp4"
    try:
        link.symlink_to(secret)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not available here")
    # The path is resolved before the root check, so the link's target is what gets judged.
    with pytest.raises(UnsafeInput):
        checked_media_path(link, allowed_root=inside)


def test_sibling_folder_with_same_prefix_is_outside_root(tmp_path: Path):
    root = tmp_path / "clips"
    sibling = tmp_path / "clips2"
    root.mkdir()
    sibling.mkdir()
    f = sibling / "a.mp4"
    f.write_bytes(b"x")
    # "clips2" starts with "clips"; a string-prefix check would wrongly allow it.
    with pytest.raises(UnsafeInput):
        checked_media_path(f, allowed_root=root)


def test_tilde_is_expanded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))  # Windows reads this one
    f = tmp_path / "a.mp4"
    f.write_bytes(b"x")
    assert checked_media_path("~/a.mp4") == f.resolve()


# ---- run(): the one function that starts processes

def test_run_times_out_with_a_readable_error():
    import sys

    with pytest.raises(ToolError, match="timed out"):
        run([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.5)


def test_run_reports_exit_code_and_stderr_tail():
    import sys

    with pytest.raises(ToolError, match="exited 3") as info:
        run([sys.executable, "-c", "import sys; sys.stderr.write('a\\nb\\nlast line\\n'); sys.exit(3)"])
    assert "last line" in str(info.value)


def test_run_decodes_utf8_whatever_the_console_code_page_is():
    """ffprobe writes UTF-8. A stream title like クリップ must come back intact, not crash."""
    import sys

    proc = run([sys.executable, "-c", "import sys; sys.stdout.buffer.write('クリップ'.encode('utf-8'))"])
    assert proc.stdout == "クリップ"


def test_run_replaces_undecodable_bytes_instead_of_raising():
    import sys

    proc = run([sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'ok\\xff\\xfe')"])
    assert proc.stdout.startswith("ok")


# ---- the nested-reference escape (measured on FFmpeg 9.0.2)

@pytest.mark.ffmpeg
def test_playlist_inside_root_cannot_read_files_outside_root(zoo, tmp_path: Path):
    """A playlist saved under --root with a playlist extension lists a file outside root.

    `-protocol_whitelist file` doesn't stop this: the entries are files too.
    `-format_whitelist` does, because the hls demuxer isn't on it. Without the
    guard, ffprobe returns the outside file's streams as if they were the
    playlist's own.
    """
    from chromaverity import report

    root = tmp_path / "root"
    root.mkdir()
    secret = zoo / "hd_labelled_601.mp4"  # outside root; distinctive label (bt470bg)
    playlist = root / "innocent.m3u8"
    playlist.write_text(
        "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:10\n"
        f"#EXTINF:2.0,\nfile:{secret}\n#EXT-X-ENDLIST\n"
    )
    with pytest.raises((ToolError, ValueError)) as info:
        report.inspect(checked_media_path(playlist, allowed_root=root), essence=False)
    assert "bt470bg" not in str(info.value)
