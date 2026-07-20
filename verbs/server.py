"""Local web server for Verb Practice.

Standard library only — nothing leaves your computer except the optional
Gemini / TTS requests.  Your computer is the server; the browser is the UI.
The server is a thin HTTP wrapper over verbs.store (data) plus verbs.phrases
(reading sentences) and verbs.audio (listening voice).
"""
import argparse
import json
import random
import re
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

from . import audio
from .data import CATS, THEMES, VOICES
from .paths import WEB_DIR
from .phrases import Cache, GEMINI_OK
from .store import Store

# Static assets we serve, by file extension → content type.
CTYPES = {".html": "text/html; charset=utf-8",
          ".js":   "text/javascript; charset=utf-8",
          ".css":  "text/css; charset=utf-8",
          ".svg":  "image/svg+xml", ".ico": "image/x-icon"}
# Only bare, lowercase words become audio (path-safety for /api/audio/<word>).
WORD_RE = re.compile(r"^[a-z][a-z' -]{0,30}$")

store = Store()
cache = Cache()
_fetch_lock = threading.Lock()


def fetch_phrases_sync(needed, key, timeout=45):
    if not needed or not key or not GEMINI_OK:
        return False
    with _fetch_lock:
        done = threading.Event(); ok = []
        cache.fetch(needed, key, lambda r: (ok.append(bool(r)), done.set()))
        done.wait(timeout)
    return bool(ok and ok[0])


