🎓 BLU Visual Teacher

Learn visually. Understand deeply.

BLU Visual Teacher transforms topics into visual lessons with narration and captions, helping learners understand concepts beyond plain text.

Instead of just reading an explanation, learners can follow a sequence of scenes, see how ideas connect, and listen to the lesson in their preferred supported language.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB" alt="React" />
  <img src="https://img.shields.io/badge/Local_AI-6C63A8?style=flat-square" alt="Local AI" />
  <img src="https://img.shields.io/badge/Open_Source_Friendly-E8F5E9?style=flat-square&logoColor=black" alt="Open source friendly" />
</p>

<p align="center">
  <a href="#-features">Features</a> ·
  <a href="#-how-it-works">How it works</a> ·
  <a href="#-tech-stack">Tech stack</a> ·
  <a href="#-getting-started">Get started</a>
</p>

💡 The Idea

Learning shouldn't stop at reading an explanation.

Some concepts are difficult to understand through text alone. Visual examples, step-by-step explanations, and audio can help make unfamiliar topics easier to follow.

BLU Visual Teacher brings these elements together in one learning experience.

🎬 See it: Learn through structured visual scenes.

🎙️ Hear it: Listen to generated narration.

💬 Follow it: Use captions alongside the explanation.

🌍 Learn in your language: Support for English, Hindi, and Tamil narration through configured local speech engines.

🖥️ Run locally: Use local AI and speech tools instead of depending entirely on cloud services.

✨ Features

<table>
  <tr>
    <td width="50%">
      <h3>🧠 AI-powered lessons</h3>
      Generate structured lesson content from a topic using a locally running language model.
    </td>
    <td width="50%">
      <h3>🎨 Visual explanations</h3>
      Present concepts as organized scenes instead of a single block of text.
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🔊 Audio narration</h3>
      Convert lesson text into speech using locally configured speech engines.
    </td>
    <td width="50%">
      <h3>📝 Synchronized learning support</h3>
      Combine narration, captions, and visual content to make lessons easier to follow.
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🎞️ MP4 video export</h3>
      Use FFmpeg to support exporting lessons as video.
    </td>
    <td width="50%">
      <h3>🔒 Local-first processing</h3>
      Run the AI model and supported speech components locally after the required setup and downloads.
    </td>
  </tr>
</table>

🔄 How It Works

flowchart TD
    A([Enter a topic]) --> B[React Frontend]
    B --> C[FastAPI Backend]
    C --> D[Ollama + Gemma 3]
    D --> E[Structured Lesson Scenes]
    E --> F[Visual Lesson Player]
    E --> G[Local Speech Engines]
    G --> H[Audio + Captions]
    F --> I[Lesson Experience]
    H --> I
    I --> J[FFmpeg Video Export]

    style A fill:#E7EAFB,stroke:#7774C7,color:#24264A
    style B fill:#DDF4EF,stroke:#4C9C8B,color:#173C36
    style C fill:#DDF4EF,stroke:#4C9C8B,color:#173C36
    style D fill:#F4E8FF,stroke:#A17AC4,color:#422C57
    style I fill:#FFE7D9,stroke:#D68A68,color:#603927
    style J fill:#FFF0C9,stroke:#C7A24B,color:#57451B

The basic flow:

The learner enters a topic.

The frontend sends the request to the backend.

The backend uses the local AI model to generate structured lesson content.

The lesson is presented through visual scenes and captions.

Configured speech engines generate narration.

FFmpeg handles the video export workflow.

🛠️ Tech Stack

Component

Technology

Purpose

Frontend

React, Vite

User interface and lesson presentation

Backend

Python, FastAPI

API and lesson-generation workflow

Language model

Ollama, Gemma 3 (4B)

Local lesson planning

English narration

Kokoro

Text-to-speech

Hindi narration

Kokoro

Text-to-speech

Tamil narration

eSpeak NG

Text-to-speech

Video processing

FFmpeg

MP4 export

Python environment

venv

Dependency isolation

🚀 Getting Started

Follow these steps to run BLU Visual Teacher on your own machine.

Prerequisites

Install the following before starting:

Python

Git

Node.js

Ollama

FFmpeg

eSpeak NG

Make sure FFmpeg and eSpeak NG are available through your system's PATH.

Verify the installations:

python --version
git --version
node --version
npm --version
ollama --version
ffmpeg -version
espeak-ng --version

1. Clone the repository

git clone https://github.com/Nithin9801/BLU-Elytra.git
cd BLU-Elytra/blu-visual-teacher

2. Prepare the local AI model

Make sure Ollama is installed and running.

Download the model used by the project:

ollama pull gemma3:4b

The initial download requires an internet connection. After downloading, Ollama can run the model locally.

3. Configure the backend

Create a Python virtual environment from the blu-visual-teacher directory:

cd backend
python -m venv venv

Activate it using the command for your operating system.

<details>
<summary><strong>Windows — PowerShell</strong></summary>

.\venv\Scripts\Activate.ps1

If script execution is blocked by your PowerShell policy, review your execution policy before changing it.

</details>

<details>
<summary><strong>Linux / macOS</strong></summary>

source venv/bin/activate

</details>

Install the Python dependencies:

python -m pip install -r requirements.txt

Download the Kokoro model and voice files required for English and Hindi narration:

python setup_kokoro.py

Start the backend server:

python -m uvicorn app.main:app --reload

Keep this terminal open.

The backend should now be available at:

API: http://127.0.0.1:8000

Interactive API documentation: http://127.0.0.1:8000/docs

4. Start the frontend

Open a second terminal. Navigate to the frontend directory from the project root:

cd frontend

If you are still inside backend, first return to the project root:

cd ..
cd frontend

Install the frontend dependencies:

npm install

Start the development server:

npm run dev

Open the local URL printed by Vite, usually:

http://localhost:5173

5. Start learning!

Make sure both the backend and frontend are running, and that Ollama is available.

Open the application in your browser and start exploring the learning experience.

⚙️ Important Notes

Internet access: Required initially to install dependencies and download AI and speech models.

Local processing: Supported AI and narration workflows can run locally once configured; this does not mean every dependency or feature is necessarily offline.

Video export: FFmpeg must be installed and accessible through PATH.

Speech engines: English and Hindi use Kokoro when configured successfully. Tamil uses eSpeak NG.

Multiple terminals: Keep the backend and frontend running together while using the development application.

Hardware: Performance depends on your system's available memory, CPU/GPU capabilities, and the models being used.

🗂️ Project Structure

The main application is organized into separate frontend and backend components.

BLU-Elytra/
└── blu-visual-teacher/
    ├── backend/
    │   ├── app/
    │   │   └── main.py
    │   ├── requirements.txt
    │   ├── setup_kokoro.py
    │   └── models/
    │
    └── frontend/
        ├── src/
        ├── package.json
        └── ...

Note: This is a simplified overview of the main application files; the exact structure may include additional files and directories.