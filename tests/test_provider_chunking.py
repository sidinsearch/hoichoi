from pathlib import Path
from unittest.mock import patch

from app.backend.models.schemas import ASRSegment
from app.backend.services.asr import GroqWhisperProvider


def test_groq_provider_offsets_bounded_chunk_timestamps(tmp_path):
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"not decoded in this unit test")
    provider = object.__new__(GroqWhisperProvider)
    chunks = [(tmp_path / "chunk0.wav", 0.0), (tmp_path / "chunk1.wav", 300.0)]
    one = [ASRSegment(start=2.0, end=4.0, text="first")]
    two = [ASRSegment(start=1.0, end=3.0, text="second")]
    with patch("app.backend.services.asr._audio_chunks", return_value=chunks):
        with patch.object(provider, "_transcribe_one", side_effect=[one, two]):
            result = provider.transcribe(audio)
    assert [(s.start, s.end, s.text) for s in result] == [
        (2.0, 4.0, "first"),
        (301.0, 303.0, "second"),
    ]
