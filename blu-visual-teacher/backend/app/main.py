from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import shutil
import time
import uuid
from pathlib import Path
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from . import audio, planner
from .captions import make_captions
from .exporter import export_lesson
from .samples import LINKED_SAMPLES, SAMPLES
from .schemas import Language, LessonOutput, LessonRequest, RevoiceRequest, SceneOutput, ScenePlan

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('blu')
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
LESSON_DIR = DATA / 'lessons'
EXPORT_DIR = DATA / 'exports'
CACHE_DIR = DATA / 'cache'
for folder in (LESSON_DIR, EXPORT_DIR, CACHE_DIR):
    folder.mkdir(parents=True, exist_ok=True)

app = FastAPI(title='Blu Visual Teacher', version='1.0.0', description='Offline-first narrated visual lessons.')
JOBS: dict[str, dict] = {}
LESSONS: dict[str, LessonOutput] = {}
EXPORT_JOBS: dict[str, str] = {}
GENERATION_LOCK = asyncio.Semaphore(1)
EXPORT_LOCK = asyncio.Semaphore(1)


def scene_output(scene, language: str, lesson_id: str, index: int, seconds: float) -> SceneOutput:
    return SceneOutput.model_validate({
        **(scene.model_dump() if hasattr(scene, 'model_dump') else scene),
        'audio_url': f'/api/audio/{lesson_id}/{index}?v=kokoro-1',
        'audio_duration': round(seconds, 3),
        'pause_seconds': audio.PAUSE_SECONDS,
        'captions': make_captions(scene.narration if hasattr(scene, 'narration') else scene['narration'], seconds),
    })


def sample_lesson(language: Language, notice: str | None = None, kind: Literal['loops', 'linked'] = 'loops') -> LessonOutput:
    sample = LINKED_SAMPLES[language] if kind == 'linked' else SAMPLES[language]
    lesson_id = f'sample-linked-{language}' if kind == 'linked' else f'sample-{language}'
    sample_dir = ROOT / 'assets' / 'sample_audio'
    if kind == 'linked':
        sample_dir /= 'linked'
    scenes = []
    for index, scene in enumerate(sample['scenes']):
        path = sample_dir / language / f'scene-{index}.wav'
        scenes.append(scene_output(scene, language, lesson_id, index, audio.duration(path)))
    result = LessonOutput(id=lesson_id, title=sample['title'], level='beginner', language=language,
                          source='sample', scenes=scenes, notice=notice)
    LESSONS[lesson_id] = result.model_copy(update={'notice': None})
    return result


def valid_lesson_id(lesson_id: str) -> bool:
    return bool(re.fullmatch(r'(?:sample-(?:linked-)?(?:en|hi|ta)|[a-f0-9]{16})', lesson_id))


def get_lesson(lesson_id: str) -> LessonOutput:
    if not valid_lesson_id(lesson_id):
        raise HTTPException(404, 'Lesson not found')
    if lesson_id.startswith('sample-'):
        return sample_lesson(lesson_id[-2:], kind='linked' if lesson_id.startswith('sample-linked-') else 'loops')
    if lesson_id in LESSONS:
        return LESSONS[lesson_id]
    manifest = LESSON_DIR / lesson_id / 'lesson.json'
    if manifest.is_file():
        try:
            lesson = LessonOutput.model_validate_json(manifest.read_text(encoding='utf-8'))
            LESSONS[lesson_id] = lesson
            return lesson
        except Exception:
            log.exception('Could not load lesson manifest')
    raise HTTPException(404, 'Lesson not found')


def audio_path(lesson: LessonOutput, index: int) -> Path:
    if not 0 <= index < len(lesson.scenes):
        raise HTTPException(404, 'Audio not found')
    if lesson.source == 'sample':
        directory = ROOT / 'assets' / 'sample_audio'
        if lesson.id.startswith('sample-linked-'):
            directory /= 'linked'
        return directory / lesson.language / f'scene-{index}.wav'
    return LESSON_DIR / lesson.id / f'scene-{index}.wav'


