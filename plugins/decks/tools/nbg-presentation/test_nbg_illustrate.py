"""nbg_illustrate: the house-style illustration tool. The Gemini API is never called:
each test replaces urllib's urlopen with a fake that records the request and answers
with a picture drawn here."""

from __future__ import annotations

import base64
import io
import json
import time

import nbg_illustrate
import pytest
from PIL import Image, ImageDraw


def _scene(size=(1200, 900)) -> bytes:
    """A subject on a white ground: a teal block holding a white 'screen', so the
    test can tell background white (made transparent) from subject white (kept)."""
    img = Image.new("RGB", size, "white")
    d = ImageDraw.Draw(img)
    d.rectangle((300, 200, 900, 700), fill="#007B85")
    d.rectangle((400, 300, 800, 600), fill="white")
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


class _Answer:
    def __init__(self, payload: dict) -> None:
        self._data = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None


@pytest.fixture
def api(monkeypatch):
    """Answers every call with `answer` and records each request."""
    calls: list = []
    state = {
        "answer": {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "inlineData": {
                                    "mimeType": "image/png",
                                    "data": base64.b64encode(_scene()).decode(),
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

    def urlopen(req, timeout=None):
        calls.append(req)
        return _Answer(state["answer"])

    monkeypatch.setattr(nbg_illustrate.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    return calls, state


def test_probe_says_whether_a_key_is_set(monkeypatch, capsys):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("DECKS_NO_KEYCHAIN", "1")
    assert nbg_illustrate.main(["--probe"]) == 3
    assert "library" in capsys.readouterr().out
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    assert nbg_illustrate.main(["--probe"]) == 0


def test_without_a_key_nothing_is_sent_and_the_exit_says_use_the_library(monkeypatch, tmp_path):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("DECKS_NO_KEYCHAIN", "1")
    sent = []
    monkeypatch.setattr(nbg_illustrate.urllib.request, "urlopen", lambda *a, **k: sent.append(a))
    code = nbg_illustrate.main(
        ["--brief", "a colleague at a desk", "--out", str(tmp_path / "a.png")]
    )
    assert code == 3 and not sent and not (tmp_path / "a.png").exists()


@pytest.mark.parametrize(
    "brief",
    [
        "a chart rising to 50",
        "a wallet with € coins",
        "a 30% growth arrow",
        "the NBG tower",
        "a branch of National Bank of Greece",
        "η Εθνική Τράπεζα",
        "ΕΘΝΙΚΗ ΤΡΑΠΕΖΑ",
    ],
)
def test_a_brief_with_numbers_money_or_the_bank_name_is_refused_before_sending(
    api, tmp_path, brief
):
    calls, _ = api
    assert nbg_illustrate.main(["--brief", brief, "--out", str(tmp_path / "a.png")]) == 2
    assert calls == []


def test_the_picture_is_trimmed_rgba_and_only_the_outer_white_is_transparent(api, tmp_path):
    out = tmp_path / "scene.png"
    assert nbg_illustrate.main(["--brief", "a screen on a teal stand", "--out", str(out)]) == 0
    with Image.open(out) as im:
        assert im.mode == "RGBA", "a palette PNG renders as a white box in LibreOffice"
        w, h = im.size
        assert (w, h) == (637, 537), "trimmed to the 601 x 501 px subject plus a 3 per cent margin"
        assert im.getpixel((2, 2))[3] == 0, "the white ground joined to the border is transparent"
        assert im.getpixel((w // 2, h // 2)) == (255, 255, 255, 255), (
            "the screen inside stays white"
        )
        assert (
            im.getpixel((30, h // 2))[:3] == (0, 123, 133) and im.getpixel((30, h // 2))[3] == 255
        )


def test_a_large_picture_is_scaled_to_the_token_maximum(api, tmp_path):
    _, state = api
    big = Image.new("RGB", (3000, 1000), "#003841")
    buf = io.BytesIO()
    big.save(buf, format="PNG")
    state["answer"]["candidates"][0]["content"]["parts"][0]["inlineData"]["data"] = (
        base64.b64encode(buf.getvalue()).decode()
    )
    out = tmp_path / "wide.png"
    assert nbg_illustrate.main(["--brief", "a wide horizon", "--out", str(out)]) == 0
    with Image.open(out) as im:
        assert max(im.size) == nbg_illustrate.nbg_tokens.get("illustration.max_px")


def test_the_request_carries_the_house_style_the_reference_and_no_key_in_the_url(api, tmp_path):
    calls, _ = api
    anchor = tmp_path / "anchor.png"
    anchor.write_bytes(_scene((200, 150)))
    out = tmp_path / "b.png"
    code = nbg_illustrate.main(
        [
            "--brief",
            "two colleagues talking",
            "--out",
            str(out),
            "--ref",
            str(anchor),
            "--size-in",
            "6",
            "3.4",
        ]
    )
    assert code == 0 and len(calls) == 1
    req = calls[0]
    assert "key=" not in req.full_url and req.get_header("X-goog-api-key") == "test-key"
    body = json.loads(req.data)
    parts = body["contents"][0]["parts"]
    sent = Image.open(io.BytesIO(base64.b64decode(parts[0]["inlineData"]["data"])))
    assert sent.format == "PNG" and sent.size == (200, 150), "the anchor's pixels, re-encoded"
    text = parts[-1]["text"]
    assert "#007B85" in text and "#003841" in text, "palette from tokens.yaml"
    assert "No text, no letters, no numbers" in text
    assert "reference" in text and text.endswith("Scene: two colleagues talking")
    assert body["generationConfig"]["imageConfig"]["aspectRatio"] == "16:9"


def test_a_reference_outside_the_output_folder_or_not_a_picture_is_never_sent(api, tmp_path):
    """A reference is uploaded to Google, so an agent passing ~/.ssh/id_rsa or a document
    as --ref must be refused before the file is read (SonarCloud S8707)."""
    calls, _ = api
    images = tmp_path / "images"
    images.mkdir()
    outside = tmp_path / "secret.png"
    outside.write_bytes(_scene((50, 50)))
    not_a_picture = images / "notes.png"
    not_a_picture.write_text("private notes", encoding="utf-8")
    out = images / "S02.png"
    for ref, code in ((outside, 2), (images / ".." / "secret.png", 2), (not_a_picture, 2)):
        args = ["--brief", "a desk", "--out", str(out), "--ref", str(ref)]
        assert nbg_illustrate.main(args) == code, ref
    assert calls == [] and not out.exists()


def test_several_candidates_are_written_beside_the_output_for_the_caller_to_choose(api, tmp_path):
    calls, _ = api
    out = tmp_path / "S05_vision.png"
    code = nbg_illustrate.main(
        ["--brief", "a team at a table", "--out", str(out), "--candidates", "2"]
    )
    assert code == 0 and len(calls) == 2
    assert (tmp_path / "S05_vision-c1.png").exists() and (tmp_path / "S05_vision-c2.png").exists()
    assert not out.exists(), "the caller picks one and copies it to the output"


def test_no_image_in_the_answer_exits_1_with_the_models_reason(api, tmp_path, capsys):
    _, state = api
    state["answer"] = {"candidates": [{"finishReason": "IMAGE_SAFETY", "content": {"parts": []}}]}
    assert nbg_illustrate.main(["--brief", "a crowd", "--out", str(tmp_path / "c.png")]) == 1
    assert "IMAGE_SAFETY" in capsys.readouterr().err


def test_an_api_error_exits_2_with_its_message_and_never_the_key(monkeypatch, tmp_path, capsys):
    import urllib.error
    from email.message import Message

    def refuse(req, timeout=None):
        body = io.BytesIO(json.dumps({"error": {"message": "API key not valid"}}).encode())
        raise urllib.error.HTTPError(req.full_url, 400, "Bad Request", Message(), body)

    monkeypatch.setattr(nbg_illustrate.urllib.request, "urlopen", refuse)
    monkeypatch.setenv("GEMINI_API_KEY", "secret-123")
    assert nbg_illustrate.main(["--brief", "a desk", "--out", str(tmp_path / "d.png")]) == 2
    err = capsys.readouterr().err
    assert "400" in err and "API key not valid" in err and "secret-123" not in err


@pytest.mark.parametrize(
    ("w", "h", "aspect"), [(6, 3.4, "16:9"), (2, 2, "1:1"), (2.1, 2.0, "1:1"), (4, 3, "4:3")]
)
def test_the_slot_picks_the_nearest_supported_aspect(w, h, aspect):
    assert nbg_illustrate.nearest_aspect(w, h) == aspect


def test_on_a_mac_the_key_comes_from_the_keychain_when_the_environment_lacks_it(monkeypatch):
    """A profile that exports the key from the Keychain reaches login shells only; a
    session started otherwise has no GEMINI_API_KEY, though the Keychain holds it."""
    import subprocess

    asked = []

    def security(cmd, **kwargs):
        asked.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="from-keychain\n", stderr="")

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("DECKS_NO_KEYCHAIN", raising=False)
    monkeypatch.setattr(nbg_illustrate.sys, "platform", "darwin")
    monkeypatch.setattr(nbg_illustrate.subprocess, "run", security)
    assert nbg_illustrate.api_key() == "from-keychain"
    assert asked == [["security", "find-generic-password", "-s", "GEMINI_API_KEY", "-w"]]

    monkeypatch.setenv("GEMINI_API_KEY", "from-env")
    assert nbg_illustrate.api_key() == "from-env" and len(asked) == 1, "the environment wins"


def test_a_keynote_photograph_is_a_16_9_jpeg_at_the_artboard_size(api, tmp_path):
    calls, _ = api
    out = tmp_path / "cover.jpg"
    code = nbg_illustrate.main(
        ["--brief", "an atrium at dusk", "--out", str(out), "--photo", "left"]
    )
    assert code == 0
    with Image.open(out) as im:
        assert im.format == "JPEG" and im.size == nbg_illustrate.PHOTO_PX
    body = json.loads(calls[0].data)
    text = body["contents"][0]["parts"][-1]["text"]
    assert "Cinematic editorial photograph" in text and "negative space on the left side" in text
    assert "No text, no letters, no numbers" in text
    assert body["generationConfig"]["imageConfig"]["aspectRatio"] == "16:9"


def test_a_photograph_is_refused_like_an_illustration_and_must_be_a_jpeg(api, tmp_path):
    calls, _ = api
    assert (
        nbg_illustrate.main(
            ["--brief", "the NBG tower", "--out", str(tmp_path / "a.jpg"), "--photo", "left"]
        )
        == 2
    )
    with pytest.raises(SystemExit):
        nbg_illustrate.main(
            ["--brief", "a street", "--out", str(tmp_path / "a.png"), "--photo", "left"]
        )
    assert calls == []
