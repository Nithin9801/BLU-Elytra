# Blu Visual Teacher

A local-first visual lesson studio built with React, FastAPI, Ollama `gemma3:4b`, and offline narration. It generates title cards, labelled diagrams and code walkthroughs, with captions, playback, and 1280×720 H.264/AAC MP4 export. No external AI API is used, and generated code is displayed, never executed.

> **Prototype and eligibility:** the challenge requires code to be written during the event's 24 hours; check the rules before submitting. Review generated teaching content and translations for correctness. The English default is a US English Kokoro voice, not a verified Indian-English accent. Tamil currently uses the more robotic eSpeak NG voice, not Kokoro; a natural Tamil voice and native-speaker review are still needed to satisfy the natural-voice requirement fully.

## What changed: Kokoro narration

- New **English** lessons use Kokoro's `af_heart` voice; new **Hindi** lessons use `hf_alpha`. Both run on your machine, with no cloud speech API.
- **Tamil** new lessons use eSpeak NG. If Kokoro is not installed, English and Hindi use eSpeak NG when its executable is available. If no voice is available, the app explains the issue and displays a built-in sample.
- Install the model files once using the verified downloader below. The ZIP intentionally does **not** include the ~92 MB model or ~28 MB voice pack. You need internet for that one-time setup, after which Kokoro can work offline.
- The bundled English and Hindi Python-loop and linked-list samples have already been re-recorded with Kokoro. Tamil sample audio uses eSpeak. The older sample MP4s under `examples/` were made with eSpeak and have not been re-recorded.
- Old generated lessons contain their original WAVs and do not automatically change. A new cache-key version makes newly created lessons use the selected current voice instead of reusing the older eSpeak cache. After setup, click **Create my lesson** again rather than reopening an old lesson.
- When Ollama is unavailable or returns invalid output, the app labels the fallback honestly. A request containing “linked list” gets a built-in **beginner singly linked-list introduction**; other requests get the Python-loop sample. These are fixed samples, not custom answers.

## Laptop setup

Download the ZIP from this conversation and extract it to a **new folder** named `blu-visual-teacher`. Stop the old backend/frontend first so the ports are free. Using a new folder is easier and safer than guessing which old files to replace. Commands below run on the laptop hosting FastAPI and Ollama.

### Prerequisites

