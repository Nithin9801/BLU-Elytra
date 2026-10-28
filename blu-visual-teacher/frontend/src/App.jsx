import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ArrowDownToLine, ArrowRight, BookOpen, Captions, Check, ChevronDown,
  CircleHelp, Clapperboard, Clock3, Code2, Copy, Film, GraduationCap,
  Layers3, LoaderCircle, LockKeyhole, MonitorPlay, Pause, Play,
  RotateCcw, SkipBack, SkipForward, Sparkles, Volume2, WandSparkles, X,
} from 'lucide-react';

const LANGUAGES = {
  en: { label: 'English', short: 'EN', native: 'English' },
  hi: { label: 'Hindi', short: 'हि', native: 'हिन्दी' },
  ta: { label: 'Tamil', short: 'த', native: 'தமிழ்' },
};
const SCENE_LABELS = { title_card: 'The big idea', diagram: 'Visual diagram', code_walkthrough: 'Code walkthrough' };
const EXAMPLES = [
  { label: 'Python loops', topic: 'How does a Python loop work?' },
  { label: 'Linked lists', topic: 'How does a linked list work?' },
  { label: 'Photosynthesis', topic: 'How does photosynthesis work?' },
  { label: 'The water cycle', topic: 'How does the water cycle work?' },
];