def build_block(cat, mode, forms, words):
    """Build the payload for one block: each word with its per-form fields."""
    idx = {"base": 1, "past": 2, "part": 3}
    if mode == "read":
        needed = [(v[1], c, store.pick_answer(v[idx[c]]))
                  for v in words for c in forms if not cache.has_any(v[1], c)]
        fetch_phrases_sync(list(dict.fromkeys(needed)), store.load_key())
    out = []
    for v in words:
        cols = random.sample(forms, len(forms)) if mode == "listen" else list(forms)
        fields = []
        for c in cols:
            ans = store.pick_answer(v[idx[c]])
            sentence = None
            if mode == "read":
                sent = cache.get(v[1], c, ans)
                if not sent:
                    fb_ans, fb_sent = cache.get_any(v[1], c)
                    if fb_ans:
                        ans, sent = fb_ans, fb_sent
                sentence = random.choice(sent) if sent else None
            fields.append({"col": c, "answer": ans, "sentence": sentence,
                           "accept": store.accepted(v, c, ans, bool(sentence), mode),
                           "meaning": store.meaning(cat, v, c)})
        out.append({"es": v[0], "base": v[1], "fields": fields})
    return out


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    # ── low-level replies ─────────────────────────────────────────────────────
    def _bytes(self, data, ctype, code=200, cache_control=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        if cache_control:
            self.send_header("Cache-Control", cache_control)
        self.end_headers()
        self.wfile.write(data)

    def _json(self, obj, code=200):
        self._bytes(json.dumps(obj).encode("utf-8"),
                    "application/json; charset=utf-8", code)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return {}

    # ── GET ───────────────────────────────────────────────────────────────────
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/state":
            self._json(self._state())
        elif path.startswith("/api/editor/"):
            cat = path[len("/api/editor/"):]
            self._json(store.editor_state(cat)) if cat in CATS else self.send_error(404)
        elif path.startswith("/api/audio/"):
            self._audio(unquote(path[len("/api/audio/"):]).strip().lower())
        elif path.startswith("/api/"):
            self.send_error(404)
        else:
            self._static(path)

    def _static(self, path):
        rel = "index.html" if path == "/" else path.lstrip("/")
        f = (WEB_DIR / rel).resolve()
        if (f.suffix not in CTYPES or not f.is_file()
                or WEB_DIR.resolve() not in f.parents):
            self.send_error(404); return
        self._bytes(f.read_bytes(), CTYPES[f.suffix])

    def _audio(self, word):
        if not WORD_RE.match(word) or not audio.GEN_OK:
            self.send_error(404); return
        try:
            p = audio.ensure(word, store.voice())
        except Exception:
            p = None
        if not p:
            self.send_error(502); return
        from pathlib import Path
        self._bytes(Path(p).read_bytes(), "audio/mpeg", cache_control="no-store")

    def _state(self):
        cats = {}
        for cat, info in CATS.items():
            blocks = [len(b) for b in store.enabled_blocks(cat) if b]
            total = store.enabled_count(cat)
            cats[cat] = {"title": info["title"], "has_part": info["has_part"],
                         "words_total": len(store.vdict(cat)), "words_on": total,
                         "blocks": blocks, "completed": min(store.comp(cat), total)}
        return {"cats": cats, "voice": store.voice(), "voices": VOICES,
                "theme": store.prog.get("theme", "light"), "themes": list(THEMES),
                "mode": store.prog.get("mode", "read"),
                "listen_hint": bool(store.prog.get("listen_hint", True)),
                "has_key": bool(store.load_key()),
                "audio_ok": audio.GEN_OK, "gemini_ok": GEMINI_OK}

    # ── POST ──────────────────────────────────────────────────────────────────
    def do_POST(self):
        path = self.path.split("?")[0]
        b = self._body()
        route = {"/api/settings": self._settings, "/api/session": self._session,
                 "/api/block": self._block, "/api/progress": self._progress,
                 "/api/editor": self._editor}.get(path)
        route(b) if route else self.send_error(404)

    def _settings(self, b):
        if b.get("voice") in {k for k, _ in VOICES}:
            store.prog["voice"] = b["voice"]
        if b.get("theme") in THEMES:
            store.prog["theme"] = b["theme"]
        if b.get("mode") in ("read", "listen"):
            store.prog["mode"] = b["mode"]
        if isinstance(b.get("listen_hint"), bool):
            store.prog["listen_hint"] = b["listen_hint"]
        if "gemini_key" in b and isinstance(b["gemini_key"], str):
            store.save_key(b["gemini_key"])
        store.save()
        self._json(self._state())

    def _progress(self, b):
        cat = b.get("cat")
        if cat not in CATS:
            self._json({"ok": False}, 400); return
        store.set_comp(cat, b.get("completed", 0))
        self._json({"ok": True, "completed": store.comp(cat)})

    def _forms(self, cat, b):
        valid = ["base", "past"] + (["part"] if CATS[cat]["has_part"] else [])
        forms = [f for f in (b.get("forms") or valid) if f in valid]
        return forms or valid

    def _session(self, b):
        cat = b.get("cat")
        if cat not in CATS:
            self._json({"error": "bad cat"}, 400); return
        sizes = [len(x) for x in store.enabled_blocks(cat) if x]
        total = sum(sizes)
        comp = min(store.comp(cat), total)
        start = acc = 0
        for i, s in enumerate(sizes):
            if acc <= comp:
                start = i
            acc += s
        if comp >= total:
            start = 0
        mode = b.get("mode") if b.get("mode") in ("read", "listen") else store.prog.get("mode", "read")
        if b.get("start") == "new":
            store.set_comp(cat, 0); start = 0
        elif isinstance(b.get("start"), int):
            start = max(0, min(b["start"], len(sizes) - 1)) if sizes else 0
        self._json({"sizes": sizes, "start": start, "total": total,
                    "completed": store.comp(cat), "mode": mode,
                    "forms": self._forms(cat, b)})

    def _block(self, b):
        cat = b.get("cat")
        if cat not in CATS:
            self._json({"error": "bad cat"}, 400); return
        blocks = [x for x in store.enabled_blocks(cat) if x]
        i = b.get("block")
        if not isinstance(i, int) or not (0 <= i < len(blocks)):
            self._json({"error": "bad block"}, 400); return
        mode = b.get("mode") if b.get("mode") in ("read", "listen") else "read"
        forms = self._forms(cat, b)
        words = random.sample(blocks[i], len(blocks[i]))
        self._json({"block": i, "words": build_block(cat, mode, forms, words)})

    def _editor(self, b):
        cat = b.get("cat"); act = b.get("action")
        if cat not in CATS:
            self._json({"error": "bad cat"}, 400); return
        name = b.get("name"); i = b.get("block")
        if   act == "toggle_word":  store.toggle_word(cat, name)
        elif act == "toggle_block": store.toggle_block(cat, i)
        elif act == "move":         store.move_word(cat, name, 1 if b.get("dir") == "down" else -1)
        elif act == "add_block":    store.add_block(cat)
        elif act == "delete_block": store.delete_block(cat, i, bool(b.get("keep_words")))
        elif act == "delete_word":  store.delete_word(cat, name)
        elif act == "restore":      store.restore_deleted(cat)
        elif act == "create":
            row = [b.get("es", ""), b.get("base", ""), b.get("past", "")]
            if CATS[cat]["has_part"]:
                row.append(b.get("part", ""))
            new = store.create_word(cat, row, int(b.get("block", 0) or 0),
                                    b.get("es_past", ""), b.get("es_part", ""))
            if not new:
                self._json({"error": "invalid", **store.editor_state(cat)}, 200); return
        else:
            self._json({"error": "bad action"}, 400); return
        store.set_comp(cat, store.comp(cat))   # clamp if the list shrank
        self._json(store.editor_state(cat))


def _prune_stale_audio():
    """Drop cached mp3s for words that no longer exist (custom edits/deletions)."""
    if not audio.GEN_OK:
        return
    valid = set()
    for cat in CATS:
        for v in store.vdict(cat).values():
            for raw in v[1:]:
                valid.update(store.answer_parts(raw))
    threading.Thread(target=audio.prune, args=(valid,), daemon=True).start()


def run(port=8321, open_browser=True):
    """Start the server (used by main.py)."""
    _prune_stale_audio()
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError:
        srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    url = f"http://127.0.0.1:{srv.server_address[1]}"
    print(f"\n  Verb Practice is running.\n  Open:  {url}\n  (Press Ctrl+C to stop)\n")
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped. ¡Hasta luego!")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Verb Practice — local web app")
    ap.add_argument("--port", type=int, default=8321)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args(argv)
    run(port=args.port, open_browser=not args.no_browser)
