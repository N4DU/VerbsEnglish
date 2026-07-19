"""Text-to-speech generation (edge-tts) with a disk cache.

Playback happens in the browser, so this module only generates and caches
mp3 files.  prune() removes audio of words that no longer exist.
"""
import os, threading
from pathlib import Path

try:
    import edge_tts as _edge_tts
    import asyncio as _asyncio
    if hasattr(_asyncio, "WindowsSelectorEventLoopPolicy"):
        _asyncio.set_event_loop_policy(_asyncio.WindowsSelectorEventLoopPolicy())
    GEN_OK = True
except Exception:
    GEN_OK = False

AUDIO_DIR = Path(__file__).with_name("audio_cache")


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