async function api(url, options) {
  const response = await fetch(url, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Something went wrong. Please try again.');
  return data;
}
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const timeLabel = (seconds) => {
  const value = Math.max(0, Math.floor(Number(seconds) || 0));
  return `${Math.floor(value / 60)}:${String(value % 60).padStart(2, '0')}`;
};

function BluMark({ small = false }) {
  return <span className={`blu-mark ${small ? 'blu-mark-small' : ''}`} aria-hidden="true"><span /><span /><span /></span>;
}

function SceneArt({ scene, playing, time }) {
  const active = Math.min((scene.items?.length || 1) - 1,
    Math.floor((time / Math.max(scene.audio_duration, 0.01)) * (scene.items?.length || 1)));
  if (scene.type === 'diagram') {
    return <div className="visual-wrap diagram-visual" aria-hidden="true">
      <div className="visual-orbit orbit-one" /><div className="visual-orbit orbit-two" />
      <div className="diagram-overline"><span /> FOLLOW THE STEPS</div>
      <div className="diagram-cards">
        {(scene.items || []).map((item, i) => <React.Fragment key={`${item}-${i}`}>
          <div className={`diagram-node ${i === active ? 'is-current' : ''}`}>
            <span className="node-num">0{i + 1}</span><strong>{item}</strong>
          </div>
          {i < scene.items.length - 1 && <ArrowRight className="node-arrow" size={16} />}
        </React.Fragment>)}
      </div>
      <span className="mini-spark diagram-spark"><Sparkles size={21} /></span>
    </div>;
  }
  if (scene.type === 'code_walkthrough') {
    const lines = (scene.code || '').split('\n').slice(0, 5);
    const highlights = scene.highlight_lines || [];
    const highlightedLine = highlights.length ? highlights[Math.min(highlights.length - 1, Math.floor(time / Math.max(scene.audio_duration, 0.01) * highlights.length))] : null;
    return <div className="visual-wrap code-visual" aria-hidden="true">
      <div className="visual-orbit orbit-one" /><div className="visual-orbit orbit-two" />
      <div className="code-editor">
        <div className="window-bar"><span className="window-dots"><i /><i /><i /></span><span>LET'S LOOK CLOSER</span></div>
        <div className="editor-lines">{lines.map((line, i) => <div className={`editor-line ${highlightedLine === i + 1 ? 'highlighted' : ''}`} key={i}>
          <span className="line-number">{i + 1}</span><code>{line || ' '}</code>
        </div>)}</div>
      </div>
      <span className="mini-spark code-spark"><Code2 size={20} /></span>
    </div>;
  }
  const values = scene.items?.length ? scene.items.slice(0, 3) : ['01', '02', '03'];
  return <div className={`visual-wrap title-visual ${playing ? 'visual-playing' : ''}`} aria-hidden="true">
    <div className="visual-orbit orbit-one" /><div className="visual-orbit orbit-two" />
    <span className="orbit-dot orbit-dot-one" /><span className="orbit-dot orbit-dot-two" />
    <div className="idea-card">
      <div className="window-dots"><i /><i /><i /></div>
      {scene.code ? <div className="idea-code">{scene.code.split('\n').slice(0, 3).map((line, i) => <code key={i}>{line || ' '}</code>)}</div>
        : <div className="idea-message"><span>ONE IDEA AT A TIME</span><strong>Let's make it click.</strong></div>}
      <div className="idea-values">{values.map((item, i) => <span key={i}>{item}</span>)}</div>
    </div>
    <span className="mini-spark title-spark"><Sparkles size={22} /></span>
    <div className="float-label"><span className="float-label-icon"><Play size={9} fill="currentColor" /></span><span>made to<br /><strong>make sense</strong></span></div>
  </div>;
}

function LessonStage({ lesson, scene, index, playing, time }) {
  const caption = scene.captions?.find((part) => time >= part.start && time < part.end)?.text
    || scene.captions?.[scene.captions.length - 1]?.text || scene.narration;
  return <div className={`scene-stage scene-${scene.type} ${playing ? 'is-playing' : ''}`}>
    <div className="stage-bubble" /><div className="stage-dots" />
    <div className="stage-topline">
      <span className="stage-kicker"><Sparkles size={13} /> {SCENE_LABELS[scene.type]}</span>
      <span className="stage-count">{String(index + 1).padStart(2, '0')} <span>/</span> {String(lesson.scenes.length).padStart(2, '0')}</span>
    </div>
    <div className={`stage-heading ${scene.heading.length > 48 ? 'long-heading' : ''}`}>
      <span className="stage-heading-label">A LITTLE CLARITY, COMING UP</span>
      <h2 lang={lesson.language}>{scene.heading}</h2>
      <span className="stage-heading-line" />
      <p>{scene.type === 'title_card' ? 'Let’s break it down.' : scene.type === 'diagram' ? 'See how it all connects.' : 'Take it one step at a time.'}</p>
    </div>
    <SceneArt scene={scene} playing={playing} time={time} />
    <div className="caption-bar" aria-live="off">
      <span className="caption-icon"><Captions size={15} /></span>
      <span lang={lesson.language}>{caption}</span>
    </div>
  </div>;
}

function useLessonPlayer(lesson, setMessage) {
  const audioRef = useRef(null);
  const gapTimer = useRef(null);
  const playingRef = useRef(false);
  const seekRef = useRef(0);
  const [index, setIndex] = useState(0);
  const [playing, setPlayingState] = useState(false);
  const [time, setTime] = useState(0);
  const [ended, setEnded] = useState(false);
  const setPlaying = useCallback((value) => { playingRef.current = value; setPlayingState(value); }, []);

  useEffect(() => {
    clearTimeout(gapTimer.current);
    setPlaying(false); setIndex(0); setTime(0); setEnded(false); seekRef.current = 0;
    return () => clearTimeout(gapTimer.current);
  }, [lesson, setPlaying]);

  useEffect(() => {
    if (!lesson?.scenes?.[index] || !audioRef.current) return;
    const audio = audioRef.current;
    clearTimeout(gapTimer.current);
    audio.pause();
    audio.src = lesson.scenes[index].audio_url;
    audio.load();
    const seek = Math.max(0, seekRef.current || 0);
    seekRef.current = 0;
    setTime(seek);
    const applySeek = () => { if (seek) { try { audio.currentTime = seek; } catch (_) { /* metadata may not be ready */ } } };
    audio.addEventListener('loadedmetadata', applySeek, { once: true });
    if (playingRef.current) audio.play().catch(() => { setPlaying(false); setMessage('The audio could not play. Please try again.'); });
    return () => audio.removeEventListener('loadedmetadata', applySeek);
  }, [lesson, index, setPlaying, setMessage]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !lesson) return;
    if (playing) {
      if (!audio.ended) audio.play().catch(() => { setPlaying(false); setMessage('The audio could not play. Please try again.'); });
    } else {
      audio.pause();
      clearTimeout(gapTimer.current);
    }
  }, [playing, lesson, setPlaying, setMessage]);

  const replay = () => {
    clearTimeout(gapTimer.current); setEnded(false); seekRef.current = 0;
    if (index === 0 && audioRef.current) { audioRef.current.currentTime = 0; setTime(0); }
    else setIndex(0);
    setPlaying(true);
    if (index === 0) audioRef.current?.play().catch(() => setPlaying(false));
  };
  const toggle = () => {
    if (ended) { replay(); return; }
    if (!playingRef.current && audioRef.current?.ended) {
      if (index < lesson.scenes.length - 1) { seekRef.current = 0; setIndex(index + 1); setEnded(false); setPlaying(true); }
      else replay();
      return;
    }
    setPlaying(!playingRef.current);
  };
  const goTo = (next) => {
    if (!lesson) return;
    clearTimeout(gapTimer.current); setEnded(false); seekRef.current = 0;
    const target = Math.max(0, Math.min(lesson.scenes.length - 1, next));
    if (target === index && audioRef.current) {
      audioRef.current.currentTime = 0; setTime(0);
      if (playingRef.current) audioRef.current.play().catch(() => setPlaying(false));
    } else setIndex(target);
  };
  const onEnded = () => {
    if (!playingRef.current || !lesson) return;
    setTime(lesson.scenes[index].audio_duration);
    clearTimeout(gapTimer.current);
    gapTimer.current = setTimeout(() => {
      if (!playingRef.current) return;
      if (index < lesson.scenes.length - 1) { seekRef.current = 0; setIndex(index + 1); }
      else { setPlaying(false); setEnded(true); }
    }, lesson.scenes[index].pause_seconds * 1000);
  };
  const total = useMemo(() => lesson?.scenes.reduce((sum, s) => sum + s.audio_duration + s.pause_seconds, 0) || 0, [lesson]);
  const elapsed = useMemo(() => {
    if (!lesson) return 0;
    const before = lesson.scenes.slice(0, index).reduce((sum, s) => sum + s.audio_duration + s.pause_seconds, 0);
    return ended ? total : Math.min(total, before + time);
  }, [lesson, index, time, ended, total]);
  const seek = (value) => {
    if (!lesson) return;
    clearTimeout(gapTimer.current); setEnded(false);
    let remaining = Number(value);
    let target = lesson.scenes.length - 1;
    for (let i = 0; i < lesson.scenes.length; i++) {
      const length = lesson.scenes[i].audio_duration + lesson.scenes[i].pause_seconds;
      if (remaining < length || i === lesson.scenes.length - 1) { target = i; break; }
      remaining -= length;
    }
    const local = Math.min(Math.max(0, remaining), Math.max(0, lesson.scenes[target].audio_duration - 0.05));
    if (target === index && audioRef.current) {
      audioRef.current.currentTime = local; setTime(local);
      if (playingRef.current) audioRef.current.play().catch(() => setPlaying(false));
    } else { seekRef.current = local; setIndex(target); }
  };
  return { audioRef, index, playing, time, ended, total, elapsed, toggle, replay, goTo, onEnded, seek,
    onTimeUpdate: () => setTime(audioRef.current?.currentTime || 0) };
}