def cache_key(request: LessonRequest) -> str:
    value = {'request': request.model_dump(), 'model': planner.OLLAMA_MODEL, 'voice': audio.voice_profile(request.language), 'version': 2}
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def revoice_cache_key(original_id: str, language: Language) -> str:
    value = {'original': original_id, 'language': language, 'model': planner.OLLAMA_MODEL,
             'voice': audio.voice_profile(language), 'version': 2}
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


@app.get('/api/health')
async def health():
    state = 'offline'
    model_found = False
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            response = await client.get(f'{planner.OLLAMA_URL}/api/tags')
            response.raise_for_status()
            models = response.json().get('models', [])
            model_found = any(m.get('name', m.get('model')) == planner.OLLAMA_MODEL for m in models)
            state = 'ready' if model_found else 'model_missing'
    except (httpx.HTTPError, ValueError, TypeError):
        pass
    voice_status = {}
    for language in ('en', 'hi', 'ta'):
        available = audio.tts_available(language)
        engine = ('kokoro' if audio.kokoro_available(language) else 'espeak-ng') if available else 'unavailable'
        voice_status[language] = {'available': available, 'engine': engine,
                                  'voice': audio.voice_profile(language) if available else None}
    return {'ollama': state, 'model': planner.OLLAMA_MODEL, 'tts': audio.tts_available(),
            'tts_languages': voice_status, 'ffmpeg': bool(shutil.which('ffmpeg')),
            'languages': ['en', 'hi', 'ta']}


@app.get('/api/sample', response_model=LessonOutput)
def get_sample(language: Language = Query(default='en'), kind: Literal['loops', 'linked'] = Query(default='loops')):
    return sample_lesson(language, kind=kind)


@app.post('/api/lessons', status_code=202)
async def start_lesson(request: LessonRequest):
    job_id = uuid.uuid4().hex
    JOBS[job_id] = {'id': job_id, 'kind': 'lesson', 'status': 'queued', 'stage': 'Waiting to plan'}
    asyncio.create_task(run_lesson_job(job_id, request))
    return {'job_id': job_id}


async def run_lesson_job(job_id: str, request: LessonRequest):
    job = JOBS[job_id]
    started = time.monotonic()
    async with GENERATION_LOCK:
        try:
            cache_file = CACHE_DIR / f'{cache_key(request)}.txt'
            if cache_file.is_file():
                try:
                    existing = get_lesson(cache_file.read_text(encoding='utf-8').strip())
                    if all(audio_path(existing, i).is_file() for i in range(len(existing.scenes))):
                        job.update(status='complete', stage='Ready from cache', lesson=existing.model_dump(), cached=True)
                        return
                except (HTTPException, OSError):
                    pass
            job.update(status='working', stage='Planning your lesson')
            plan_started = time.monotonic()
            plan = await planner.plan_lesson(request)
            planning_seconds = time.monotonic() - plan_started
            if not audio.tts_available(request.language):
                raise RuntimeError('No local voice is available for this language. Install Kokoro for English/Hindi or eSpeak NG for Tamil.')
            job.update(stage='Creating narration')
            voice_started = time.monotonic()
            lesson_id = uuid.uuid4().hex[:16]
            out = LESSON_DIR / lesson_id
            out.mkdir(parents=True, exist_ok=True)
            scenes = []
            try:
                for index, scene in enumerate(plan.scenes):
                    job['stage'] = f'Creating narration · scene {index + 1} of {len(plan.scenes)}'
                    seconds = await asyncio.to_thread(audio.synthesize, scene.narration, request.language, out / f'scene-{index}.wav')
                    scenes.append(scene_output(scene, request.language, lesson_id, index, seconds))
            except Exception:
                shutil.rmtree(out, ignore_errors=True)
                raise
            voice_seconds = time.monotonic() - voice_started
            lesson = LessonOutput(id=lesson_id, title=plan.title, level=request.level,
                                  language=request.language, source='ollama', scenes=scenes,
                                  timings={'planning': round(planning_seconds, 2), 'narration': round(voice_seconds, 2),
                                           'total': round(time.monotonic() - started, 2)})
            (out / 'lesson.json').write_text(lesson.model_dump_json(indent=2), encoding='utf-8')
            cache_file.write_text(lesson_id, encoding='utf-8')
            LESSONS[lesson_id] = lesson
            job.update(status='complete', stage='Your lesson is ready', lesson=lesson.model_dump(), cached=False)
        except Exception as exc:
            if not isinstance(exc, (planner.PlanningError, RuntimeError)):
                log.exception('Lesson generation failed')
                reason = 'Something went wrong while creating the lesson.'
            else:
                log.info('Using fallback sample: %s', exc)
                reason = str(exc)
            is_linked = bool(re.search(r'\blinked[\s-]+lists?\b', request.topic, re.IGNORECASE))
            if is_linked:
                fallback = sample_lesson(request.language, kind='linked', notice=f'{reason} Showing a built-in beginner singly linked-list introduction instead of a custom lesson.')
            else:
                fallback = sample_lesson(request.language, notice=f'{reason} Showing the built-in Python loop sample instead.')
            job.update(status='complete', stage='Sample lesson ready', lesson=fallback.model_dump(), cached=False)


