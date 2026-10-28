"""Offline 720p renderer. The LLM supplies text only; all visuals are ours."""
from __future__ import annotations

import math
import os
import shutil
import subprocess
import wave
from functools import lru_cache
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageFont, features

HAS_RAQM = features.check_feature('raqm')

from .captions import make_srt
from .schemas import LessonOutput

HERE = Path(__file__).resolve().parents[1]
FONTS = HERE / 'assets' / 'fonts'
WIDTH, HEIGHT, FPS = 1280, 720, 20
INK = '#202442'
MUTED = '#777e9d'
BLUE = '#5365e9'
LAVENDER = '#e7eafd'


@lru_cache(maxsize=60)
def font(size: int, language: str = 'en', bold: bool = False, mono: bool = False):
    if mono:
        name = 'DejaVuSansMono.ttf'
    else:
        name = {'hi': 'NotoSansDevanagari.ttf', 'ta': 'NotoSansTamil.ttf'}.get(language, 'DMSans.ttf')
    layout = ImageFont.Layout.RAQM if HAS_RAQM else ImageFont.Layout.BASIC
    result = ImageFont.truetype(str(FONTS / name), size=size, layout_engine=layout)
    if bold and not mono:
        try:
            result.set_variation_by_name('Bold')
        except (OSError, ValueError):
            pass
    return result


def text_width(draw, text, font_obj):
    return draw.textlength(text, font=font_obj)


def wrap(draw, text, f, max_width, max_lines=None):
    """Wrap using measured, shaped glyph widths; preserve Unicode text."""
    lines = []
    for paragraph in text.split('\n'):
        line = ''
        for word in paragraph.split():
            candidate = f'{line} {word}'.strip()
            if line and text_width(draw, candidate, f) > max_width:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines[-1] and text_width(draw, lines[-1] + '…', f) > max_width:
            lines[-1] = lines[-1][:-1]
        lines[-1] += '…'
    return lines


def draw_lines(draw, lines, xy, f, fill, spacing):
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=f, fill=fill, anchor='lt')
        y += spacing
    return y


def pill(draw, box, fill, text, f, text_color, outline=None):
    draw.rounded_rectangle(box, radius=(box[3] - box[1]) // 2, fill=fill, outline=outline, width=1)
    tx = box[0] + (box[2] - box[0] - text_width(draw, text, f)) / 2
    # anchor=mm keeps Latin and Indic scripts centered in their pills.
    draw.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), text,
              font=f, fill=text_color, anchor='mm')


def base_frame(scene, lesson, index, t, scene_length, total_elapsed, total_length):
    img = Image.new('RGB', (WIDTH, HEIGHT), '#eef0ff')
    d = ImageDraw.Draw(img)
    # A few quiet decorative marks; no model-generated drawing code is run.
    d.ellipse((830, -280, 1390, 280), fill='#e5e8fd')
    d.ellipse((1010, 130, 1390, 510), outline='#d8def9', width=2)
    for x in range(74, 400, 21):
        d.ellipse((x, 540, x + 2, 542), fill='#cbd1f1')
    pill(d, (74, 62, 245, 98), '#ffffff', 'VISUAL LESSON', font(14, bold=True), BLUE)
    d.text((1202, 80), f'{index + 1:02} / {len(lesson.scenes):02}', font=font(16, bold=True), fill='#8288a7', anchor='rm')

    # Headings are wrapped in the relevant local font and script.
    title_size = 45 if lesson.language == 'en' else 40
    title_font = font(title_size, lesson.language, True)
    title_lines = wrap(d, scene.heading, title_font, 478)
    while len(title_lines) > 4 and title_size > 25:
        title_size -= 3
        title_font = font(title_size, lesson.language, True)
        title_lines = wrap(d, scene.heading, title_font, 478)
    draw_lines(d, title_lines[:4], (76, 146), title_font, INK, min(63, round(title_size * 1.42)))
    d.rounded_rectangle((76, 424, 118, 429), radius=2, fill='#7785f3')
    kind = {'title_card': 'THE BIG IDEA', 'diagram': 'LET’S VISUALISE', 'code_walkthrough': 'TAKE A CLOSER LOOK'}[scene.type]
    d.text((76, 451), kind, font=font(15, bold=True), fill='#878dab', anchor='lt')

    if scene.type == 'title_card':
        draw_title_visual(d, scene, t, lesson.language)
    elif scene.type == 'diagram':
        draw_diagram(d, scene, t, scene_length, lesson.language)
    else:
        draw_code(d, scene, t, scene_length)

    caption = scene.narration
    if scene.captions:
        caption = next((c.text for c in scene.captions if c.start <= min(t, scene.audio_duration - 0.001) < c.end), scene.captions[-1].text)
    d.rounded_rectangle((74, 584, 1206, 678), radius=18, fill='#232747')
    d.ellipse((98, 616, 129, 647), fill='#5d70f1')
    # Draw the caption icon as a vector, so it does not depend on font glyphs.
    d.rounded_rectangle((105, 626, 122, 639), radius=3, outline='white', width=2)
    d.line((108, 631, 112, 631), fill='white', width=2)
    d.line((115, 631, 119, 631), fill='white', width=2)
    d.line((108, 635, 119, 635), fill='white', width=2)
    caption_font = font(25 if lesson.language != 'en' else 26, lesson.language)
    caption_lines = wrap(d, caption, caption_font, 1010, 2)
    draw_lines(d, caption_lines, (151, 605 if len(caption_lines) > 1 else 617), caption_font, '#ffffff', 34)
    d.rectangle((0, 712, WIDTH, 720), fill='#d2d8f5')
    progress = max(0, min(1, total_elapsed / max(total_length, 0.001)))
    d.rectangle((0, 712, round(WIDTH * progress), 720), fill='#6274f2')
    return img