function MiniScene({ type }) {
  if (type === 'diagram') return <div className="mini-diagram"><span /><i /><span /><i /><span /></div>;
  if (type === 'code_walkthrough') return <div className="mini-code"><i /><i /><i /></div>;
  return <div className="mini-title"><Sparkles size={15} /><span /><span /></div>;
}

function HelpModal({ onClose }) {
  const [copied, setCopied] = useState(false);
  useEffect(() => {
    const listener = (event) => { if (event.key === 'Escape') onClose(); };
    window.addEventListener('keydown', listener); return () => window.removeEventListener('keydown', listener);
  }, [onClose]);
  const copy = async () => {
    try { await navigator.clipboard.writeText('ollama pull gemma3:4b'); setCopied(true); setTimeout(() => setCopied(false), 2000); } catch (_) { /* command remains selectable */ }
  };
  return <div className="modal-overlay" onMouseDown={onClose}>
    <section className="help-modal" role="dialog" aria-modal="true" aria-labelledby="help-title" onMouseDown={(e) => e.stopPropagation()}>
      <button className="modal-close icon-button" aria-label="Close" onClick={onClose}><X size={19} /></button>
      <span className="modal-icon"><Sparkles size={20} /></span>
      <div className="eyebrow">A LITTLE HELPING HAND</div>
      <h2 id="help-title">Made to work locally.</h2>
      <p>Blu turns a concept into scenes, local narration, and a downloadable video. Your lesson is created on the machine running the backend.</p>
      <div className="help-steps">
        <div><span>1</span><p><strong>Start Ollama</strong><small>Install Ollama and make sure its local server is running.</small></p></div>
        <div><span>2</span><p><strong>Pull the lesson planner</strong><small>Download the model once, before going offline.</small></p></div>
        <div className="command"><code>ollama pull gemma3:4b</code><button onClick={copy} aria-label="Copy command">{copied ? <Check size={15} /> : <Copy size={15} />}</button></div>
        <div><span>3</span><p><strong>Set up local speech</strong><small>Run python setup_kokoro.py in the backend folder for English and Hindi. Tamil uses eSpeak NG. See the README.</small></p></div>
        <div><span>4</span><p><strong>Install FFmpeg</strong><small>FFmpeg provides local MP4 export.</small></p></div>
      </div>
      <div className="help-note"><BookOpen size={17} /><span>Until Ollama is ready, you can play a built-in Python loop sample or ask for a beginner linked-list sample in English, Hindi, or Tamil.</span></div>
      <button className="modal-done" onClick={onClose}>Got it <ArrowRight size={16} /></button>
    </section>
  </div>;
}