@app.post('/api/lessons/{lesson_id}/revoice', status_code=202)
async def start_revoice(lesson_id: str, request: RevoiceRequest):
    lesson = get_lesson(lesson_id)
    job_id = uuid.uuid4().hex
    JOBS[job_id] = {'id': job_id, 'kind': 'revoice', 'status': 'queued', 'stage': 'Preparing translation'}
    asyncio.create_task(run_revoice_job(job_id, lesson, request.language))
    return {'job_id': job_id}


async def run_revoice_job(job_id: str, lesson: LessonOutput, language: Language):
    job = JOBS[job_id]
    started = time.monotonic()
    async with GENERATION_LOCK:
        try:
            if lesson.source == 'sample':
                kind = 'linked' if lesson.id.startswith('sample-linked-') else 'loops'
                translated = sample_lesson(language, kind=kind)
                job.update(status='complete', stage='Sample ready', lesson=translated.model_dump(), cached=True)
                return
            original = get_lesson(lesson.original_id or lesson.id)
            if language == original.language:
                job.update(status='complete', stage='Original lesson ready', lesson=original.model_dump(), cached=True)
                return
            cache_file = CACHE_DIR / f'{revoice_cache_key(original.id, language)}.txt'
            if cache_file.is_file():
                try:
                    cached = get_lesson(cache_file.read_text(encoding='utf-8').strip())
                    if all(audio_path(cached, i).is_file() for i in range(len(cached.scenes))):
                        job.update(status='complete', stage='Translation ready from cache', lesson=cached.model_dump(), cached=True)
                        return
                except (HTTPException, OSError):
                    pass
            if not audio.tts_available(language):
                raise RuntimeError('No local voice is available for this language. Install Kokoro for English/Hindi or eSpeak NG for Tamil.')
            job.update(status='working', stage='Translating your lesson')
            translation_started = time.monotonic()
            result = await planner.translate_lesson(original, language)
            translation_seconds = time.monotonic() - translation_started
            voice_started = time.monotonic()
            lesson_id = uuid.uuid4().hex[:16]
            out = LESSON_DIR / lesson_id
            out.mkdir(parents=True, exist_ok=True)
            scenes = []
            try:
                for index, (old, new) in enumerate(zip(original.scenes, result.scenes)):
                    job['stage'] = f'Creating narration · scene {index + 1} of {len(original.scenes)}'
                    # Only translated text is accepted; structure, code and highlights are preserved.
                    scene = ScenePlan.model_validate({**old.model_dump(), **new.model_dump()})
                    seconds = await asyncio.to_thread(audio.synthesize, scene.narration, language, out / f'scene-{index}.wav')
                    scenes.append(scene_output(scene, language, lesson_id, index, seconds))
            except Exception:
                shutil.rmtree(out, ignore_errors=True)
                raise
            translated = LessonOutput(id=lesson_id, original_id=original.id, title=result.title,
                                      level=original.level, language=language, source='ollama', scenes=scenes,
                                      timings={'translation': round(translation_seconds, 2),
                                               'narration': round(time.monotonic() - voice_started, 2),
                                               'total': round(time.monotonic() - started, 2)})
            (out / 'lesson.json').write_text(translated.model_dump_json(indent=2), encoding='utf-8')
            cache_file.write_text(lesson_id, encoding='utf-8')
            LESSONS[lesson_id] = translated
            job.update(status='complete', stage='Translation ready', lesson=translated.model_dump(), cached=False)
        except Exception as exc:
            if not isinstance(exc, (planner.PlanningError, RuntimeError)):
                log.exception('Revoicing failed')
                reason = 'The lesson could not be translated.'
            else:
                reason = str(exc)
            job.update(status='error', stage='Revoicing failed', error=f'{reason} Your original lesson is still available.')