- **Python 3.10–3.13** (Python 3.12 recommended). `kokoro-onnx==0.6.1` does not install on Python 3.14.
- **Node.js 18 or 20+** and npm for the frontend.
- [Ollama](https://ollama.com/download) for custom lessons. Pull `gemma3:4b` once while online. Gemma 3 4B is a separate multi-gigabyte download; sufficient laptop memory and time are required.
- **eSpeak NG** for Tamil (and fallback English/Hindi) and **FFmpeg** with `libx264` for video export. Both executables need to be on your PATH. Kokoro's Python dependency includes an eSpeak NG library for phonemization, but that does not provide the `espeak-ng` command needed by our Tamil fallback.
- Pillow with libraqm for correct Hindi/Tamil shaping in video export (see the font check below).

On Debian/Ubuntu: `sudo apt install espeak-ng ffmpeg`. On macOS with Homebrew: `brew install espeak-ng ffmpeg`. On Windows install [eSpeak NG](https://github.com/espeak-ng/espeak-ng/releases) and an FFmpeg build containing `libx264`, then reopen the terminal and check `espeak-ng --version` and `ffmpeg -version`. See the tools' official installation instructions if necessary.

### 1. Prepare the lesson planner

In a terminal, after installing and starting Ollama:

```text
ollama pull gemma3:4b
```

Keep Ollama running. If its local server is not already started by the app, run `ollama serve` in a separate terminal. Kokoro is independent of Ollama: Kokoro speaks text; Ollama writes custom lesson plans.

### 2. Install Kokoro and start FastAPI

In a terminal, go to the extracted project’s `backend` folder. On **Windows PowerShell** (if Python 3.12 is installed through the standard Python installer):

```powershell
cd path\to\blu-visual-teacher\backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe setup_kokoro.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

On **macOS/Linux** (replace `python3.12` with another installed 3.10–3.13 interpreter if needed):

```bash
cd /path/to/blu-visual-teacher/backend
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python setup_kokoro.py
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The first two installation commands and the downloader need the internet; subsequent runs only need the last command. The downloader verifies SHA-256 before installing, skips already verified files, and can be rerun if interrupted. It creates:

```text
backend/models/kokoro-v1.0.int8.onnx
backend/models/kokoro-voices.bin
```

Once FastAPI is running, open `http://127.0.0.1:8000/api/health`. Under `tts_languages`, English and Hindi should show `"engine": "kokoro"`; Tamil shows `"espeak-ng"` if the executable is on PATH. `ollama` should be `"ready"` for custom lessons, and `ffmpeg` should be `true` for MP4 export. A health check reports file/package availability; if a synthesis actually fails, read the backend terminal for details.

### 3. Start the frontend

Open a **second terminal** in the extracted `frontend` folder:

```text
cd path/to/blu-visual-teacher/frontend
npm ci
npm run dev -- --host 127.0.0.1
```

Open the address printed by Vite, normally `http://127.0.0.1:5173`. Enter a concept, choose English or Hindi, and click **Create my lesson**. You can also click the **Linked lists** example to try the built-in fallback if Ollama is offline. Play the result, change its language, or export it to MP4.

By default Vite proxies `/api` to FastAPI on port 8000. To put the **frontend on port 8000** instead, start FastAPI on port 8001 and point Vite to it. On macOS/Linux:

```bash
# In backend: .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
# In frontend:
BLU_API_PROXY_TARGET=http://127.0.0.1:8001 npm run dev -- --host 127.0.0.1 --port 8000 --strictPort
```

On Windows PowerShell:

```powershell
# In backend: .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
# In frontend:
$env:BLU_API_PROXY_TARGET = 'http://127.0.0.1:8001'
npm run dev -- --host 127.0.0.1 --port 8000 --strictPort
```

### Optional: change the Kokoro voice

Before starting FastAPI, set `BLU_KOKORO_EN_VOICE` or `BLU_KOKORO_HI_VOICE` to a voice ID from the downloaded pack. The defaults are `af_heart` and `hf_alpha`; other Hindi IDs include `hf_beta`, `hm_omega` and `hm_psi`. The English locale remains `en-us`. A voice/locale mismatch can affect pronunciation. These settings change **new generated lessons**, not prerecorded samples or old WAVs. Restart the backend after changing them. See [Kokoro voice details](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md).

For example, in PowerShell before starting the backend: `$env:BLU_KOKORO_HI_VOICE = 'hm_omega'`. In macOS/Linux: `export BLU_KOKORO_HI_VOICE=hm_omega`.

### Troubleshooting

- **Still hear the old voice?** Use the new extracted folder, check `tts_languages` in `/api/health`, restart FastAPI, and create the lesson again. Preexisting lessons and the old example MP4s keep their existing audio. Hard-refresh the browser if it has cached an earlier sample.
- **Health says `espeak-ng` for English/Hindi:** make sure you ran the backend virtual environment’s `python -m pip install -r requirements.txt` and `python setup_kokoro.py`, then restart FastAPI. The model filenames must match the paths above.
- **Kokoro fails during synthesis:** check the backend terminal. Rerun the downloader to verify the files. An installed but broken Kokoro does not silently get cached as eSpeak.
- **Only a sample appears:** check `/api/health` and start Ollama / run `ollama pull gemma3:4b` on the FastAPI machine. The sample notice also appears when the model returns invalid output.
- **Tamil unavailable:** install eSpeak NG and ensure `espeak-ng --version` works in the terminal from which FastAPI is launched. Restart the backend.
- **Port already in use:** stop the older server, or use the port-8000 frontend arrangement above.
- **Wrong Python version:** use a Python 3.10–3.13 interpreter to create a fresh `.venv`. The Kokoro 0.6.1 package excludes Python 3.14.

## Architecture and limitations

- FastAPI calls `${OLLAMA_URL:-http://127.0.0.1:11434}/api/generate` with `${OLLAMA_MODEL:-gemma3:4b}`. Pydantic validates 3–6 scenes and bounds visual labels/code. Only project-owned components are rendered.
- Scene length is the measured WAV duration plus a 0.6-second pause. Captions are approximate chunks, not forced word alignment. Target length is a target, not a strict trim. Diagram arrows depict a sequence and need review against the topic.
- Changing language for a generated lesson asks Ollama to translate text, preserves its scene types/code/highlights, and synthesizes fresh audio. A translation error leaves the original lesson available. The built-in samples use hand-written translations.
- Kokoro uses an ONNX int8 model and creates mono 22,050 Hz PCM WAVs locally; samples and new lessons can be played without a network once dependencies are present. English/Hindi pronunciation, especially mixed-script technical words, needs human review. Performance depends on the laptop.
- Generation and export use background jobs. Successful lessons are cached by request, model and voice/version. Files and render caches live in `backend/data/`; delete that directory to clear them. `BLU_KOKORO_MODEL` and `BLU_KOKORO_VOICES` optionally override model paths.
- **Security:** the prototype has no authentication. Keep both servers on loopback and do not expose them publicly. The Vite config allows preview hosts for the hosted development environment; local commands above override its host binding.

Check Hindi/Tamil font shaping with the backend virtual environment:

```text
python -c "from PIL import features; print('libraqm:', features.check_feature('raqm'))"
```

For the correct interpreter, replace `python` with `.venv/bin/python` on macOS/Linux or `.\.venv\Scripts\python.exe` on Windows. Indic MP4 export reports an error if libraqm is unavailable rather than silently producing unshaped text.

## API sketch

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Ollama/model, local speech engine per language, and FFmpeg status |
| `GET /api/sample?language=en&kind=linked` | Built-in loops or linked-list sample, in `en`, `hi` or `ta` |
| `POST /api/lessons` | Start lesson with `topic`, `level`, `language`, `target_seconds` |
| `POST /api/lessons/{id}/revoice` | Translate/revoice an existing lesson |
| `GET /api/jobs/{id}` | Job status and result |
| `GET /api/audio/{id}/{index}` | Scene narration WAV |
| `POST /api/lessons/{id}/export` | Start MP4/SRT render |
| `GET /api/exports/{id}/lesson.mp4` | Download video |

## Tests

```text
# In backend, using its virtual environment's Python:
python -m pip install -r requirements-dev.txt
python -m pytest -q
# In frontend:
npm ci
npm run build
```

The test suite uses a **mock Ollama server** to check `gemma3:4b` requests, validated generation, voice and cache behavior, translation and fallback. The Kokoro int8 model was also exercised locally for English and Hindi on Linux, and Tamil eSpeak was exercised. This development sandbox did not run a real Gemma 3 4B model; real-model output, resource usage and latency still need to be verified on your laptop.

## Licences and assets

Review upstream terms and redistribution obligations for the exact files/binaries you use. The ZIP does not bundle Ollama, Gemma, or the Kokoro model/voice weights.

| Component | Licence / note |
| --- | --- |
| Gemma 3 4B weights | Gemma Terms of Use and prohibited-use policy, not Apache-2.0: https://ai.google.dev/gemma/terms |
| Kokoro ONNX wrapper | MIT: https://github.com/thewh1teagle/kokoro-onnx |
| Kokoro v1.0 model and voice pack | Apache-2.0 according to the upstream model: https://huggingface.co/hexgrad/Kokoro-82M; voice-specific notes: https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md |
| eSpeak NG | GPL-3.0-or-later; the Kokoro dependency `espeakng-loader` bundles an eSpeak library, and the app also uses the executable for Tamil: https://github.com/espeak-ng/espeak-ng |
| phonemizer Python package | GPL-3.0-or-later; check the installed package's notices. |
| FFmpeg with libx264 | The licence depends on the build; enabling GPL components such as libx264 makes that FFmpeg build GPL. |
| Noto Sans Devanagari, Noto Sans Tamil, DM Sans | SIL Open Font License 1.1; notices in `backend/assets/fonts/`. |
| DejaVu Sans Mono | DejaVu/Bitstream font licence; notice bundled in `backend/assets/fonts/`. |
| React, Vite, FastAPI, Pydantic | MIT; inspect installed packages for notices. |
| lucide-react | ISC. |
| Uvicorn, HTTPX | BSD-3-Clause. |
| Pillow | MIT-CMU (historical PIL licence). |
| Newly authored project source | No project licence has been declared; choose one before redistribution. |

The English/Hindi sample WAVs were generated from the hand-written sample text with Kokoro; Tamil sample WAVs and the older example MP4s were generated with eSpeak NG. This note is not legal advice.
