"""Text-to-speech generation (edge-tts) with a disk cache.

edge-tts is imported lazily — only when a sound is actually generated — so it
never slows down startup.  GEN_OK just checks that the package is installed
(cheap), without importing it.  Playback happens in the browser; this module
only produces and caches mp3 files.
"""
import importlib.util
import os
import threading

from .paths import AUDIO_DIR

# Availability without the import cost: find_spec locates edge-tts in ~5 ms;
# actually importing it costs ~400 ms, which we defer until first use.
GEN_OK = importlib.util.find_spec("edge_tts") is not None


def generate(text, voice):
    """Generate TTS and return mp3 bytes. Call from a worker thread."""
    import asyncio

    import edge_tts
    if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async def _gen():
        communicate = edge_tts.Communicate(text, voice)
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
    if p:
        return p
    if not GEN_OK:
        return None
    data = generate(word, voice)
    if not data:
        return None
    AUDIO_DIR.mkdir(exist_ok=True)
    # Unique temp name per call: two threads generating the same word must not
    # write to (and rename from) the same temp file, which would corrupt it.
    tmp = dest.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
    try:
        tmp.write_bytes(data)
        tmp.replace(dest)
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass
    return dest if dest.exists() else None


def prune(valid_words):
    """Delete cached audio for words that are no longer in the verb lists."""
    valid = {_safe(w) for w in valid_words}
    try:
        for f in AUDIO_DIR.glob("*.mp3"):
            word = f.stem.split("__", 1)[-1]
            if word not in valid:
                try:
                    f.unlink()
                except OSError:
                    pass
        for f in AUDIO_DIR.glob("*.tmp"):   # sweep temp files left by a crash
            try:
                f.unlink()
            except OSError:
                pass
    except Exception:
        pass
