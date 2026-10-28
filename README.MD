# BLU Visual Teacher

BLU Visual Teacher is a project built around making learning easier to understand through visual explanations and audio.  
Instead of relying only on written explanations, the idea is to make concepts easier to follow and learn.  
The project combines a web-based frontend with a backend that handles lesson generation, narration, and video export.

## Getting Started

Want to run it on your own machine? Let's get it running.

### 1. Download the project

Make sure you have [Python](https://www.python.org/downloads/), [Git](https://git-scm.com/downloads), and [Node.js](https://nodejs.org/en/download/) installed.

Open your terminal and run:

bash
git clone https://github.com/Nithin9801/BLU-Elytra.git
cd BLU-Elytra/blu-visual-teacher


### 2. Install the required tools

BLU uses a few local tools for AI-powered lesson generation, speech, and video export.

- **[Ollama](https://ollama.com/download)** — runs the lesson-planning model locally.
- **[FFmpeg](https://ffmpeg.org/download.html)** — handles MP4 video export.
- **[eSpeak NG](https://github.com/espeak-ng/espeak-ng/releases)** — provides local text-to-speech support, including Tamil.

Install the tools for your operating system. For FFmpeg and eSpeak NG, make sure their executable paths are added to your system's PATH if the installers do not do this automatically.

After installation, open a new terminal and check:

bash
ffmpeg -version
espeak-ng --version
ollama --version


If a command is not recognized, check that the corresponding tool is installed correctly and available through PATH.

### 3. Set up the local AI model

Make sure Ollama is installed and its local service is running.

Download the model used by BLU:

bash
ollama pull gemma3:4b


The model download requires an internet connection. Once downloaded, Ollama can run the model locally.

### 4. Set up the backend

Open a terminal in the blu-visual-teacher directory and run:

bash
cd backend
python -m venv venv


Activate the virtual environment.

*Windows PowerShell:*

powershell
.\venv\Scripts\Activate.ps1


*macOS or Linux:*

bash
source venv/bin/activate


Install the Python dependencies:

bash
python -m pip install -r requirements.txt


For English and Hindi narration, download and verify the local Kokoro speech model and voice files:

bash
python setup_kokoro.py


This downloads the required files into the backend's models directory. You need an internet connection for the initial download.

Now start the backend:

bash
python -m uvicorn app.main:app --reload


Keep this terminal running.

The backend will be available at:

- *API:* http://127.0.0.1:8000
- *Interactive API documentation:* http://127.0.0.1:8000/docs

### 5. Set up and start the frontend

Open a *second terminal*. Do not stop the backend.

Navigate to the frontend directory:

bash
cd BLU-Elytra/blu-visual-teacher/frontend


If your terminal is already inside blu-visual-teacher, use:

bash
cd frontend


Install the frontend dependencies:

bash
npm install


Start the development server:

bash
npm run dev


Open the local address displayed in your terminal, usually:

*http://localhost:5173*

That's it! Keep both terminals running while using BLU Visual Teacher.

## The Idea Behind BLU

*Learning shouldn't stop at reading an explanation.*

Sometimes, reading about a concept isn't enough. Seeing how it works, following its steps, and hearing an explanation can make it easier to understand.

That's the direction behind BLU Visual Teacher: turning a topic into a lesson with visual scenes, narration, and captions.

The project is also designed around local processing, using tools such as Ollama and local speech engines rather than relying entirely on cloud services.

## A Few Things to Know

- The first setup requires an internet connection to install dependencies and download the AI and speech models.
- Once the required models and dependencies are installed, supported lesson generation and narration can run locally.
- FFmpeg is required for video export.
- English and Hindi narration use Kokoro when configured successfully. Tamil uses eSpeak NG.
- Keep the backend and frontend running together for the application to work properly.

## Conclusion

BLU Visual Teacher is a step toward making technical and educational concepts easier to understand through visual explanations, narration, and interactive learning.

The goal is simple: *make learning clearer, one concept at a time.*