@app.get('/api/jobs/{job_id}')
def job_status(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, 'Job not found')
    return JOBS[job_id]


@app.get('/api/lessons/{lesson_id}', response_model=LessonOutput)
def lesson_detail(lesson_id: str):
    return get_lesson(lesson_id)


@app.get('/api/audio/{lesson_id}/{index}')
def get_audio(lesson_id: str, index: int):
    lesson = get_lesson(lesson_id)
    path = audio_path(lesson, index)
    if not path.is_file():
        raise HTTPException(404, 'Audio not found')
    return FileResponse(path, media_type='audio/wav', headers={'Cache-Control': 'private, max-age=3600'})


@app.post('/api/lessons/{lesson_id}/export', status_code=202)
async def start_export(lesson_id: str):
    lesson = get_lesson(lesson_id)
    if not shutil.which('ffmpeg'):
        raise HTTPException(503, 'FFmpeg is not installed. Install it and restart the backend.')
    existing_id = EXPORT_JOBS.get(lesson_id)
    if existing_id and JOBS[existing_id]['status'] in ('queued', 'working'):
        return {'job_id': existing_id}
    job_id = uuid.uuid4().hex
    JOBS[job_id] = {'id': job_id, 'kind': 'export', 'status': 'queued', 'stage': 'Preparing your video', 'progress': 0}
    EXPORT_JOBS[lesson_id] = job_id
    asyncio.create_task(run_export_job(job_id, lesson))
    return {'job_id': job_id}


async def run_export_job(job_id: str, lesson: LessonOutput):
    job = JOBS[job_id]
    async with EXPORT_LOCK:
        try:
            out = EXPORT_DIR / lesson.id
            video = out / 'lesson.mp4'
            subtitle = out / 'captions.srt'
            version_file = out / 'render-version.txt'
            if video.is_file() and subtitle.is_file() and version_file.is_file() and version_file.read_text() == '4':
                job.update(status='complete', stage='Video ready', progress=1,
                           video_url=f'/api/exports/{lesson.id}/lesson.mp4', srt_url=f'/api/exports/{lesson.id}/captions.srt')
                return
            job.update(status='working', stage='Rendering 720p video')
            paths = [audio_path(lesson, i) for i in range(len(lesson.scenes))]
            await asyncio.to_thread(export_lesson, lesson, paths, out, lambda value: job.update(progress=value))
            version_file.write_text('4', encoding='utf-8')
            job.update(status='complete', stage='Video ready', progress=1,
                       video_url=f'/api/exports/{lesson.id}/lesson.mp4', srt_url=f'/api/exports/{lesson.id}/captions.srt')
        except Exception as exc:
            log.exception('MP4 export failed')
            job.update(status='error', stage='Export failed', error=str(exc)[:300])


@app.get('/api/exports/{lesson_id}/{filename}')
def get_export(lesson_id: str, filename: str):
    get_lesson(lesson_id)
    if filename not in ('lesson.mp4', 'captions.srt'):
        raise HTTPException(404, 'File not found')
    path = EXPORT_DIR / lesson_id / filename
    if not path.is_file():
        raise HTTPException(404, 'Export not found')
    mime = 'video/mp4' if filename.endswith('.mp4') else 'application/x-subrip'
    return FileResponse(path, media_type=mime, filename=f'blu-{lesson_id}-{filename}')
