"""Offline narration: Kokoro for English/Hindi, eSpeak NG as a fallback.

Kokoro model assets are installed once by ``python setup_kokoro.py``. Audio is
written as mono 16-bit PCM at 22050 Hz so every scene can be concatenated by
our offline MP4 exporter, regardless of which local voice was used.
"""
from __future__ import annotations

import importlib.util
import logging
import os
import shutil
import subprocess
import threading
import wave
from functools import lru_cache
from pathlib import Path

log = logging.getLogger('blu.audio')
ROOT = Path(__file__).resolve().parents[1]
MODEL = Path(os.environ.get('BLU_KOKORO_MODEL', ROOT / 'models' / 'kokoro-v1.0.int8.onnx'))
VOICES_FILE = Path(os.environ.get('BLU_KOKORO_VOICES', ROOT / 'models' / 'kokoro-voices.bin'))
KOKORO_VOICES = {
    'en': (os.environ.get('BLU_KOKORO_EN_VOICE', 'af_heart'), 'en-us'),
    'hi': (os.environ.get('BLU_KOKORO_HI_VOICE', 'hf_alpha'), 'hi'),
}
ESPEAK_VOICES = {'en': 'en-gb', 'hi': 'hi', 'ta': 'ta'}
PAUSE_SECONDS = 0.6
OUTPUT_RATE = 22050
# The local phonemizer and ONNX session are shared; serialize synthesis.
_KOKORO_LOCK = threading.Lock()


def kokoro_available(language: str | None = None) -> bool:
    if language is not None and language not in KOKORO_VOICES:
        return False
    return (MODEL.is_file() and VOICES_FILE.is_file()
            and importlib.util.find_spec('kokoro_onnx') is not None)


def tts_available(language: str | None = None) -> bool:
    return kokoro_available(language) or bool(shutil.which('espeak-ng'))


def voice_profile(language: str) -> str:
    """Include the voice backend in cache keys so old robotic audio is not reused."""
    if kokoro_available(language):
        return f'kokoro-int8-{KOKORO_VOICES[language][0]}-v1'
    return f'espeak-ng-{ESPEAK_VOICES[language]}-150'


@lru_cache(maxsize=1)
def _kokoro():
    from kokoro_onnx import Kokoro
    return Kokoro(str(MODEL), str(VOICES_FILE))


def duration(path: Path) -> float:
    with wave.open(str(path), 'rb') as audio:
        return audio.getnframes() / audio.getframerate()


def _synthesize_kokoro(text: str, language: str, destination: Path) -> float:
    import numpy as np
    voice, locale = KOKORO_VOICES[language]
    with _KOKORO_LOCK:
        samples, sample_rate = _kokoro().create(text, voice=voice, speed=1.0, lang=locale)
    samples = np.asarray(samples, dtype=np.float32).reshape(-1)
    if len(samples) == 0 or not np.all(np.isfinite(samples)):
        raise RuntimeError('Kokoro produced empty or invalid audio.')
    if sample_rate != OUTPUT_RATE:
        count = max(1, round(len(samples) * OUTPUT_RATE / sample_rate))
        positions = np.arange(count, dtype=np.float64) * sample_rate / OUTPUT_RATE
        samples = np.interp(positions, np.arange(len(samples)), samples).astype(np.float32)
    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype('<i2').tobytes()
    with wave.open(str(destination), 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(OUTPUT_RATE)
        wav.writeframes(pcm)
    return round(duration(destination), 3)


def _synthesize_espeak(text: str, language: str, destination: Path) -> float:
    exe = shutil.which('espeak-ng')
    if not exe:
        raise RuntimeError('Install Kokoro or eSpeak NG to narrate this language.')
    try:
        result = subprocess.run(
            [exe, '-v', ESPEAK_VOICES[language], '-s', '150', '-w', str(destination), '--stdin'],
            input=text.encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=60, check=False,
        )
        if result.returncode != 0 or not destination.exists():
            raise RuntimeError(result.stderr.decode('utf-8', errors='replace').strip() or 'speech synthesis failed')
        seconds = duration(destination)
        if seconds <= 0:
            raise RuntimeError('The local voice produced an empty audio file.')
        return round(seconds, 3)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError('The local voice timed out.') from exc


def synthesize(text: str, language: str, destination: Path) -> float:
    """Synthesize locally, never using a shell or running model-generated code."""
    if language not in ESPEAK_VOICES:
        raise ValueError('Unsupported narration language.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    if kokoro_available(language):
        try:
            return _synthesize_kokoro(text, language, destination)
        except Exception as exc:
            destination.unlink(missing_ok=True)
            log.exception('Kokoro could not create narration')
            # Do not silently mislabel eSpeak audio as Kokoro or cache it as such.
            raise RuntimeError('Kokoro could not create narration. Check the backend log and run python setup_kokoro.py again.') from exc
    return _synthesize_espeak(text, language, destination)
