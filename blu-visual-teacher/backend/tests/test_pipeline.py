import json
import threading
import time
import uuid
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import audio, planner
from app.captions import make_captions, make_srt
from app.main import app
import app.main as main
from app.schemas import LessonPlan, ScenePlan


VALID_PLAN = {
    'title': 'How a loop works',
    'scenes': [
        {'type': 'title_card', 'heading': 'Meet a loop', 'narration': 'A loop repeats an instruction.'},
        {'type': 'diagram', 'heading': 'One at a time', 'items': ['zero', 'one', 'two'],
         'narration': 'Each pass moves to the next value.'},
        {'type': 'code_walkthrough', 'heading': 'Read the code', 'code': 'for i in range(3):\n    print(i)',
         'highlight_lines': [1, 2], 'narration': 'The indented instruction runs for each value.'},
    ],
}


class FakeOllama(BaseHTTPRequestHandler):
    response_text = json.dumps(VALID_PLAN)
    calls = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.reply({'models': [{'name': 'gemma3:4b'}]})

    def do_POST(self):
        size = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(size))
        self.__class__.calls.append((self.path, body))
        self.reply({'response': self.__class__.response_text})

    def reply(self, body):
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)


@pytest.fixture
def fake_ollama(monkeypatch, tmp_path):
    FakeOllama.response_text = json.dumps(VALID_PLAN)
    FakeOllama.calls = []
    server = ThreadingHTTPServer(('127.0.0.1', 0), FakeOllama)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr(planner, 'OLLAMA_URL', f'http://127.0.0.1:{server.server_port}')
    monkeypatch.setattr(planner, 'OLLAMA_MODEL', 'gemma3:4b')
    for name in ('LESSON_DIR', 'CACHE_DIR', 'EXPORT_DIR'):
        path = tmp_path / name
        path.mkdir()
        monkeypatch.setattr(main, name, path)
    main.JOBS.clear()
    main.LESSONS.clear()
    yield server
    server.shutdown()
    server.server_close()
    thread.join()


def finished_job(client, job_id):
    for _ in range(2000):
        job = client.get(f'/api/jobs/{job_id}').json()
        if job['status'] in ('complete', 'error'):
            return job
        time.sleep(0.03)
    raise AssertionError('Job did not finish')


def test_fallback_samples_have_real_measured_audio():
    with TestClient(app) as client:
        for language in ('en', 'hi', 'ta'):
            lesson = client.get('/api/sample', params={'language': language}).json()
            assert lesson['id'] == f'sample-{language}'
            assert len(lesson['scenes']) == 4
            assert lesson['source'] == 'sample'
            for scene in lesson['scenes']:
                response = client.get(scene['audio_url'])
                assert response.status_code == 200
                with wave.open(BytesIO(response.content)) as wav:
                    assert abs(wav.getnframes() / wav.getframerate() - scene['audio_duration']) < 0.002
                assert scene['captions'][0]['start'] == 0
                assert abs(scene['captions'][-1]['end'] - scene['audio_duration']) < 0.002


