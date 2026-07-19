"""Text-to-speech: generation (edge-tts), disk cache and playback (pygame).

Playback safety: SDL / pygame.mixer.music is NOT thread-safe — calling
load/play/unload from several threads at once segfaults the process.
All mixer calls therefore happen in ONE dedicated worker thread; the rest
of the app just enqueues the file to play (newest request wins).

Audio cache: generated words are stored as mp3 files in audio_cache/
(one per word+voice), so replays and future sessions are instant.
prune() deletes files for words that no longer exist in the verb lists.
"""
import os, queue, threading
from pathlib import Path

# GEN_OK: can we generate speech (edge-tts)?  Needed by desktop and web.
# TTS_OK: can we also PLAY it locally (pygame)?  Only the desktop app needs
# this — the web interface plays audio in the browser.
try:
    import edge_tts as _edge_tts
    import asyncio as _asyncio
    if hasattr(_asyncio, "WindowsSelectorEventLoopPolicy"):
        _asyncio.set_event_loop_policy(_asyncio.WindowsSelectorEventLoopPolicy())
    GEN_OK = True
except Exception:
    GEN_OK = False
try:
    import pygame as _pygame
    _pygame.mixer.init()
    TTS_OK = GEN_OK
except Exception:
    TTS_OK = False

AUDIO_DIR = Path(__file__).with_name("audio_cache")

# ── Generation + disk cache ───────────────────────────────────────────────────
def generate(text, voice):
    """Generate TTS and return mp3 bytes. Call from a worker thread."""
    import asyncio
    async def _gen():
        communicate = _edge_tts.Communicate(text, voice)
        data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                data += chunk["data"]
        return data
    return asyncio.run(_gen())

def _safe(word):
    return "".join(ch if (ch.isalnum() or ch == "-") else "_" for ch in word.lower())

def cache_path(word, voice):
    return AUDIO_DIR / f"{voice}__{_safe(word)}.mp3"

def get_cached(word, voice):
    """Path of the cached mp3, or None if not generated yet."""
    p = cache_path(word, voice)
    return p if p.exists() and p.stat().st_size > 0 else None

def ensure(word, voice):
    """Return the cached mp3 path, generating it first if needed."""
    dest = cache_path(word, voice)
    p = get_cached(word, voice)
    if p: return p
    if not GEN_OK: return None
    data = generate(word, voice)
    if not data: return None
    AUDIO_DIR.mkdir(exist_ok=True)
    # Unique temp name per call: two threads generating the same word must not
    # write to (and rename from) the same temp file, which would corrupt it.
    tmp = dest.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
    try:
        tmp.write_bytes(data)
        tmp.replace(dest)
    finally:
        try: tmp.unlink()
        except OSError: pass
    return dest if dest.exists() else None

def prune(valid_words):
    """Delete cached audio for words that are no longer in the verb lists."""
    valid = {_safe(w) for w in valid_words}
    try:
        for f in AUDIO_DIR.glob("*.mp3"):
            word = f.stem.split("__", 1)[-1]
            if word not in valid:
                try: f.unlink()
                except Exception: pass
        for f in AUDIO_DIR.glob("*.tmp"):   # sweep temp files left by a crash
            try: f.unlink()
            except Exception: pass
    except Exception: pass

# ── Playback (single worker thread owns the mixer) ────────────────────────────
_q = queue.Queue()
_worker_thread = None
_lock = threading.Lock()

def _worker():
    while True:
        path = _q.get()
        if path is None: return
        # drain: if more requests queued up, keep only the newest
        while True:
            try: nxt = _q.get_nowait()
            except queue.Empty: break
            if nxt is None: return
            path = nxt
        try:
            _pygame.mixer.music.stop()
            if hasattr(_pygame.mixer.music, "unload"):
                _pygame.mixer.music.unload()
            _pygame.mixer.music.load(str(path))
            _pygame.mixer.music.play()
        except Exception:
            pass

def play_path(path):
    """Queue an mp3 file for playback (non-blocking, newest wins)."""
    global _worker_thread
    if not TTS_OK or not path: return
    with _lock:
        if _worker_thread is None:
            _worker_thread = threading.Thread(target=_worker, daemon=True)
            _worker_thread.start()
    _q.put(path)

def shutdown():
    if not TTS_OK: return
    try:
        if _worker_thread is not None:
            _q.put(None)
            _worker_thread.join(timeout=1.0)   # let it finish before quitting SDL
        _pygame.mixer.quit()
    except Exception: pass
