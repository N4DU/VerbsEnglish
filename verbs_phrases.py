"""Fill-in-the-blank sentence cache, backed by Gemini AI.

Cache key: "verb|col|answer"  e.g. "go|past|went", "be|past|was"
Value: list of sentence strings with a ___ placeholder.
"""
import json, threading, time

from verbs_data import PHRA_F

try:
    from google import genai as _genai
    GEMINI_OK = True
except ImportError:
    GEMINI_OK = False


class Cache:
    def __init__(self):
        self._lock = threading.Lock(); self._d = {}
        try:
            if PHRA_F.exists():
                d = json.loads(PHRA_F.read_text("utf-8"))
                if isinstance(d, dict): self._d = d
        except Exception: pass

    def _save(self):
        try: PHRA_F.write_text(json.dumps(self._d, indent=2, ensure_ascii=False), "utf-8")
        except Exception: pass

    @staticmethod
    def _valid(v):
        if not isinstance(v, list): return None
        v = [p for p in v if isinstance(p, str) and "___" in p]
        return v or None

    def get(self, verb, col, answer):
        with self._lock: return self._valid(self._d.get(f"{verb}|{col}|{answer}"))

    def has_any(self, verb, col):
        prefix = f"{verb}|{col}|"
        with self._lock:
            return any(k.startswith(prefix) and self._valid(v)
                       for k, v in self._d.items())

    def get_any(self, verb, col):
        """Return (answer, sentences) for any cached answer for this verb+col."""
        prefix = f"{verb}|{col}|"
        with self._lock:
            for k, v in self._d.items():
                if k.startswith(prefix):
                    v = self._valid(v)
                    if v: return k[len(prefix):], v
        return None, None

    def put(self, verb, col, answer, sentences):
        with self._lock:
            self._d[f"{verb}|{col}|{answer}"] = sentences
            self._save()

    def fetch(self, needed, api_key, cb):
        """needed = [(verb_base, col, answer), ...].  Always calls cb exactly once."""
        needed = list(dict.fromkeys(needed))  # dedupe, keep order
        def run():
            try:
                self._fetch(needed, api_key, cb)
            except Exception:
                cb(None)
        threading.Thread(target=run, daemon=True).start()

    def _fetch(self, needed, api_key, cb):
        if not GEMINI_OK or not api_key or not needed:
            cb(None); return
        lines = "\n".join(f"- verb={v}, tense={c}, answer={a}" for v,c,a in needed)
        prompt = (
            "You are an English teacher making fill-in-the-blank exercises for A2-B1 students.\n"
            "For each item write 5 short sentences (under 10 words) using simple everyday vocabulary.\n"
            "Replace the verb in each sentence with ___ (three underscores).\n"
            "The word that fills ___ must be EXACTLY the word given as 'answer'.\n"
            "Build the sentence so that 'answer' fits naturally and grammatically.\n\n"
            "Return ONLY valid JSON, no markdown:\n"
            '{"verb|col|answer": ["sentence1","sentence2","sentence3","sentence4","sentence5"]}\n\n'
            f"Items:\n{lines}"
        )
        client = _genai.Client(api_key=api_key); resp = None
        for att in range(4):
            try:
                resp = client.models.generate_content(
                    model="models/gemini-2.5-flash", contents=prompt)
                break
            except Exception as e:
                if "503" in str(e) or "UNAVAILABLE" in str(e): time.sleep(5*(att+1))
                else: cb(None); return
        if not resp: cb(None); return
        t = resp.text.strip()
        if t.startswith("```"): t = "\n".join(t.splitlines()[1:])
        if "```" in t: t = t[:t.rfind("```")]
        s, e = t.find("{"), t.rfind("}")
        if s < 0 or e <= s: cb(None); return
        data = json.loads(t[s:e+1])
        out = {}
        for key, phrases in data.items():
            parts = key.split("|")
            if len(parts) != 3: continue
            v, c, a = parts
            valid = [p for p in phrases if isinstance(p, str) and "___" in p]
            if len(valid) >= 2:
                self.put(v, c, a, valid)
                out[(v, c, a)] = valid
        cb(out if out else None)