@pytest.mark.skipif(not (audio.tts_available('en') and audio.tts_available('hi')), reason='Local English and Hindi speech are required')
def test_full_planner_request_to_ollama_and_local_voice(fake_ollama):
    with TestClient(app) as client:
        assert client.get('/api/health').json()['ollama'] == 'ready'
        request = {'topic': 'Explain Python loops ' + uuid.uuid4().hex[:6], 'level': 'intermediate', 'language': 'en', 'target_seconds': 90}
        started = client.post('/api/lessons', json=request)
        assert started.status_code == 202
        job = finished_job(client, started.json()['job_id'])
        assert job['status'] == 'complete'
        lesson = job['lesson']
        assert lesson['source'] == 'ollama'
        assert lesson['level'] == 'intermediate'
        assert len(lesson['scenes']) == 3
        assert all(client.get(scene['audio_url']).status_code == 200 for scene in lesson['scenes'])
        path, payload = FakeOllama.calls[0]
        assert path == '/api/generate'
        assert payload['model'] == 'gemma3:4b'
        assert payload['stream'] is False
        assert payload['format']['properties']['scenes']['minItems'] == 3
        assert request['topic'] in payload['prompt']
        assert '90 seconds' in payload['prompt']
        assert 'intermediate' in payload['prompt']
        # A repeat of a successful request uses the local cache, not another model call.
        repeat = client.post('/api/lessons', json=request)
        cached = finished_job(client, repeat.json()['job_id'])
        assert cached['cached'] is True
        assert cached['lesson']['id'] == lesson['id']
        assert len(FakeOllama.calls) == 1

        # Revoice the same scene structure without re-planning or changing code.
        FakeOllama.response_text = json.dumps({
            'title': 'लूप कैसे काम करता है',
            'scenes': [
                {'heading': 'लूप से मिलें', 'narration': 'लूप एक निर्देश को दोहराता है।', 'items': []},
                {'heading': 'एक बार में एक', 'narration': 'हर बार अगला मान लिया जाता है।', 'items': ['शून्य', 'एक', 'दो']},
                {'heading': 'कोड पढ़ें', 'narration': 'हर मान के लिए निर्देश चलता है।', 'items': []},
            ],
        }, ensure_ascii=False)
        revoice = client.post(f"/api/lessons/{lesson['id']}/revoice", json={'language': 'hi'})
        translated_job = finished_job(client, revoice.json()['job_id'])
        assert translated_job['status'] == 'complete'
        translated = translated_job['lesson']
        assert translated['language'] == 'hi'
        assert translated['original_id'] == lesson['id']
        assert [s['type'] for s in translated['scenes']] == [s['type'] for s in lesson['scenes']]
        assert translated['scenes'][2]['code'] == lesson['scenes'][2]['code']
        assert translated['scenes'][2]['highlight_lines'] == [1, 2]
        assert all(client.get(scene['audio_url']).status_code == 200 for scene in translated['scenes'])
        assert len(FakeOllama.calls) == 2
        assert 'do not add, omit, explain or replan' in FakeOllama.calls[1][1]['prompt'].lower()
        back = client.post(f"/api/lessons/{translated['id']}/revoice", json={'language': 'en'})
        assert finished_job(client, back.json()['job_id'])['lesson']['id'] == lesson['id']
        repeat_hi = client.post(f"/api/lessons/{lesson['id']}/revoice", json={'language': 'hi'})
        assert finished_job(client, repeat_hi.json()['job_id'])['lesson']['id'] == translated['id']
        assert len(FakeOllama.calls) == 2
        malformed = json.loads(FakeOllama.response_text)
        malformed['scenes'][1]['items'] = []  # Translation must not alter the diagram structure.
        FakeOllama.response_text = json.dumps(malformed, ensure_ascii=False)
        bad = client.post(f"/api/lessons/{lesson['id']}/revoice", json={'language': 'ta'})
        rejected = finished_job(client, bad.json()['job_id'])
        assert rejected['status'] == 'error'
        assert 'original lesson is still available' in rejected['error']
        assert client.get(f"/api/lessons/{lesson['id']}").status_code == 200


def test_invalid_model_output_falls_back_in_requested_language(fake_ollama):
    FakeOllama.response_text = '{"title":"Invalid", "scenes":[]}'
    with TestClient(app) as client:
        started = client.post('/api/lessons', json={'topic': 'Light and prisms', 'language': 'hi', 'target_seconds': 60})
        job = finished_job(client, started.json()['job_id'])
        assert job['status'] == 'complete'
        assert job['lesson']['id'] == 'sample-hi'
        assert 'sample instead' in job['lesson']['notice']
        assert 'लूप' in job['lesson']['title']


def test_schema_rejects_non_visual_or_oversized_content():
    with pytest.raises(ValidationError):
        ScenePlan(type='diagram', heading='Oops', narration='Text', items=['only one'])
    with pytest.raises(ValidationError):
        ScenePlan(type='code_walkthrough', heading='Oops', narration='Text', code='x' * 39)
    with pytest.raises(ValidationError):
        LessonPlan(title='Oops', scenes=[])
    with pytest.raises(planner.PlanningError):
        planner.parse_plan(json.dumps(VALID_PLAN), 'ta')


def test_caption_segments_cover_audio_without_hardcoded_scene_lengths():
    text = ' '.join(['A clear explanation'] * 20)
    captions = make_captions(text, 12.345, max_chars=45)
    assert len(captions) > 1
    assert ' '.join(item['text'] for item in captions) == text
    assert captions[0]['start'] == 0
    assert captions[-1]['end'] == 12.345
    assert all(a['end'] == b['start'] for a, b in zip(captions, captions[1:]))


