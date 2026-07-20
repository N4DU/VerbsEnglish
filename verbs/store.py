"""Data layer: progress, word layout, settings and answer rules.

All persistence and every word-list mutation live here, so the server stays
a thin HTTP wrapper over these methods.
"""
import json, os, random

from .data import ALT_FORMS, SPANISH_FORMS, BLOCK, CATS, VOICES
from .paths import PROG_F, CONF_F


def _atomic_write(path, text):
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(text, "utf-8")
    tmp.replace(path)


class Store:
    def __init__(self):
        self.prog = self._load_prog()

    # ── persistence ───────────────────────────────────────────────────────────
    def _load_prog(self):
        d = {}
        try:
            if PROG_F.exists():
                raw = json.loads(PROG_F.read_text("utf-8"))
                if isinstance(raw, dict): d = raw
        except Exception: pass
        legacy = d.pop("settings", None)
        if isinstance(legacy, dict) and legacy.get("voice") and "voice" not in d:
            d["voice"] = legacy["voice"]
        def _int(x):
            try: return max(0, int(x))
            except (TypeError, ValueError): return 0
        for cat in CATS:
            p = d.get(cat)
            if not isinstance(p, dict): p = {"completed": 0}
            p["completed"] = _int(p.get("completed", 0))
            d[cat] = p
        d.setdefault("voice", "en-US-AriaNeural")
        d.setdefault("theme", "light")
        d.setdefault("mode", "read")
        d.setdefault("listen_hint", True)
        return d

    def save(self):
        try:
            _atomic_write(PROG_F, json.dumps(self.prog, indent=2, ensure_ascii=False))
        except Exception: pass

    # ── settings ──────────────────────────────────────────────────────────────
    def voice(self):
        v = self.prog.get("voice", "en-US-AriaNeural")
        return v if any(v == k for k, _ in VOICES) else VOICES[0][0]

    def load_key(self):
        env = os.environ.get("GEMINI_API_KEY", "").strip()
        if env: return env
        try:
            d = json.loads(CONF_F.read_text("utf-8"))
            k = str(d.get("gemini_api_key", "")).strip()
            placeholders = {"PONER_LA_KEY_AQUI", "TU_KEY_AQUI", "YOUR_API_KEY_HERE"}
            if k and k not in placeholders: return k
        except Exception: pass
        return None

    def save_key(self, k):
        try:
            _atomic_write(CONF_F, json.dumps({"gemini_api_key": (k or "").strip()},
                                             indent=2))
        except Exception: pass

    # ── word data: built-ins − deleted + custom (same rules as the app) ───────
    def cat_prog(self, cat):
        return self.prog[cat]

    def custom(self, cat):
        p = self.cat_prog(cat)
        c = p.get("custom")
        if not isinstance(c, list): c = []
        c = [v for v in c if isinstance(v, list) and len(v) >= 3
             and all(isinstance(s, str) and s.strip() for s in v[:3])]
        p["custom"] = c
        return c

    def custom_es(self, cat):
        p = self.cat_prog(cat)
        m = p.get("custom_es")
        if not isinstance(m, dict): m = {}
        names = {v[1] for v in self.custom(cat)}
        m = {k: [str(v[0]), str(v[1] if len(v) > 1 else "")]
             for k, v in m.items()
             if k in names and isinstance(v, list) and v}
        p["custom_es"] = m
        return m

    def deleted(self, cat):
        builtin = {v[1] for v in CATS[cat]["verbs"]}
        p = self.cat_prog(cat)
        d = {n for n in (p.get("deleted") or []) if n in builtin}
        p["deleted"] = sorted(d)
        return d

    def vdict(self, cat):
        dele = self.deleted(cat)
        has_part = CATS[cat]["has_part"]
        d = {v[1]: v for v in CATS[cat]["verbs"] if v[1] not in dele}
        for v in self.custom(cat):
            row = list(v[:4] if has_part else v[:3])
            if has_part and len(row) == 3: row.append(row[2])
            d[row[1]] = row
        return d

    def layout(self, cat):
        names = list(self.vdict(cat))
        known = set(names)
        p = self.cat_prog(cat)
        # keep empty blocks — they're legitimate in the editor (you can add
        # words to them). the practice flow filters empties out on its own.
        lay, seen = [], set()
        for blk in (p.get("layout") or []):
            if not isinstance(blk, list): continue
            b = [n for n in blk if n in known and n not in seen]
            seen.update(b)
            lay.append(b)
        missing = [n for n in names if n not in seen]
        if not any(lay):
            lay = [missing[i:i+BLOCK] for i in range(0, len(missing), BLOCK)] or [[]]
        else:
            for n in missing:
                if lay and len(lay[-1]) < BLOCK: lay[-1].append(n)
                else: lay.append([n])
        p["layout"] = lay
        return lay

    def disabled(self, cat):
        p = self.cat_prog(cat)
        known = set(self.vdict(cat))
        ds = {n for n in (p.get("disabled") or []) if n in known}
        p["disabled"] = sorted(ds)
        return ds

    def enabled_blocks(self, cat):
        vd, ds = self.vdict(cat), self.disabled(cat)
        return [[vd[n] for n in blk if n not in ds and n in vd]
                for blk in self.layout(cat)]

    def enabled_count(self, cat):
        return sum(len(b) for b in self.enabled_blocks(cat))

    def comp(self, cat):
        return max(0, int(self.cat_prog(cat).get("completed", 0)))

    def set_comp(self, cat, n):
        total = self.enabled_count(cat)
        self.cat_prog(cat)["completed"] = max(0, min(int(n), total))
        self.save()

    # ── answers and meanings (same rules as the app) ──────────────────────────
    @staticmethod
    def answer_parts(raw):
        parts = [p.strip() for p in raw.replace("/", "-").split("-") if p.strip()]
        return parts or [raw.strip()]

    def pick_answer(self, raw):
        return random.choice(self.answer_parts(raw))

    def meaning(self, cat, verb, col):
        """Spanish meaning of a form: eat->comer, ate->comí, eaten->comido."""
        if col == "base": return verb[0]
        forms = SPANISH_FORMS.get(verb[1]) or self.custom_es(cat).get(verb[1])
        if not forms: return verb[0]
        val = forms[0] if col == "past" else forms[1]
        return val or verb[0]

    def accepted(self, verb, col, ans, has_sentence, mode):
        """Every answer the field should accept, lowercase."""
        idx = {"base": 1, "past": 2, "part": 3}[col]
        raw = verb[idx].strip().lower()
        ans = (ans or "").strip().lower() or self.answer_parts(raw)[0]
        ok = {ans, *ALT_FORMS.get(ans, ())}
        if not has_sentence and mode != "listen":
            for p in self.answer_parts(raw):
                ok.add(p); ok.update(ALT_FORMS.get(p, ()))
        return sorted(ok)

    # ── word-list editor (all mutations live here, shared by any UI) ──────────
    def editor_state(self, cat):
        """Everything the editor needs to render the word list."""
        vd, ds = self.vdict(cat), self.disabled(cat)
        customs = {v[1] for v in self.custom(cat)}
        has_part = CATS[cat]["has_part"]
        blocks = []
        for blk in self.layout(cat):
            rows = []
            for name in blk:
                v = vd.get(name)
                if not v: continue
                rows.append({"name": name, "es": v[0],
                             "forms": list(v[1:4] if has_part else v[1:3]),
                             "on": name not in ds, "custom": name in customs})
            blocks.append(rows)
        return {"cat": cat, "title": CATS[cat]["title"], "has_part": has_part,
                "blocks": blocks, "deleted": len(self.deleted(cat)),
                "total": len(vd), "on": self.enabled_count(cat)}

    def _blocks_names(self, cat):
        vd = set(self.vdict(cat))
        return [[n for n in blk if n in vd] for blk in self.layout(cat)]

    def _save_layout(self, cat, blocks):
        # keep empty blocks (the editor may hold empties on purpose)
        self.cat_prog(cat)["layout"] = [list(b) for b in blocks] or [[]]
        self.save()

    def _set_disabled(self, cat, names):
        self.cat_prog(cat)["disabled"] = sorted(names)
        self.save()

    def toggle_word(self, cat, name):
        ds = self.disabled(cat)
        ds.discard(name) if name in ds else ds.add(name)
        self._set_disabled(cat, ds)

    def toggle_block(self, cat, i):
        blocks = self._blocks_names(cat)
        if not (0 <= i < len(blocks)): return
        blk, ds = blocks[i], self.disabled(cat)
        if any(n in ds for n in blk): ds.difference_update(blk)
        else: ds.update(blk)
        self._set_disabled(cat, ds)

    def move_word(self, cat, name, d):
        """Slide a word one step (crossing block borders); returns new layout."""
        blocks = self._blocks_names(cat)
        bi = pos = None
        for i, blk in enumerate(blocks):
            if name in blk: bi, pos = i, blk.index(name); break
        if bi is None: return
        blk = blocks[bi]
        if d > 0:
            if pos < len(blk) - 1: blk[pos], blk[pos+1] = blk[pos+1], blk[pos]
            elif bi < len(blocks) - 1: blk.pop(pos); blocks[bi+1].insert(0, name)
            else: return
        else:
            if pos > 0: blk[pos-1], blk[pos] = blk[pos], blk[pos-1]
            elif bi > 0: blk.pop(pos); blocks[bi-1].append(name)
            else: return
        self._save_layout(cat, blocks)

    def add_block(self, cat):
        blocks = self._blocks_names(cat); blocks.append([])
        self._save_layout(cat, blocks)

    def delete_block(self, cat, i, keep_words):
        blocks = self._blocks_names(cat)
        if not (0 <= i < len(blocks)) or len(blocks) <= 1: return
        blk = blocks.pop(i)
        if keep_words:
            if i > 0: blocks[i-1].extend(blk)
            elif blocks: blocks[0][0:0] = blk
            else: blocks = [blk]
        else:
            p = self.cat_prog(cat); cust = {v[1] for v in self.custom(cat)}
            for name in blk:
                if name in cust:
                    p["custom"] = [v for v in self.custom(cat) if v[1] != name]
                    es = p.get("custom_es")
                    if isinstance(es, dict): es.pop(name, None)
                else:
                    d = self.deleted(cat); d.add(name); p["deleted"] = sorted(d)
                ds = self.disabled(cat); ds.discard(name); p["disabled"] = sorted(ds)
        self._save_layout(cat, blocks)

    def delete_word(self, cat, name):
        p = self.cat_prog(cat); cust = {v[1] for v in self.custom(cat)}
        if name in cust:
            p["custom"] = [v for v in self.custom(cat) if v[1] != name]
            es = p.get("custom_es")
            if isinstance(es, dict): es.pop(name, None)
        else:
            d = self.deleted(cat); d.add(name); p["deleted"] = sorted(d)
        ds = self.disabled(cat); ds.discard(name); p["disabled"] = sorted(ds)
        blocks = [[n for n in blk if n != name] for blk in self._blocks_names(cat)]
        self._save_layout(cat, blocks)

    def restore_deleted(self, cat):
        self.cat_prog(cat)["deleted"] = []
        self.save()

    def create_word(self, cat, row, block_i, es_past="", es_part=""):
        """row = [es, base, past] (+part). Returns the base name, or None on error."""
        row = [s.strip() for s in row]
        base = row[1].lower()
        if not base or base in self.vdict(cat) or any("|" in s for s in row):
            return None
        row[1] = base; row[2] = row[2].lower()
        if len(row) > 3: row[3] = row[3].lower()
        # snapshot the layout BEFORE the word is known, so reconciliation
        # doesn't also auto-insert it (which would duplicate the row)
        blocks = self._blocks_names(cat) or [[]]
        p = self.cat_prog(cat)
        c = self.custom(cat); c.append(row); p["custom"] = c
        if es_past.strip() or es_part.strip():
            m = p.get("custom_es")
            if not isinstance(m, dict): m = {}
            m[base] = [es_past.strip(), es_part.strip()]; p["custom_es"] = m
        bi = max(0, min(block_i, len(blocks) - 1))
        blocks[bi].append(base)
        self._save_layout(cat, blocks)
        return base