def draw_title_visual(d, scene, t, language):
    # Concentric lines suggest an idea in motion.
    d.ellipse((663, 110, 1193, 640), outline='#d2d8fa', width=3)
    d.ellipse((711, 158, 1145, 592), outline='#d7dcfb', width=2)
    # A slowly travelling dot gives the title card motion without generated code.
    angle = t * 0.32 - 2.13
    dot_x = 928 + 265 * math.cos(angle)
    dot_y = 375 + 265 * math.sin(angle)
    d.ellipse((dot_x - 8, dot_y - 8, dot_x + 8, dot_y + 8), fill='#aeb9ff')
    d.ellipse((1164, 436, 1175, 447), fill='#aeb9ff')
    d.rounded_rectangle((692, 215, 1156, 477), radius=24, fill='#d9ddf8')
    d.rounded_rectangle((682, 205, 1146, 467), radius=24, fill='white')
    d.ellipse((709, 230, 720, 241), fill='#ffb4a2')
    d.ellipse((729, 230, 740, 241), fill='#f7d382')
    d.ellipse((749, 230, 760, 241), fill='#a2dcbe')
    if scene.code:
        code_font = font(20, mono=True)
        lines = scene.code.splitlines()[:3]
        for i, line in enumerate(lines):
            d.text((719, 275 + i * 36), line[:31], font=code_font, fill='#404568', anchor='lt')
    else:
        d.text((720, 276), 'A LITTLE CLARITY', font=font(15, bold=True), fill='#9ba1bc', anchor='lt')
        d.text((720, 310), 'One idea at a time.', font=font(27, bold=True), fill=INK, anchor='lt')
    choices = (scene.items or ['01', '02', '03'])[:3]
    for i, item in enumerate(choices):
        x = 719 + i * 72
        d.rounded_rectangle((x, 385, x + 56, 431), radius=12, fill=['#dfe4ff', '#e8e2fd', '#ffeadc'][i])
        f = font(20, language, True)
        label = item if len(item) <= 5 else item[:4] + '…'
        d.text((x + 28, 408), label, font=f, fill=BLUE, anchor='mm')
    d.ellipse((1072, 172, 1122, 222), fill='#7384f5')
    d.polygon([(1097, 183), (1100, 192), (1109, 196), (1100, 199),
               (1097, 209), (1094, 199), (1085, 196), (1094, 192)], fill='white')


def draw_diagram(d, scene, t, scene_length, language):
    items = scene.items[:5]
    count = len(items)
    left, right = 630, 1170
    gap = 16
    card_w = (right - left - gap * (count - 1)) / max(count, 1)
    active = min(count - 1, int((t / max(scene_length - 0.6, 0.01)) * count))
    d.text((640, 227), 'FOLLOW THE STEPS', font=font(15, bold=True), fill='#9098b8', anchor='lt')
    for i, item in enumerate(items):
        x1 = round(left + i * (card_w + gap))
        x2 = round(x1 + card_w)
        y1, y2 = 278, 416
        color = '#596ceb' if i == active else '#ffffff'
        d.rounded_rectangle((x1, y1 + 8, x2, y2 + 8), radius=18, fill='#d9def7')
        d.rounded_rectangle((x1, y1, x2, y2), radius=18, fill=color)
        d.text(((x1 + x2) / 2, 307), f'{i + 1:02}', font=font(13, bold=True), fill='#d8ddff' if i == active else '#a7afcd', anchor='mm')
        f = font(22 if count < 4 else 16, language, True)
        lines = wrap(d, item, f, card_w - 18, 2)
        for line_num, line in enumerate(lines):
            d.text(((x1 + x2) / 2, 350 + 27 * line_num), line, font=f, fill='white' if i == active else INK, anchor='mm')
        if i < count - 1:
            d.line((x2 + 2, 347, x2 + gap - 4, 347), fill='#a2adf0', width=2)
            d.polygon([(x2 + gap - 7, 343), (x2 + gap - 2, 347), (x2 + gap - 7, 351)], fill='#a2adf0')
    d.text((640, 457), 'STEP BY STEP', font=font(14, bold=True), fill='#a0a6c2', anchor='lt')