def test_linked_list_fallback_and_sample_revoice(fake_ollama):
    FakeOllama.response_text = '{"title":"Invalid", "scenes":[]}'
    with TestClient(app) as client:
        response = client.post('/api/lessons', json={'topic': 'Explain linked lists', 'language': 'en'})
        job = finished_job(client, response.json()['job_id'])
        lesson = job['lesson']
        assert lesson['id'] == 'sample-linked-en'
        assert lesson['source'] == 'sample'
        assert 'beginner singly linked-list introduction' in lesson['notice']
        assert len(lesson['scenes']) == 5
        assert lesson['scenes'][1]['items'][0] == 'head'
        assert all(client.get(s['audio_url']).status_code == 200 for s in lesson['scenes'])
        translated = client.post(f"/api/lessons/{lesson['id']}/revoice", json={'language': 'hi'})
        result = finished_job(client, translated.json()['job_id'])
        assert result['lesson']['id'] == 'sample-linked-hi'
        assert len(result['lesson']['scenes']) == len(lesson['scenes'])
        assert client.get('/api/sample?language=ta&kind=linked').json()['id'] == 'sample-linked-ta'
        assert client.get('/api/lessons/sample-linked-en').status_code == 200
        assert client.get('/api/audio/sample-linked-en/99').status_code == 404


def test_voice_routing_failure_is_not_silently_cached_as_kokoro(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(audio, 'kokoro_available', lambda language=None: language in ('en', 'hi'))
    monkeypatch.setattr(audio, '_synthesize_kokoro', lambda text, lang, path: calls.append(('kokoro', lang)) or 1.25)
    monkeypatch.setattr(audio, '_synthesize_espeak', lambda text, lang, path: calls.append(('espeak', lang)) or 1.0)
    assert audio.synthesize('Hello', 'en', tmp_path / 'en.wav') == 1.25
    assert audio.synthesize('नमस्ते', 'hi', tmp_path / 'hi.wav') == 1.25
    assert audio.synthesize('வணக்கம்', 'ta', tmp_path / 'ta.wav') == 1.0
    assert calls == [('kokoro', 'en'), ('kokoro', 'hi'), ('espeak', 'ta')]
    old_key = main.cache_key(main.LessonRequest(topic='Linked list', language='en'))
    monkeypatch.setattr(audio, 'kokoro_available', lambda language=None: False)
    new_key = main.cache_key(main.LessonRequest(topic='Linked list', language='en'))
    assert old_key != new_key
    monkeypatch.setattr(audio, 'kokoro_available', lambda language=None: True)
    def broken(*args):
        raise ValueError('bad model')
    monkeypatch.setattr(audio, '_synthesize_kokoro', broken)
    with pytest.raises(RuntimeError, match='Kokoro could not create narration'):
        audio.synthesize('Hello', 'en', tmp_path / 'broken.wav')
    assert calls == [('kokoro', 'en'), ('kokoro', 'hi'), ('espeak', 'ta')]


@pytest.mark.skipif(not audio.kokoro_available('en'), reason='Optional Kokoro model files not installed')
@pytest.mark.parametrize(('language', 'text'), [
    ('en', 'A node points to the next node.'),
    ('hi', 'हर नोड अगले नोड की ओर इशारा करता है।'),
])
def test_real_kokoro_creates_export_compatible_wav(language, text, tmp_path):
    path = tmp_path / f'{language}.wav'
    seconds = audio.synthesize(text, language, path)
    with wave.open(str(path), 'rb') as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == 22050
        assert wav.getnframes() > 22050
        assert abs(wav.getnframes() / wav.getframerate() - seconds) < 0.002
        assert any(wav.readframes(wav.getnframes()))


def test_verified_download_is_atomic(tmp_path):
    from setup_kokoro import checksum, download_verified
    source, dest = tmp_path / 'source', tmp_path / 'model'
    source.write_bytes(b'test model bytes')
    download_verified(source.as_uri(), dest, checksum(source))
    assert dest.read_bytes() == source.read_bytes()
    download_verified(source.as_uri(), dest, checksum(source))  # verified file is reused
    with pytest.raises(ValueError, match='SHA-256 verification failed'):
        download_verified(source.as_uri(), tmp_path / 'bad', '0' * 64)
    assert not (tmp_path / 'bad').exists()
    assert not (tmp_path / 'bad.part').exists()
