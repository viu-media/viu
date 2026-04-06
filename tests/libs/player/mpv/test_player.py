from types import SimpleNamespace
from unittest.mock import patch

import pytest

from viu_media.core.config import MpvConfig
from viu_media.core.exceptions import ViuError
from viu_media.libs.player.mpv.player import MpvPlayer
from viu_media.libs.player.params import PlayerParams


def _make_config(args: str = "", pre_args: str = ""):
    return MpvConfig(args=args, pre_args=pre_args)


def _make_params(url: str, **overrides):
    base = {
        "url": url,
        "title": "Episode Title",
        "query": "query",
        "episode": "1",
        "syncplay": False,
        "subtitles": None,
        "headers": None,
        "start_time": None,
    }
    base.update(overrides)
    return PlayerParams(**base)


def test_create_mpv_cli_options_builds_all_supported_flags():
    with patch("viu_media.libs.player.mpv.player.shutil.which", return_value="mpv"):
        player = MpvPlayer(_make_config(args="--force-window=yes,--quiet"))

    params = _make_params(
        "https://example.com/video.m3u8",
        headers={"Referer": "https://example.com", "User-Agent": "ua"},
        subtitles=["sub1.srt", "sub2.srt"],
        start_time="00:01:05",
        title="My Show",
    )

    options = player._create_mpv_cli_options(params)

    assert "--http-header-fields=Referer:https://example.com,User-Agent:ua" in options
    assert "--sub-file=sub1.srt" in options
    assert "--sub-file=sub2.srt" in options
    assert "--start=00:01:05" in options
    assert "--title=My Show" in options
    assert "--force-window=yes" in options
    assert "--quiet" in options


def test_play_on_desktop_raises_when_mpv_missing():
    with patch("viu_media.libs.player.mpv.player.shutil.which", return_value=None):
        player = MpvPlayer(_make_config())

    params = _make_params("https://example.com/video.mp4")
    with pytest.raises(ViuError, match="MPV executable not found"):
        player._play_on_desktop(params)


def test_play_on_mobile_uses_youtube_intent_for_youtube_urls():
    with patch("viu_media.libs.player.mpv.player.shutil.which", return_value="mpv"):
        player = MpvPlayer(_make_config())

    params = _make_params("https://youtu.be/abc123")
    with patch("viu_media.libs.player.mpv.player.subprocess.run") as mock_run:
        result = player._play_on_mobile(params)

    args = mock_run.call_args.args[0]
    assert "com.google.android.youtube/.UrlActivity" in args
    assert result.episode == "1"


def test_play_on_mobile_uses_mpv_activity_for_non_youtube_urls():
    with patch("viu_media.libs.player.mpv.player.shutil.which", return_value="mpv"):
        player = MpvPlayer(_make_config())

    params = _make_params("https://example.com/video.mp4")
    with patch("viu_media.libs.player.mpv.player.subprocess.run") as mock_run:
        player._play_on_mobile(params)

    args = mock_run.call_args.args[0]
    assert "is.xyz.mpv/.MPVActivity" in args


def test_stream_on_desktop_with_subprocess_parses_av_time():
    with patch("viu_media.libs.player.mpv.player.shutil.which", return_value="mpv"):
        player = MpvPlayer(_make_config(pre_args="nohup"))

    params = _make_params("https://example.com/video.m3u8")
    process_output = "line1\nAV: 00:10:03 / 00:24:00 (41%)\n"
    fake_proc = SimpleNamespace(stdout=process_output)

    with patch(
        "viu_media.libs.player.mpv.player.subprocess.run",
        return_value=fake_proc,
    ) as mock_run:
        result = player._stream_on_desktop_with_subprocess(params)

    assert result.stop_time == "00:10:03"
    assert result.total_time == "00:24:00"
    assert mock_run.call_args.kwargs["capture_output"] is True


def test_play_rejects_torrent_on_termux():
    with patch("viu_media.libs.player.mpv.player.shutil.which", return_value="mpv"):
        player = MpvPlayer(_make_config())

    params = _make_params("magnet:?xt=urn:btih:1234567890123456789012345678901234567890")
    with patch(
        "viu_media.libs.player.mpv.player.detect.is_running_in_termux",
        return_value=True,
    ):
        with pytest.raises(ViuError, match="Unable to play torrents on termux"):
            player.play(params)


def test_play_rejects_syncplay_on_termux():
    with patch("viu_media.libs.player.mpv.player.shutil.which", return_value="mpv"):
        player = MpvPlayer(_make_config())

    params = _make_params("https://example.com/video.mp4", syncplay=True)
    with patch(
        "viu_media.libs.player.mpv.player.detect.is_running_in_termux",
        return_value=True,
    ):
        with pytest.raises(ViuError, match="Unable to play with syncplay on termux"):
            player.play(params)
