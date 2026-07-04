"""Text-to-speech: generation (edge-tts) and playback (pygame)."""
import time

try:
    import edge_tts as _edge_tts
    import pygame as _pygame
    import os as _os, tempfile as _tempfile
    _pygame.mixer.init()
    TTS_OK = True
except Exception:
    TTS_OK = False


def generate(text, voice):
    """Generate TTS and return mp3 bytes. Call from a worker thread."""
    import asyncio
    if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    async def _gen():
        communicate = _edge_tts.Communicate(text, voice)
        data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                data += chunk["data"]
        return data
    return asyncio.run(_gen())


def play(data):
    """Play mp3 bytes via a temp file. Call from a worker thread."""
    fname = None
    try:
        with _tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(data); fname = f.name
        _pygame.mixer.music.load(fname)
        _pygame.mixer.music.play()
        while _pygame.mixer.music.get_busy(): time.sleep(0.04)
        # release the file handle so unlink works on Windows too
        if hasattr(_pygame.mixer.music, "unload"):
            _pygame.mixer.music.unload()
    except Exception:
        pass
    finally:
        if fname:
            try: _os.unlink(fname)
            except Exception: pass


def shutdown():
    if TTS_OK:
        try: _pygame.mixer.quit()
        except Exception: pass