def draw_code(d, scene, t, scene_length):
    d.rounded_rectangle((640, 190, 1168, 466), radius=22, fill='#d8def8')
    d.rounded_rectangle((632, 181, 1160, 457), radius=22, fill='#242944')
    for i, color in enumerate(('#fa998d', '#f3ce79', '#8bd3b0')):
        d.ellipse((660 + 20*i, 207, 671 + 20*i, 218), fill=color)
    d.text((1128, 213), 'CODE', font=font(12, bold=True), fill='#8f99c3', anchor='rm')
    lines = scene.code.splitlines()[:5]
    highlights = scene.highlight_lines
    active = highlights[min(len(highlights) - 1, int(t / max(scene.audio_duration, 0.01) * len(highlights)))] if highlights else None
    for i, line in enumerate(lines):
        y = 256 + i * 34
        is_highlight = i + 1 == active
        if is_highlight:
            d.rounded_rectangle((652, y - 9, 1138, y + 23), radius=6, fill='#36416d')
        d.text((663, y), str(i + 1), font=font(15, mono=True), fill='#7e88aa', anchor='lt')
        d.text((697, y), line[:38], font=font(19, mono=True), fill='#eef1ff', anchor='lt')


def concatenate_audio(paths: list[Path], frame_counts: list[int], destination: Path):
    with wave.open(str(paths[0]), 'rb') as first:
        params = first.getparams()
    if params.nchannels != 1 or params.sampwidth != 2 or params.comptype != 'NONE':
        raise RuntimeError('Only mono 16-bit PCM narration is supported by this exporter.')
    with wave.open(str(destination), 'wb') as output:
        output.setnchannels(params.nchannels)
        output.setsampwidth(params.sampwidth)
        output.setframerate(params.framerate)
        for path, frame_count in zip(paths, frame_counts):
            with wave.open(str(path), 'rb') as current:
                if (current.getnchannels(), current.getsampwidth(), current.getframerate()) != (params.nchannels, params.sampwidth, params.framerate):
                    raise RuntimeError('Narration files do not share the same audio format.')
                num_samples = current.getnframes()
                output.writeframes(current.readframes(num_samples))
            # Round up video frames and fill the exact remainder with silence.
            target_samples = round(frame_count / FPS * params.framerate)
            output.writeframes(b'\x00' * max(0, (target_samples - num_samples) * params.sampwidth))


def export_lesson(lesson: LessonOutput, audio_paths: list[Path], output_dir: Path,
                  on_progress: Callable[[float], None] | None = None) -> tuple[Path, Path]:
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise RuntimeError('FFmpeg is not installed. Install it to export MP4.')
    if lesson.language in ('hi', 'ta') and not HAS_RAQM:
        raise RuntimeError('Indic export needs a Pillow build with libraqm enabled for correct script shaping.')
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / 'lesson.mp4'
    subtitle = output_dir / 'captions.srt'
    temp_video = output_dir / 'lesson.tmp.mp4'
    combined = output_dir / 'narration.tmp.wav'
    ffmpeg_log = output_dir / 'ffmpeg.tmp.log'
    frames = [math.ceil((s.audio_duration + s.pause_seconds) * FPS) for s in lesson.scenes]
    total_frames = sum(frames)
    total_duration = total_frames / FPS
    concatenate_audio(audio_paths, frames, combined)
    subtitle.write_text(make_srt(lesson.scenes, FPS), encoding='utf-8')
    command = [ffmpeg, '-hide_banner', '-loglevel', 'error', '-y',
               '-f', 'rawvideo', '-pixel_format', 'rgb24', '-video_size', f'{WIDTH}x{HEIGHT}',
               '-framerate', str(FPS), '-i', 'pipe:0', '-i', str(combined),
               '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '24', '-threads', '2',
               '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart',
               '-shortest', str(temp_video)]
    process = None
    try:
        with ffmpeg_log.open('wb') as log:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log)
            written = 0
            for index, scene in enumerate(lesson.scenes):
                for frame in range(frames[index]):
                    t = frame / FPS
                    img = base_frame(scene, lesson, index, t, frames[index] / FPS, written / FPS, total_duration)
                    process.stdin.write(img.tobytes())
                    written += 1
                    if on_progress and (written % 10 == 0 or written == total_frames):
                        on_progress(round(written / total_frames, 3))
            process.stdin.close()
            result = process.wait(timeout=180)
        if result != 0:
            raise RuntimeError('FFmpeg could not encode the lesson: ' + ffmpeg_log.read_text(errors='replace')[-600:])
        os.replace(temp_video, output)
        return output, subtitle
    except Exception:
        if process and process.poll() is None:
            process.kill()
            process.wait()
        raise
    finally:
        for path in (combined, temp_video, ffmpeg_log):
            path.unlink(missing_ok=True)