function App() {
  const [topic, setTopic] = useState('How does a Python loop work?');
  const [level, setLevel] = useState('beginner');
  const [language, setLanguage] = useState('en');
  const [length, setLength] = useState(60);
  const [lesson, setLesson] = useState(null);
  const [health, setHealth] = useState(null);
  const [busy, setBusy] = useState(false);
  const [stage, setStage] = useState('');
  const [message, setMessage] = useState('');
  const [help, setHelp] = useState(false);
  const [exportJob, setExportJob] = useState(null);
  const [sampleLoading, setSampleLoading] = useState(false);
  const [revoicing, setRevoicing] = useState(false);
  const [revoiceStage, setRevoiceStage] = useState('');
  const generationCounter = useRef(0);
  const sampleCounter = useRef(0);
  const exportCounter = useRef(0);
  const revoiceCounter = useRef(0);
  const player = useLessonPlayer(lesson, setMessage);
  const activateLesson = useCallback((nextLesson) => {
    exportCounter.current += 1; // Ignore work finishing for a previous lesson.
    revoiceCounter.current += 1;
    setRevoicing(false);
    setExportJob(null);
    setLesson(nextLesson);
  }, []);

  const refreshHealth = useCallback(async () => {
    try { setHealth(await api('/api/health')); } catch (_) { setHealth({ ollama: 'backend_offline' }); }
  }, []);
  useEffect(() => {
    refreshHealth();
    const timer = setInterval(refreshHealth, 30000);
    return () => clearInterval(timer);
  }, [refreshHealth]);

  const loadSample = useCallback(async (lang, clearNotice = true, kind = 'loops') => {
    const requestId = ++sampleCounter.current;
    generationCounter.current += 1;
    revoiceCounter.current += 1;
    setRevoicing(false);
    setBusy(false);
    setSampleLoading(true);
    try {
      const sample = await api(`/api/sample?language=${encodeURIComponent(lang)}&kind=${encodeURIComponent(kind)}`);
      if (requestId !== sampleCounter.current) return;
      activateLesson(sample);
      if (clearNotice) setMessage('');
    } catch (_) {
      if (requestId === sampleCounter.current) setMessage('The lesson backend is unavailable. Start the FastAPI server to see the sample.');
    } finally {
      if (requestId === sampleCounter.current) setSampleLoading(false);
    }
  }, [activateLesson]);
  useEffect(() => { loadSample('en'); }, [loadSample]);

  const changeLanguage = (event) => {
    const next = event.target.value;
    setLanguage(next);
    if (lesson?.source === 'sample' && !busy) loadSample(next, true, lesson.id.startsWith('sample-linked-') ? 'linked' : 'loops');
  };
  const revoice = async (event) => {
    const target = event.target.value;
    if (!lesson || target === lesson.language || revoicing) return;
    if (lesson.source === 'sample') {
      setLanguage(target);
      loadSample(target, true, lesson.id.startsWith('sample-linked-') ? 'linked' : 'loops');
      return;
    }
    const requestId = ++revoiceCounter.current;
    setRevoicing(true); setRevoiceStage('Translating your lesson'); setMessage('');
    try {
      const started = await api(`/api/lessons/${lesson.id}/revoice`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ language: target }),
      });
      for (let n = 0; n < 310; n++) {
        const job = await api(`/api/jobs/${started.job_id}`);
        if (requestId !== revoiceCounter.current) return;
        setRevoiceStage(job.stage || 'Creating the new voice');
        if (job.status === 'complete') {
          activateLesson(job.lesson);
          setLanguage(target);
          setMessage(job.cached ? 'This language version was loaded from your local cache.' : 'The same scenes are ready in the new language.');
          return;
        }
        if (job.status === 'error') throw new Error(job.error || 'The lesson could not be revoiced.');
        await wait(1000);
      }
      throw new Error('Revoicing is taking longer than expected. Your original lesson is still available.');
    } catch (error) {
      if (requestId === revoiceCounter.current) setMessage(error.message || 'Could not revoice the lesson.');
    } finally {
      if (requestId === revoiceCounter.current) setRevoicing(false);
    }
  };
  const generate = async (event) => {
    event.preventDefault();
    if (topic.trim().length < 3) { setMessage('Add a topic of at least three characters to get started.'); return; }
    const requestId = ++generationCounter.current;
    sampleCounter.current += 1;
    revoiceCounter.current += 1;
    setRevoicing(false);
    setSampleLoading(false);
    setBusy(true); setMessage(''); setStage('Planning your lesson');
    try {
      const started = await api('/api/lessons', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: topic.trim(), level, language, target_seconds: length }) });
      for (let n = 0; n < 310; n++) {
        const job = await api(`/api/jobs/${started.job_id}`);
        if (generationCounter.current !== requestId) return;
        setStage(job.stage || 'Creating your lesson');
        if (job.status === 'complete') {
          activateLesson(job.lesson);
          setMessage(job.lesson.notice || (job.cached ? 'Loaded your previously created lesson from the local cache.' : ''));
          refreshHealth(); return;
        }
        if (job.status === 'error') throw new Error(job.error || 'Could not create the lesson.');
        await wait(1000);
      }
      throw new Error('The request is still taking a while. Check the backend and try again.');
    } catch (error) {
      if (generationCounter.current === requestId) setMessage(error.message || 'Could not reach the lesson backend.');
    } finally { if (generationCounter.current === requestId) setBusy(false); }
  };
  const exportVideo = async () => {
    if (!lesson || exportJob?.working) return;
    if (exportJob?.videoUrl) return;
    const requestId = ++exportCounter.current;
    setExportJob({ working: true, progress: 0 }); setMessage('');
    try {
      const started = await api(`/api/lessons/${lesson.id}/export`, { method: 'POST' });
      for (let n = 0; n < 600; n++) {
        const job = await api(`/api/jobs/${started.job_id}`);
        if (requestId !== exportCounter.current) return;
        if (job.status === 'complete') {
          setExportJob({ working: false, videoUrl: job.video_url, srtUrl: job.srt_url, progress: 1 });
          setMessage('Your 720p video is ready. Download the MP4 and optional captions below.');
          return;
        }
        if (job.status === 'error') throw new Error(job.error || 'The video could not be exported.');
        setExportJob({ working: true, progress: job.progress || 0 });
        await wait(1000);
      }
      throw new Error('Export is taking longer than expected. Check the backend.');
    } catch (error) {
      if (requestId === exportCounter.current) { setExportJob(null); setMessage(error.message || 'Could not export the video.'); }
    }
  };
  const statusText = !health ? 'Checking Ollama' : health.ollama === 'ready' ? 'Ollama connected' : health.ollama === 'model_missing' ? 'Model not installed' : health.ollama === 'backend_offline' ? 'Backend offline' : 'Ollama offline';
  const statusReady = health?.ollama === 'ready';
  const current = lesson?.scenes?.[player.index];
  const voiceEngine = health?.tts_languages?.[language]?.engine;
  const voiceHint = voiceEngine === 'kokoro' ? 'Kokoro ready for new narration' : voiceEngine === 'espeak-ng' ? 'eSpeak NG for new narration' : voiceEngine === 'unavailable' ? 'No local voice for this language' : 'Local by design. Made for curious minds.';

  return <div className="app-shell">
    <aside className="rail" aria-label="Navigation">
      <button className="rail-brand" aria-label="Blu home" onClick={() => loadSample(language)}><BluMark /></button>
      <div className="rail-separator" />
      <button className="rail-button selected" aria-label="Lesson studio" title="Lesson studio"><MonitorPlay size={20} /></button>
      <button className="rail-button" aria-label="Load sample lesson" title="Load sample lesson" onClick={() => loadSample(language)}><Layers3 size={20} /></button>
      <div className="rail-bottom"><button className="rail-button" aria-label="Setup help" title="Setup help" onClick={() => setHelp(true)}><CircleHelp size={20} /></button><span className="rail-avatar">B</span></div>
    </aside>

    <aside className="create-panel">
      <div className="brand-row"><div className="brand-word">blu<span>.</span><small>VISUAL TEACHER</small></div><span className="brand-badge">STUDIO</span></div>
      <div className="panel-inner">
        <div className="panel-intro">
          <span className="eyebrow"><span className="eyebrow-spark">✳</span> LET'S CREATE SOMETHING</span>
          <h1>What are we<br />{' '}learning today<span>?</span></h1>
          <p>Give us an idea. We’ll help you make it make sense.</p>
        </div>
        <form onSubmit={generate}>
          <div className="field-heading"><label htmlFor="topic">YOUR CONCEPT</label><span>{topic.length}/280</span></div>
          <div className="topic-wrap"><textarea id="topic" maxLength={280} value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="e.g. How does a Python loop work?" rows={3} /><span className="topic-spark"><Sparkles size={16} /></span></div>
          <div className="examples"><span>Try:</span>{EXAMPLES.map((example) => <button type="button" key={example.label} onClick={() => setTopic(example.topic)}>{example.label}</button>)}</div>
          <div className="field-block"><div className="field-heading"><span>LEARNER LEVEL</span><GraduationCap size={15} /></div>
            <div className="segmented level-segment" role="group" aria-label="Learner level">{['beginner', 'intermediate'].map((item) => <button type="button" key={item} aria-pressed={level === item} className={level === item ? 'active' : ''} onClick={() => setLevel(item)}>{item === 'beginner' && <span className="level-dot" />}{item[0].toUpperCase() + item.slice(1)}</button>)}</div>
          </div>
          <div className="field-block"><div className="field-heading"><label htmlFor="language">LESSON LANGUAGE</label><span>3 available</span></div>
            <div className="select-wrap"><span className="language-icon">अ<span>A</span></span><select id="language" value={language} onChange={changeLanguage} disabled={busy || revoicing}><option value="en">English</option><option value="hi">हिन्दी (Hindi)</option><option value="ta">தமிழ் (Tamil)</option></select><ChevronDown size={16} /></div>
          </div>
          <div className="field-block length-block"><div className="field-heading"><span>TARGET LENGTH</span><Clock3 size={14} /></div>
            <div className="segmented length-segment" role="group" aria-label="Target lesson length">{[30, 60, 90].map((seconds) => <button type="button" key={seconds} aria-pressed={length === seconds} className={length === seconds ? 'active' : ''} onClick={() => setLength(seconds)}>{seconds} sec</button>)}</div>
          </div>
          <button className="generate-button" type="submit" disabled={busy || revoicing || topic.trim().length < 3}>
            {busy ? <LoaderCircle className="spin" size={18} /> : <WandSparkles size={18} />}<span>{busy ? stage : 'Create my lesson'}</span>{!busy && <ArrowRight size={17} />}
          </button>
          <p className="form-footnote"><LockKeyhole size={13} /> {voiceHint}</p>
        </form>
      </div>
      <div className="panel-bottom"><span className="panel-bottom-icon"><Sparkles size={14} /></span><span>Good ideas deserve<br /><strong>great explanations.</strong></span><span className="smiley">☺</span></div>
    </aside>

    <main className="workspace">
      <header className="workspace-nav"><div className="breadcrumbs"><span>Your workspace</span><span className="crumb-slash">/</span><strong>Lesson studio</strong></div>
        <div className="nav-actions"><button className={`connection-pill ${statusReady ? 'ready' : ''}`} onClick={() => setHelp(true)}><i />{statusText}</button><button className="help-button" aria-label="Open setup help" onClick={() => setHelp(true)}><CircleHelp size={19} /></button></div>
      </header>
      <div className="workspace-inner">
        <div className="workspace-heading"><div><span className="eyebrow workspace-eyebrow"><span className="tiny-star">✦</span> YOUR LESSON STUDIO</span><h2>Let’s make it <em>click.</em></h2><p>Small scenes. Big “aha!” moments.</p></div>
          {exportJob?.videoUrl ? <a className="export-button ready-export" href={exportJob.videoUrl} download><ArrowDownToLine size={17} /> Download MP4 <ArrowRight size={15} /></a> :
            <button className="export-button" disabled={!lesson || exportJob?.working} onClick={exportVideo}>{exportJob?.working ? <LoaderCircle className="spin" size={17} /> : <ArrowDownToLine size={17} />} {exportJob?.working ? `Rendering ${Math.round((exportJob.progress || 0) * 100)}%` : 'Export lesson'} {!exportJob?.working && <ArrowRight size={15} />}</button>}
        </div>
        {message && <div className={`notice ${lesson?.notice ? 'notice-warning' : ''}`} role="status"><span className="notice-dot" /> <span>{message}</span>{exportJob?.srtUrl && <a href={exportJob.srtUrl} download>Download SRT</a>}<button onClick={() => setMessage('')} aria-label="Dismiss message"><X size={15} /></button></div>}
        <section className="preview-section" aria-label="Lesson preview">
          <div className="section-heading"><div className="section-title"><span className="section-title-icon"><Play size={13} fill="currentColor" /></span><strong>Lesson preview</strong>{lesson?.source === 'sample' && <span className="sample-tag">SAMPLE LESSON</span>}</div>
            <div className="preview-meta"><span className="meta-spark">✳</span> {lesson ? `${lesson.scenes.length} scenes` : 'Getting things ready'}
              {lesson && <><span className="meta-divider" /><label className="preview-language" title="Change the language of this lesson">
                {revoicing ? <LoaderCircle className="spin" size={13} /> : <Volume2 size={13} />}
                <select aria-label="Change lesson language" value={lesson.language} onChange={revoice} disabled={revoicing || busy}>
                  <option value="en">English</option><option value="hi">Hindi</option><option value="ta">Tamil</option>
                </select><ChevronDown size={12} />
              </label></>}
            </div>
          </div>
          {current ? <>
            <LessonStage lesson={lesson} scene={current} index={player.index} playing={player.playing} time={player.time} />
            <div className="player-controls">
              <audio ref={player.audioRef} onTimeUpdate={player.onTimeUpdate} onEnded={player.onEnded} onError={() => {}} preload="metadata" />
              <button className="play-button" aria-label={player.playing ? 'Pause lesson' : 'Play lesson'} onClick={player.toggle}>{player.playing ? <Pause size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" />}</button>
              <button className="control-icon skip-back" aria-label="Previous scene" onClick={() => player.goTo(player.index - 1)}><SkipBack size={17} /></button>
              <button className="control-icon" aria-label="Next scene" onClick={() => player.goTo(player.index + 1)}><SkipForward size={17} /></button>
              <span className="time-current">{timeLabel(player.elapsed)}</span>
              <input className="progress-slider" type="range" aria-label="Lesson progress" min="0" max={player.total || 1} step="0.05" value={Math.min(player.elapsed, player.total || 0)} onChange={(e) => player.seek(e.target.value)} style={{ '--progress': `${player.total ? (player.elapsed / player.total) * 100 : 0}%` }} />
              <span className="time-total">{timeLabel(Math.ceil(player.total))}</span>
              <span className="control-divider" /><button className="control-icon replay-control" aria-label="Replay lesson" onClick={player.replay}><RotateCcw size={16} /></button><Volume2 className="volume-icon" size={17} />
            </div>
          </> : <div className="stage-loading"><LoaderCircle className="spin" size={24} /><span>{sampleLoading ? 'Getting your sample ready…' : 'Connect the backend to preview your lesson.'}</span></div>}
          <div className="preview-footnote"><span><span className="pulse-dot" /> {revoicing ? revoiceStage : lesson?.source === 'sample' ? 'A little sample to get you started' : 'Your lesson is ready to play'}</span><span>Captions & narration included <Captions size={14} /></span></div>
        </section>
        {lesson && <section className="storyboard" aria-label="Lesson scenes"><div className="storyboard-heading"><div><span className="eyebrow">THE STORYBOARD</span><h3>One idea at a time<span>.</span></h3></div><span className="scene-total">{lesson.scenes.length} scenes <span>·</span> {timeLabel(Math.ceil(player.total))} total</span></div>
          <div className="scene-grid">{lesson.scenes.map((scene, index) => <button key={`${index}-${scene.heading}`} className={`scene-card ${player.index === index ? 'active' : ''}`} onClick={() => player.goTo(index)} aria-label={`Go to scene ${index + 1}: ${scene.heading}`} aria-pressed={player.index === index}>
            <div className={`scene-thumbnail thumb-${scene.type}`}><MiniScene type={scene.type} />{player.index === index && <span className="thumbnail-play"><Play size={8} fill="currentColor" /></span>}</div>
            <div className="scene-card-copy"><div><span>SCENE {String(index + 1).padStart(2, '0')}</span><span>{timeLabel(Math.ceil(scene.audio_duration))}</span></div><strong>{scene.heading}</strong></div>
          </button>)}</div>
        </section>}
        <div className="workspace-footer"><span><BluMark small /> Made for the moment it makes sense.</span><span>LEARN A LITTLE, EVERY DAY <Sparkles size={13} /></span></div>
      </div>
    </main>
    {help && <HelpModal onClose={() => setHelp(false)} />}
  </div>;
}

export default App;
