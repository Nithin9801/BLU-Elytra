"""Small caption chunks timed proportionally within each spoken audio file.

Without a forced aligner the individual words are approximate; scene boundaries are
always based on the WAV's measured duration, not on guessed word counts.
"""
from __future__ import annotations


def make_captions(text: str, audio_duration: float, max_chars: int = 105) -> list[dict]:
    words = text.split()
    groups: list[str] = []
    line = ''
    for word in words:
        candidate = f'{line} {word}'.strip()
        if line and len(candidate) > max_chars:
            groups.append(line)
            line = word
        else:
            line = candidate
    if line:
        groups.append(line)
    if not groups:
        return []
    weights = [max(len(group), 1) for group in groups]
    weight_total = sum(weights)
    used = 0
    result = []
    for i, (group, weight) in enumerate(zip(groups, weights)):
        start = audio_duration * used / weight_total
        used += weight
        end = audio_duration if i == len(groups) - 1 else audio_duration * used / weight_total
        result.append({'text': group, 'start': round(start, 3), 'end': round(end, 3)})
    return result


def srt_timestamp(seconds: float) -> str:
    millis = max(0, round(seconds * 1000))
    hours, millis = divmod(millis, 3600000)
    minutes, millis = divmod(millis, 60000)
    seconds, millis = divmod(millis, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{millis:03}'


def make_srt(scenes: list, fps: int = 12) -> str:
    import math
    offset = 0.0
    blocks = []
    for scene in scenes:
        for cap in scene.captions:
            blocks.append(f'{len(blocks)+1}\n{srt_timestamp(offset + cap.start)} --> {srt_timestamp(offset + cap.end)}\n{cap.text}\n')
        # Match the rounded scene frame counts used by the MP4 renderer.
        offset += math.ceil((scene.audio_duration + scene.pause_seconds) * fps) / fps
    return '\n'.join(blocks)
