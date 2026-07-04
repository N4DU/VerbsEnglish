"""Verb Practice — main application (UI and session logic).

Two ways to practice, chosen in the setup screen:
  Reading   — fill the blank in a sentence (Gemini-generated) for each form.
  Listening — hear each form (shuffled order) and type the word; each correct
              word instantly reveals its Spanish meaning, conjugated
              (eat -> comer, ate -> comí, eaten -> comido).

The word list screen supports enabling/disabling words, creating custom
words, deleting words, and picking a word up (→) to carry it with ↑↓ and
drop it (←) anywhere — including into another block.
"""
import tkinter as tk
import tkinter.font as tkfont
import os, random, json, threading

import verbs_audio as audio
from verbs_phrases import Cache, GEMINI_OK
from verbs_data import (
    ALT_FORMS, SPANISH_FORMS, THEMES, PTR, BLOCK, FEED_OK, FEED_BAD,
    BASE_W, BASE_H, AUDIO_ICON, PROG_F, CONF_F, VOICES, COLS, CATS, SPIN,
)


class App:
    def __init__(self):
        w = self.win = tk.Tk()
        w.title("Verb Practice"); w.geometry(f"{BASE_W}x{BASE_H}")
        w.minsize(640, 460)
        w.protocol("WM_DELETE_WINDOW", self._on_close)
        w.bind("<F8>", self._toggle_topmost)

        self.cache  = Cache()
        self.prog   = self._load_prog()
        self.key    = self._load_key()
        self.C      = THEMES.get(self.prog.get("theme","light"), THEMES["light"])
        w.config(bg=self.C["BG"])
        self.FF     = self._pick_family()
        self._audio = {}   # col -> cached mp3 path

        # session state
        self.cat = "regular"; self.cols = ["base","past"]; self.cur_cols = []
        self.cst = {"base":True,"past":True,"part":False}
        self.sblocks = []; self._starts = []
        self.bidx = self.vidx = 0
        self.ok_n = self.bad_n = self.blk_ok = self.blk_bad = self.streak = 0
        self.phrases = {}; self.entries = {}; self.icons = {}; self.fb_id = None
        self.locked = False; self._vt = 0
        # per-screen cursors
        self.mi = self.si = self.sb = self.bi = self.fi = self.sti = self.wi = 0
        self.sr = []; self._pending = None
        self._anim_i = 0; self.screen = "menu"
        self._last_size = (0,0); self._resize_job = None
        # word-list editor state
        self.wd_blocks = []; self.wd_carry = None; self.wd_del_pending = None

        # clean cached audio of words that no longer exist in the verb lists
        if audio.TTS_OK:
            valid = set()
            for cat in CATS:
                for v in self._vdict(cat).values():
                    for raw in v[1:]:
                        valid.update(self._answer_parts(raw))
            threading.Thread(target=audio.prune, args=(valid,), daemon=True).start()

        self._build()
        for key, fn in [("<Up>",self._up),("<Down>",self._dn),("<Left>",self._lt),
                        ("<Right>",self._rt),("<Return>",self._en),
                        ("<space>",self._sp),("<Escape>",self._es),
                        ("<Key-a>",self._ka),("<Key-n>",self._kn),
                        ("<Delete>",self._kdel)]:
            w.bind(key, fn)
        w.bind("<Configure>", self._on_resize)
        self._init_fonts()
        self._show("menu"); self._draw_menu()

    # ── Lifecycle / misc ──────────────────────────────────────────────────────
    def _on_close(self):
        audio.shutdown()
        self.win.destroy()

    def _toggle_topmost(self, _=None):
        try:
            cur = bool(int(self.win.attributes("-topmost")))
        except Exception:
            cur = False
        self.win.attributes("-topmost", not cur)

    def _pick_family(self):
        try: fams = set(tkfont.families())
        except Exception: fams = set()
        for f in ("Segoe UI","SF Pro Text","Helvetica Neue","DejaVu Sans","Arial"):
            if f in fams: return f
        return "TkDefaultFont"

    # ── Answer picking / matching ─────────────────────────────────────────────
    def _answer_parts(self, raw):
        """'was-were' -> ['was','were'].  Handles '/' separators too."""
        parts = [p.strip() for p in raw.replace("/", "-").split("-") if p.strip()]
        return parts or [raw.strip()]

    def _pick_answer(self, raw):
        return random.choice(self._answer_parts(raw))

    def _expected_set(self, col):
        """All accepted answers for this column of the current verb."""
        obj = self.phrases.get(col) or {}
        ans = (obj.get("a") or "").strip().lower()
        idx_map = {"base":1,"past":2,"part":3}
        raw = self._cur_verb()[idx_map[col]].strip().lower()
        if not ans: ans = self._answer_parts(raw)[0]
        ok = {ans, *ALT_FORMS.get(ans, ())}
        if not obj.get("s") and self._mode() != "listen":
            # reading mode without sentence context: any listed form is fine
            for p in self._answer_parts(raw):
                ok.add(p); ok.update(ALT_FORMS.get(p, ()))
        return ok

    def _expected_main(self, col):
        obj = self.phrases.get(col) or {}
        if obj.get("a"): return obj["a"]
        idx_map = {"base":1,"past":2,"part":3}
        return self._cur_verb()[idx_map[col]]

    def _meaning(self, col, verb=None):
        """Spanish meaning of the given form: eat->comer, ate->comí, eaten->comido."""
        verb = verb or self._cur_verb()
        if col == "base": return verb[0]
        forms = SPANISH_FORMS.get(verb[1])
        if not forms: return verb[0]
        return forms[0] if col == "past" else forms[1]

    # ── Progress / config ─────────────────────────────────────────────────────
    def _load_prog(self):
        d = {}
        try:
            if PROG_F.exists():
                raw = json.loads(PROG_F.read_text("utf-8"))
                if isinstance(raw, dict): d = raw
        except Exception: pass
        # migrate legacy {"settings": {"voice": ...}}
        legacy = d.pop("settings", None)
        if isinstance(legacy, dict) and legacy.get("voice") and "voice" not in d:
            d["voice"] = legacy["voice"]
        def _int(x):
            try: return max(0, int(x))
            except (TypeError, ValueError): return 0
        for cat in CATS:
            p = d.get(cat)
            if not isinstance(p, dict): p = {"completed":0}
            p["completed"] = _int(p.get("completed", 0))
            d[cat] = p
        d.setdefault("voice", "en-US-AriaNeural")
        d.setdefault("theme", "light")
        d.setdefault("mode", "read")
        d.setdefault("listen_hint", True)
        return d

    def _save_prog(self):
        # Atomic write: a crash mid-save can't corrupt progress.json
        # (which holds custom words, block layout and progress).
        try:
            data = json.dumps(self.prog, indent=2, ensure_ascii=False)
            tmp = PROG_F.with_suffix(".json.tmp")
            tmp.write_text(data, "utf-8")
            tmp.replace(PROG_F)
        except Exception: pass

    def _cat_prog(self, cat=None):
        return self.prog[cat or self.cat]

    def _comp(self, cat=None):
        return max(0, int(self._cat_prog(cat).get("completed",0)))

    def _set_comp(self, n, cat=None):
        total = sum(len(b) for b in self._enabled_blocks(cat))
        self._cat_prog(cat)["completed"] = max(0, min(int(n), total))
        self._save_prog()

    def _load_key(self):
        # Environment variable wins, so users never have to edit a file.
        env = os.environ.get("GEMINI_API_KEY", "").strip()
        if env: return env
        try:
            d = json.loads(CONF_F.read_text("utf-8"))
            k = str(d.get("gemini_api_key","")).strip()
            placeholders = {"PONER_LA_KEY_AQUI", "TU_KEY_AQUI", "YOUR_API_KEY_HERE"}
            if k and k not in placeholders: return k
        except Exception: pass
        return None

    def _get_voice(self):
        v = self.prog.get("voice", "en-US-AriaNeural")
        return v if any(v == k for k,_ in VOICES) else VOICES[0][0]
    def _set_voice(self, v): self.prog["voice"] = v; self._save_prog()

    def _mode(self):
        m = self.prog.get("mode", "read")
        return m if (m == "read" or audio.TTS_OK) else "read"

    # ── Word data: built-ins − deleted + custom ───────────────────────────────
    def _custom(self, cat=None):
        """User-created verb rows: [es, base, past] or [es, base, past, part]."""
        p = self._cat_prog(cat)
        c = p.get("custom")
        if not isinstance(c, list): c = []
        c = [v for v in c if isinstance(v, list) and len(v) >= 3
             and all(isinstance(s, str) and s.strip() for s in v[:3])]
        p["custom"] = c
        return c

    def _deleted(self, cat=None):
        """Names of built-in verbs the user removed."""
        cat = cat or self.cat
        builtin = {v[1] for v in CATS[cat]["verbs"]}
        p = self._cat_prog(cat)
        d = {n for n in (p.get("deleted") or []) if n in builtin}
        p["deleted"] = sorted(d)
        return d

    def _vdict(self, cat=None):
        cat = cat or self.cat
        dele = self._deleted(cat)
        has_part = CATS[cat]["has_part"]
        d = {v[1]: v for v in CATS[cat]["verbs"] if v[1] not in dele}
        for v in self._custom(cat):
            row = list(v[:4] if has_part else v[:3])
            if has_part and len(row) == 3: row.append(row[2])
            d[row[1]] = row
        return d

    def _layout(self, cat=None):
        """Blocks of verb base-names for a category; reconciled and persisted."""
        cat = cat or self.cat
        names = list(self._vdict(cat))
        known = set(names)
        p = self._cat_prog(cat)
        lay, seen = [], set()
        for blk in (p.get("layout") or []):
            if not isinstance(blk, list): continue
            b = [n for n in blk if n in known and n not in seen]
            seen.update(b)
            if b: lay.append(b)
        missing = [n for n in names if n not in seen]
        if not lay:
            lay = [missing[i:i+BLOCK] for i in range(0, len(missing), BLOCK)]
        else:
            for n in missing:
                if len(lay[-1]) < BLOCK: lay[-1].append(n)
                else: lay.append([n])
        p["layout"] = lay
        return lay

    def _disabled(self, cat=None):
        p = self._cat_prog(cat)
        known = set(self._vdict(cat))
        ds = {n for n in (p.get("disabled") or []) if n in known}
        p["disabled"] = sorted(ds)
        return ds

    def _set_disabled(self, ds, cat=None):
        self._cat_prog(cat)["disabled"] = sorted(ds)
        self._save_prog()

    def _enabled_blocks(self, cat=None):
        """Layout blocks with disabled words removed (verb rows, empties kept)."""
        vd, ds = self._vdict(cat), self._disabled(cat)
        return [[vd[n] for n in blk if n not in ds and n in vd]
                for blk in self._layout(cat)]

    def _enabled_count(self, cat=None):
        return sum(len(b) for b in self._enabled_blocks(cat))

    # ── UI helpers ────────────────────────────────────────────────────────────
    def _build(self):
        C = self.C
        self.fr = {n: tk.Frame(self.win, bg=C["BG"])
                   for n in ["menu","setup","words","load","prac","blk","fin","settings"]}
        self._bld_menu(); self._bld_setup(); self._bld_words(); self._bld_load()
        self._bld_prac(); self._bld_blk(); self._bld_fin(); self._bld_settings()

    def _lbl(self, parent, text, size, fg=None, bold=False, bg=None, **kw):
        C = self.C
        font = (self.FF, size, "bold") if bold else (self.FF, size)
        return tk.Label(parent, text=text, font=font,
                        bg=bg or C["BG"], fg=fg or C["FG2"], **kw)

    def _hint(self, parent, text):
        l = self._lbl(parent, text, 9, self.C["FG3"])
        l.place(relx=.5, rely=.97, anchor="center")
        return l

    def _card(self, parent, **kw):
        C = self.C
        return tk.Frame(parent, bg=C["CARD"], highlightthickness=1,
                        highlightbackground=C["BORDER"], **kw)

    def _card_sel(self, card, on):
        C = self.C
        card.config(highlightbackground=C["ACC"] if on else C["BORDER"],
                    highlightthickness=2 if on else 1,
                    bg=C["SEL"] if on else C["CARD"])
        for ch in card.winfo_children():
            try: ch.config(bg=C["SEL"] if on else C["CARD"])
            except tk.TclError: pass

    def _show(self, name):
        for fr in self.fr.values(): fr.place_forget()
        self.fr[name].place(relwidth=1, relheight=1)
        self.screen = name
        if name == "words":
            for ev in ("<MouseWheel>","<Button-4>","<Button-5>"):
                self.win.bind_all(ev, self._wd_wheel)
        else:
            for ev in ("<MouseWheel>","<Button-4>","<Button-5>"):
                self.win.unbind_all(ev)
        self.win.focus_set()

    # ── Menu screen ───────────────────────────────────────────────────────────
    def _bld_menu(self):
        f = self.fr["menu"]; C = self.C
        self._lbl(f,"ENGLISH PRACTICE",11,C["FG3"]).place(relx=.5,rely=.06,anchor="n")
        self._lbl(f,"What do you want to practice?",20,C["FG"],bold=True)\
            .place(relx=.5,rely=.13,anchor="n")

        self.menu_cards = []
        specs = [("Regular verbs","regular"), ("Irregular verbs","irregular"),
                 ("Settings", None)]
        for i,(title,cat) in enumerate(specs):
            card = self._card(f, cursor="hand2")
            if i < 2:
                card.place(relx=.18+.32*i, rely=.30, relwidth=.30, relheight=.36)
                t = tk.Label(card, text=title, font=(self.FF,15,"bold"),
                             bg=C["CARD"], fg=C["FG"])
                t.place(relx=.5, rely=.22, anchor="center")
                sub = tk.Label(card, text="", font=(self.FF,10),
                               bg=C["CARD"], fg=C["FG2"], justify="center")
                sub.place(relx=.5, rely=.62, anchor="center")
                card.sub = sub
            else:
                card.place(relx=.5, rely=.76, relwidth=.28, relheight=.10, anchor="n")
                t = tk.Label(card, text="⚙  "+title, font=(self.FF,12),
                             bg=C["CARD"], fg=C["FG"])
                t.place(relx=.5, rely=.5, anchor="center")
            for w in [card]+card.winfo_children():
                w.bind("<Button-1>", lambda _,i=i: self._click_menu(i))
                w.bind("<Enter>",    lambda _,i=i: self._hover_menu(i))
            self.menu_cards.append(card)
        self._hint(f,"↑ ↓ ← →  Navigate      Enter  Select      F8  Always on top")

    def _menu_stats(self, cat):
        total = len(self._vdict(cat)); en = self._enabled_count(cat)
        comp = min(self._comp(cat), en)
        nblk = sum(1 for b in self._enabled_blocks(cat) if b)
        return f"{en} of {total} words selected\n{comp}/{en} done  ·  {nblk} blocks"

    def _draw_menu(self):
        for cat, card in zip(("regular","irregular"), self.menu_cards):
            card.sub.config(text=self._menu_stats(cat))
        for i, card in enumerate(self.menu_cards):
            self._card_sel(card, i == self.mi)

    def _hover_menu(self, i):
        if self.screen=="menu" and self.mi != i:
            self.mi = i; self._draw_menu()

    def _click_menu(self, i):
        self.mi = i; self._draw_menu(); self._menu_go()

    def _menu_go(self):
        if   self.mi==0: self.cat="regular";   self._open_setup()
        elif self.mi==1: self.cat="irregular"; self._open_setup()
        else:            self._open_settings()

    # ── Settings screen ───────────────────────────────────────────────────────
    def _bld_settings(self):
        f = self.fr["settings"]; C = self.C
        self._lbl(f,"SETTINGS",18,C["FG"],bold=True).place(relx=.5,rely=.08,anchor="n")
        self._lbl(f,"Voice",11,C["FG3"]).place(relx=.24,rely=.26,anchor="w")
        self.st_rows = []
        ys = [.33,.41, .57,.65]
        for y in ys[:2]:
            l = self._lbl(f,"",13,cursor="hand2",anchor="w")
            l.place(relx=.27,rely=y,anchor="w"); self.st_rows.append(l)
        self._lbl(f,"Theme",11,C["FG3"]).place(relx=.24,rely=.50,anchor="w")
        for y in ys[2:]:
            l = self._lbl(f,"",13,cursor="hand2",anchor="w")
            l.place(relx=.27,rely=y,anchor="w"); self.st_rows.append(l)
        if not audio.TTS_OK:
            self._lbl(f,"(voice disabled: edge-tts / pygame not installed)",10,C["RED"])\
                .place(relx=.5,rely=.78,anchor="center")
        for i,l in enumerate(self.st_rows):
            l.bind("<Button-1>", lambda _,i=i: self._click_settings(i))
            l.bind("<Enter>", lambda _,i=i: self._hover_settings(i))
        self._hint(f,"↑↓ Navigate      Enter Apply      Esc Back")

    def _hover_settings(self, i):
        if self.screen=="settings" and self.sti != i:
            self.sti=i; self._draw_settings()

    def _open_settings(self):
        cur = self._get_voice()
        self.sti = next((i for i,(k,_) in enumerate(VOICES) if k==cur), 0)
        self._show("settings"); self._draw_settings()

    def _draw_settings(self):
        C = self.C; cur = self._get_voice(); theme = self.prog.get("theme","light")
        opts = [ (k==cur, lbl) for k,lbl in VOICES ]
        opts += [ (theme=="light","Light theme"), (theme=="dark","Dark theme") ]
        for i,(on,txt) in enumerate(opts):
            mark = "●  " if on else "○  "
            self.st_rows[i].config(
                text=(PTR if i==self.sti else "   ")+mark+txt,
                fg=C["FG"] if i==self.sti else C["FG2"])

    def _sel_settings(self):
        if self.sti < 2:
            self._set_voice(VOICES[self.sti][0]); self._draw_settings()
        else:
            theme = "light" if self.sti==2 else "dark"
            if theme != self.prog.get("theme"):
                self.prog["theme"] = theme; self._save_prog()
                self._apply_theme()
            else:
                self._draw_settings()

    def _click_settings(self, i):
        self.sti = i; self._draw_settings(); self._sel_settings()

    def _apply_theme(self):
        self.C = THEMES[self.prog.get("theme","light")]
        self.win.config(bg=self.C["BG"])
        for fr in self.fr.values(): fr.destroy()
        self._base_fonts = {}
        self._build()
        self._init_fonts()
        self._show("settings"); self._draw_settings()

    # ── Setup screen ──────────────────────────────────────────────────────────
    def _bld_setup(self):
        f = self.fr["setup"]; C = self.C
        self.su_t = self._lbl(f,"",18,C["FG"],bold=True); self.su_t.place(relx=.5,rely=.035,anchor="n")
        self.su_sub = self._lbl(f,"",10,C["FG3"]); self.su_sub.place(relx=.5,rely=.10,anchor="n")

        self._lbl(f,"Practice",10,C["FG3"]).place(relx=.16,rely=.16,anchor="w")
        self.su_base = self._lbl(f,"",13,cursor="hand2",anchor="w"); self.su_base.place(relx=.19,rely=.22,anchor="w")
        self.su_past = self._lbl(f,"",13,cursor="hand2",anchor="w"); self.su_past.place(relx=.19,rely=.28,anchor="w")
        self.su_part = self._lbl(f,"",13,cursor="hand2",anchor="w"); self.su_part.place(relx=.19,rely=.34,anchor="w")
        self.su_m = self._lbl(f,"",13,cursor="hand2",anchor="w"); self.su_m.place(relx=.19,rely=.415,anchor="w")
        self.su_h = self._lbl(f,"",13,cursor="hand2",anchor="w"); self.su_h.place(relx=.19,rely=.475,anchor="w")

        self._lbl(f,"Words",10,C["FG3"]).place(relx=.16,rely=.545,anchor="w")
        self.su_w = self._lbl(f,"",13,cursor="hand2",anchor="w"); self.su_w.place(relx=.19,rely=.605,anchor="w")

        self._lbl(f,"Start",10,C["FG3"]).place(relx=.16,rely=.675,anchor="w")
        self.su_c = self._lbl(f,"",13,cursor="hand2",anchor="w"); self.su_c.place(relx=.19,rely=.735,anchor="w")
        self.su_b = self._lbl(f,"",13,cursor="hand2",anchor="w"); self.su_b.place(relx=.19,rely=.795,anchor="w")
        self.su_bp = self._lbl(f,"",9,C["FG3"],anchor="w");        self.su_bp.place(relx=.23,rely=.838,anchor="w")
        self.su_n = self._lbl(f,"",13,cursor="hand2",anchor="w"); self.su_n.place(relx=.19,rely=.885,anchor="w")

        self.su_msg = self._lbl(f,"",10,C["RED"]); self.su_msg.place(relx=.5,rely=.935,anchor="center")
        self._hint(f,"Space Toggle    ↑↓ Move    ←→ Block/Mode    Enter Select    Esc Back")
        self.su_wm = {"col_base":self.su_base,"col_past":self.su_past,"col_part":self.su_part,
                      "mode":self.su_m,"hint":self.su_h,
                      "words":self.su_w,"ac":self.su_c,"ab":self.su_b,"an":self.su_n}
        for k,ww in self.su_wm.items():
            ww.bind("<Button-1>", lambda _,k=k: self._click_setup(k))
            ww.bind("<Enter>", lambda _,k=k: self._hover_setup(k))

    def _hover_setup(self, k):
        if self.screen=="setup" and k in self.sr and self.si != self.sr.index(k):
            self.si = self.sr.index(k); self._draw_setup()

    def _open_setup(self):
        info = CATS[self.cat]
        self.cst = {"base":True,"past":True,"part":info["has_part"]}
        self.su_msg.config(text="")
        # default block = where progress would continue
        comp = min(self._comp(), self._enabled_count())
        self.sb = self._block_at(comp)
        self._build_sr()
        self.si = self.sr.index("ac") if "ac" in self.sr else self.sr.index("an")
        self._show("setup"); self._draw_setup()

    def _block_at(self, comp):
        """Index of the layout block that starts at completed-count `comp`."""
        acc = 0
        blocks = self._enabled_blocks()
        for i,b in enumerate(blocks):
            if acc >= comp and b: return i
            acc += len(b)
        return next((i for i,b in enumerate(blocks) if b), 0)

    def _build_sr(self):
        total = self._enabled_count()
        has_c = 0 < self._comp() < total
        self.sr = ["col_base","col_past","col_part","mode"]
        if self._mode() == "listen": self.sr.append("hint")
        self.sr.append("words")
        if has_c: self.sr.append("ac")
        self.sr += ["ab","an"]

    def _draw_setup(self):
        C = self.C; info = CATS[self.cat]
        blocks = self._enabled_blocks()
        total = self._enabled_count(); comp = min(self._comp(), total)
        nblk = len(blocks)
        self.su_t.config(text=info["title"].upper())
        self.su_sub.config(text=f"{comp}/{total} done")
        def cb(ww,k,lbl,en):
            if not en: self.cst[k]=False
            m = "☑" if self.cst[k] else "☐"
            ww.config(text=f"{m}  {lbl}"+("" if en else "   (n/a)"),
                      fg=C["FG2"] if en else C["FG3"])
        cb(self.su_base,"base","Base form",True)
        cb(self.su_past,"past","Past simple",True)
        cb(self.su_part,"part","Past participle",info["has_part"])

        listen = self._mode() == "listen"
        if audio.TTS_OK:
            mtxt = "Listening — type what you hear" if listen else "Reading — fill in sentences"
            self.su_m.config(text=f"Mode:   ‹ {mtxt} ›", fg=C["FG2"])
        else:
            self.su_m.config(text="Mode:   Reading   (listening needs edge-tts + pygame)",
                             fg=C["FG3"])
        if listen:
            m = "☑" if self.prog.get("listen_hint", True) else "☐"
            self.su_h.config(text=f"{m}  Show Spanish word as a hint", fg=C["FG2"])
        elif not self.key:
            self.su_h.config(
                text="No API key — you'll practice with blank fields."
                     + ("  Try Listening (no key needed)." if audio.TTS_OK else ""),
                fg=C["FG3"])
        else:
            self.su_h.config(text="")

        self.su_w.config(text=f"Edit word list   ({total}/{len(self._vdict())} selected)")
        self.su_c.config(text=f"Continue  ({comp}/{total})" if "ac" in self.sr else "")
        self.sb = max(0, min(self.sb, nblk-1)) if nblk else 0
        cur = blocks[self.sb] if blocks else []
        self.su_b.config(text=f"Start at block   ‹  {self.sb+1} / {max(1,nblk)}  ›")
        prev = ", ".join(v[1] for v in cur[:4])
        self.su_bp.config(text=(f"{len(cur)} words:  {prev}…" if cur else "empty block"))
        self.su_n.config(text="New session  (reset progress)")
        for i,r in enumerate(self.sr):
            ww = self.su_wm[r]; t = ww.cget("text")
            if t.startswith(PTR): t = t[len(PTR):]
            ww.config(text=(PTR+t) if i==self.si else t)

    def _tog(self):
        r = self.sr[self.si]
        if r == "mode": self._toggle_mode(); return
        if r == "hint": self._toggle_hint(); return
        if not r.startswith("col_"): return
        k = r[4:]
        if k=="part" and not CATS[self.cat]["has_part"]: return
        if self.cst[k] and sum(self.cst.values())==1:
            self.su_msg.config(text="Select at least one form."); return
        self.su_msg.config(text=""); self.cst[k] = not self.cst[k]; self._draw_setup()

    def _toggle_mode(self):
        if not audio.TTS_OK:
            self.su_msg.config(text="Install edge-tts and pygame to use listening mode.")
            return
        self.prog["mode"] = "listen" if self._mode()=="read" else "read"
        self._save_prog()
        self._build_sr()
        self.si = self.sr.index("mode")
        self._draw_setup()

    def _toggle_hint(self):
        self.prog["listen_hint"] = not self.prog.get("listen_hint", True)
        self._save_prog(); self._draw_setup()

    def _sel_setup(self):
        r = self.sr[self.si]
        if r.startswith("col_") or r in ("mode","hint"): self._tog()
        elif r=="words": self._open_words()
        elif r=="ac": self._start("continue")
        elif r=="ab": self._start("block")
        elif r=="an": self._start("new")

    def _click_setup(self, k):
        if k not in self.sr: return
        self.si = self.sr.index(k); self._draw_setup(); self._sel_setup()

    # ── Words screen (enable/disable, create, delete, carry words) ────────────
    def _bld_words(self):
        f = self.fr["words"]; C = self.C
        self.wd_t = self._lbl(f,"",16,C["FG"],bold=True)
        self.wd_t.place(relx=.5,rely=.025,anchor="n")
        self.wd_sub = self._lbl(f,"",9,C["FG3"])
        self.wd_sub.place(relx=.5,rely=.085,anchor="n")
        self.wd_add = self._lbl(f,"[ + New word ]",10,C["ACC_D"],cursor="hand2")
        self.wd_add.place(relx=.06,rely=.135,anchor="w")
        self.wd_add.bind("<Button-1>", lambda _: self._wd_new_dialog())
        self.wd_res = self._lbl(f,"",10,C["ACC_D"],cursor="hand2")
        self.wd_res.place(relx=.94,rely=.135,anchor="e")
        self.wd_res.bind("<Button-1>", lambda _: self._wd_restore())

        self.wd_cv = tk.Canvas(f, bg=C["BG"], highlightthickness=0)
        self.wd_scr = tk.Scrollbar(f, orient="vertical", command=self.wd_cv.yview)
        self.wd_cv.config(yscrollcommand=self.wd_scr.set)
        self.wd_cv.place(relx=.06, rely=.18, relwidth=.86, relheight=.74)
        self.wd_scr.place(relx=.93, rely=.18, relwidth=.02, relheight=.74)
        self.wd_in = tk.Frame(self.wd_cv, bg=C["BG"])
        self.wd_win = self.wd_cv.create_window((0,0), window=self.wd_in, anchor="nw")
        self.wd_in.bind("<Configure>",
            lambda e: self.wd_cv.config(scrollregion=self.wd_cv.bbox("all") or (0,0,0,0)))
        self.wd_cv.bind("<Configure>",
            lambda e: self.wd_cv.itemconfig(self.wd_win, width=e.width))
        self._hint(f,"Space Toggle    → Pick up   ↑↓ Carry   ← Drop    N New    Del Delete    A Block on/off    Esc Done")

    def _open_words(self):
        self.wd_t.config(text=f"{CATS[self.cat]['title'].upper()} — WORD LIST")
        self.wd_blocks = [list(b) for b in self._layout()]
        if not self.wd_blocks: self.wd_blocks = [[]]
        self.wd_carry = None; self.wd_del_pending = None
        self.wi = 0
        self._words_rebuild()
        self._show("words")

    def _words_rebuild(self, keep_name=None):
        C = self.C
        for ch in self.wd_in.winfo_children(): ch.destroy()
        self.wd_rows = []; self.wd_recs = {}
        self.wd_heads = {}; self.wd_head_frames = {}
        vd = self._vdict()
        customs = {v[1] for v in self._custom()}
        has_part = CATS[self.cat]["has_part"]

        for bi, blk in enumerate(self.wd_blocks):
            head = tk.Frame(self.wd_in, bg=C["BG"]); head.pack(fill="x", pady=(10 if bi else 2, 3))
            hl = tk.Label(head, text="", font=(self.FF,11,"bold"), bg=C["BG"], fg=C["ACC_D"])
            hl.pack(side="left", padx=(2,8))
            ha = tk.Label(head, text="[ all ]", font=(self.FF,9), bg=C["BG"],
                          fg=C["FG3"], cursor="hand2")
            ha.pack(side="left")
            ha.bind("<Button-1>", lambda _,b=bi: self._wd_toggle_block(b))
            self.wd_heads[bi] = hl; self.wd_head_frames[bi] = head

            for name in blk:
                v = vd.get(name)
                if not v: continue
                row = tk.Frame(self.wd_in, bg=C["BG"], cursor="hand2",
                               highlightthickness=0, highlightbackground=C["ACC"])
                row.pack(fill="x", pady=1)
                forms = " · ".join(v[1:4] if has_part else v[1:3])
                l = tk.Label(row, text="", font=(self.FF,11), bg=C["BG"], anchor="w")
                l.pack(side="left", padx=(14,0))
                r = tk.Label(row, text=v[0]+("  •" if name in customs else ""),
                             font=(self.FF,10), bg=C["BG"], fg=C["FG3"], anchor="e")
                r.pack(side="right", padx=(0,14))
                rec = {"name":name,"bi":bi,"frame":row,"l":l,"r":r,"forms":forms}
                for w in (row,l,r):
                    w.bind("<Button-1>", lambda _,n=name: self._wd_click_name(n))
                self.wd_rows.append(rec); self.wd_recs[name] = rec

        foot = tk.Label(self.wd_in, text="[ + Add block ]", font=(self.FF,10),
                        bg=C["BG"], fg=C["FG3"], cursor="hand2")
        foot.pack(pady=(14,8))
        foot.bind("<Button-1>", lambda _: self._wd_add_block())

        if keep_name and keep_name in self.wd_recs:
            self.wi = self.wd_rows.index(self.wd_recs[keep_name])
        self.wi = max(0, min(self.wi, len(self.wd_rows)-1))
        self._wd_refresh_all()
        self._collect_fonts(self.wd_in); self._scale_fonts()
        self.wd_cv.yview_moveto(0)
        if keep_name: self.win.after(50, lambda: self._wd_scroll_to(self.wi))

    def _wd_refresh_all(self):
        C = self.C; ds = self._disabled()
        for i in range(len(self.wd_rows)): self._wd_refresh_row(i)
        en_total = 0
        for bi, blk in enumerate(self.wd_blocks):
            en = sum(1 for n in blk if n not in ds); en_total += en
            if bi in self.wd_heads:
                self.wd_heads[bi].config(text=f"Block {bi+1}  —  {en}/{len(blk)} selected")
        if self.wd_carry:
            self.wd_sub.config(fg=C["ACC_D"],
                text=f"Carrying '{self.wd_carry}' — move it with ↑↓, drop it with ←")
        else:
            self.wd_sub.config(fg=C["FG3"],
                text=f"{en_total} words selected  ·  {len(self.wd_blocks)} blocks  ·  "
                     "changes are saved automatically")
        dele = self._deleted()
        self.wd_res.config(text=f"[ Restore {len(dele)} deleted ]" if dele else "")

    def _wd_refresh_row(self, i):
        C = self.C; rec = self.wd_rows[i]
        ds = self._disabled()
        on  = rec["name"] not in ds
        sel = (i == self.wi)
        carried = (rec["name"] == self.wd_carry)
        bg  = C["SEL"] if (sel or carried) else C["BG"]
        mark = "☑" if on else "☐"
        rec["frame"].config(bg=bg, highlightthickness=1 if carried else 0)
        rec["l"].pack_configure(padx=((34 if carried else 14), 0))
        rec["l"].config(text=f"{mark}  {rec['forms']}", bg=bg,
                        fg=(C["FG"] if sel else C["FG2"]) if on else C["FG3"])
        rec["r"].config(bg=bg, fg=C["FG2"] if sel else C["FG3"])

    def _wd_click_name(self, name):
        if self.wd_carry: return
        rec = self.wd_recs.get(name)
        if not rec: return
        old = self.wi; self.wi = self.wd_rows.index(rec)
        self._wd_refresh_row(old); self._wd_refresh_row(self.wi)
        self._wd_toggle()

    def _wd_toggle(self):
        if not self.wd_rows or self.wd_carry: return
        self.wd_del_pending = None
        rec = self.wd_rows[self.wi]; ds = self._disabled()
        if rec["name"] in ds: ds.discard(rec["name"])
        else: ds.add(rec["name"])
        self._set_disabled(ds)
        self._wd_refresh_all()

    def _wd_toggle_block(self, bi):
        if self.wd_carry: return
        blk = self.wd_blocks[bi]; ds = self._disabled()
        if any(n in ds for n in blk): ds.difference_update(blk)
        else: ds.update(blk)
        self._set_disabled(ds)
        self._wd_refresh_all()

    # — carry a word (game-style move) —
    def _wd_pick(self):
        if not self.wd_rows or self.wd_carry: return
        self.wd_carry = self.wd_rows[self.wi]["name"]
        self.wd_del_pending = None
        self._wd_refresh_all()

    def _wd_drop(self):
        if not self.wd_carry: return
        name = self.wd_carry
        self.wd_carry = None
        # drop can leave the source block empty — rebuild so its header goes away
        if any(not b for b in self.wd_blocks):
            self.wd_blocks = [b for b in self.wd_blocks if b] or [[]]
            self._wd_save_layout()
            self._words_rebuild(keep_name=name)
        else:
            self._wd_save_layout()
            self._wd_refresh_all()

    def _wd_pos(self, name):
        for bi, blk in enumerate(self.wd_blocks):
            if name in blk: return bi, blk.index(name)
        return None, None

    def _wd_carry_move(self, d):
        name = self.wd_carry
        bi, pos = self._wd_pos(name)
        if bi is None: return
        blk = self.wd_blocks[bi]
        if d > 0:
            if pos < len(blk)-1:
                blk[pos], blk[pos+1] = blk[pos+1], blk[pos]
            elif bi < len(self.wd_blocks)-1:
                blk.pop(pos); self.wd_blocks[bi+1].insert(0, name)
            else: return
        else:
            if pos > 0:
                blk[pos-1], blk[pos] = blk[pos], blk[pos-1]
            elif bi > 0:
                blk.pop(pos); self.wd_blocks[bi-1].append(name)
            else: return
        self._wd_repack(name)

    def _wd_repack(self, name):
        """Re-pack the carried row at its new position (no full rebuild)."""
        rec = self.wd_recs[name]
        bi, pos = self._wd_pos(name)
        rec["bi"] = bi
        if pos > 0:
            prev = self.wd_recs[self.wd_blocks[bi][pos-1]]["frame"]
            rec["frame"].pack(fill="x", pady=1, after=prev)
        else:
            rec["frame"].pack(fill="x", pady=1, after=self.wd_head_frames[bi])
        self.wd_rows = [self.wd_recs[n] for blk in self.wd_blocks
                        for n in blk if n in self.wd_recs]
        self.wi = self.wd_rows.index(rec)
        self._wd_refresh_all()
        self._wd_scroll_to(self.wi)

    # — create / delete / restore —
    def _wd_add_block(self):
        if self.wd_carry: return
        self.wd_blocks.append([])
        keep = self.wd_rows[self.wi]["name"] if self.wd_rows else None
        self._words_rebuild(keep_name=keep)

    def _wd_create_word(self, row, bi):
        """row = [es, base, past] (+[part] for irregular); insert into block bi."""
        p = self._cat_prog()
        c = self._custom(); c.append([s.strip() for s in row]); p["custom"] = c
        if not self.wd_blocks: self.wd_blocks = [[]]
        bi = max(0, min(bi, len(self.wd_blocks)-1))
        self.wd_blocks[bi].append(row[1].strip())
        self._wd_save_layout()
        self._words_rebuild(keep_name=row[1].strip())
        # generate its audio right away
        if audio.TTS_OK:
            voice = self._get_voice()
            words = []
            for raw in row[1:]: words.extend(self._answer_parts(raw))
            def run():
                for w_ in dict.fromkeys(words):
                    try: audio.ensure(w_, voice)
                    except Exception: pass
            threading.Thread(target=run, daemon=True).start()

    def _wd_new_dialog(self):
        if self.screen != "words" or self.wd_carry: return
        C = self.C; has_part = CATS[self.cat]["has_part"]
        dlg = tk.Toplevel(self.win)
        dlg.title("New word"); dlg.transient(self.win)
        try: dlg.grab_set()
        except tk.TclError: pass
        dlg.resizable(False, False); dlg.config(bg=C["BG"], padx=24, pady=18)

        tk.Label(dlg, text="Create your own word", font=(self.FF,13,"bold"),
                 bg=C["BG"], fg=C["FG"]).grid(row=0, column=0, columnspan=3, pady=(0,12))
        fields = [("Spanish (significado)", ""), ("English (base form)", ""),
                  ("Past simple", "")] + ([("Past participle","")] if has_part else [])
        entries = []
        for i,(lbl,_) in enumerate(fields):
            tk.Label(dlg, text=lbl, font=(self.FF,10), bg=C["BG"], fg=C["FG2"],
                     anchor="w").grid(row=1+i, column=0, sticky="w", pady=3)
            e = tk.Entry(dlg, font=(self.FF,11), width=20, bg=C["ENTRY"], fg=C["FG"],
                         insertbackground=C["FG"], bd=0, highlightthickness=1,
                         highlightbackground=C["BORDER"], highlightcolor=C["ACC"])
            e.grid(row=1+i, column=1, columnspan=2, sticky="we", padx=(12,0), pady=3)
            entries.append(e)

        cur_bi = self.wd_rows[self.wi]["bi"] if self.wd_rows else 0
        blk = [cur_bi]
        rowN = 1+len(fields)
        tk.Label(dlg, text="Block", font=(self.FF,10), bg=C["BG"], fg=C["FG2"],
                 anchor="w").grid(row=rowN, column=0, sticky="w", pady=(8,3))
        bl = tk.Label(dlg, text="", font=(self.FF,11), bg=C["BG"], fg=C["FG"])
        bl.grid(row=rowN, column=1, pady=(8,3))
        def bset(d):
            blk[0] = max(0, min(blk[0]+d, len(self.wd_blocks)-1)); bdraw()
        def bdraw():
            bl.config(text=f"‹   {blk[0]+1} / {len(self.wd_blocks)}   ›")
        bl.bind("<Button-1>", lambda e: bset(1 if e.x > bl.winfo_width()//2 else -1))
        bdraw()

        msg = tk.Label(dlg, text="", font=(self.FF,9), bg=C["BG"], fg=C["RED"])
        msg.grid(row=rowN+1, column=0, columnspan=3, pady=(6,0))

        def save(_=None):
            vals = [e.get().strip() for e in entries]
            eng  = [v.lower() for v in vals[1:]]
            if not vals[0] or any(not v for v in eng):
                msg.config(text="Fill in every field."); return
            if any("|" in v for v in vals):
                msg.config(text="The character | is not allowed."); return
            if eng[0] in self._vdict():
                msg.config(text=f"'{eng[0]}' already exists."); return
            self._wd_create_word([vals[0]] + eng, blk[0])
            dlg.destroy()
        def cancel(_=None): dlg.destroy()

        bf = tk.Frame(dlg, bg=C["BG"]); bf.grid(row=rowN+2, column=0, columnspan=3, pady=(12,0))
        for txt, cmd in (("Save", save), ("Cancel", cancel)):
            b = tk.Label(bf, text=txt, font=(self.FF,11), bg=C["CARD"], fg=C["FG"],
                         padx=16, pady=7, cursor="hand2",
                         highlightthickness=1, highlightbackground=C["BORDER"])
            b.pack(side="left", padx=6)
            b.bind("<Button-1>", cmd)
        tk.Label(dlg, text="Tab Next field    Enter Save    Esc Cancel",
                 font=(self.FF,8), bg=C["BG"], fg=C["FG3"])\
            .grid(row=rowN+3, column=0, columnspan=3, pady=(10,0))

        dlg.bind("<Return>", save); dlg.bind("<Escape>", cancel)
        dlg.update_idletasks()
        x = self.win.winfo_rootx()+(self.win.winfo_width() -dlg.winfo_width()) //2
        y = self.win.winfo_rooty()+(self.win.winfo_height()-dlg.winfo_height())//2
        dlg.geometry(f"+{max(x,0)}+{max(y,0)}")
        entries[0].focus_set(); dlg.wait_window()

    def _wd_delete(self):
        if self.screen != "words" or not self.wd_rows or self.wd_carry: return
        rec = self.wd_rows[self.wi]; name = rec["name"]
        if self.wd_del_pending != name:
            self.wd_del_pending = name
            self.wd_sub.config(text=f"Delete '{name}'?  Press Delete again to confirm",
                               fg=self.C["RED"])
            return
        self.wd_del_pending = None
        nxt = (self.wd_rows[self.wi+1]["name"] if self.wi+1 < len(self.wd_rows)
               else self.wd_rows[self.wi-1]["name"] if self.wi > 0 else None)
        for blk in self.wd_blocks:
            if name in blk: blk.remove(name); break
        p = self._cat_prog()
        customs = self._custom()
        if any(v[1] == name for v in customs):
            p["custom"] = [v for v in customs if v[1] != name]
        else:
            dele = self._deleted(); dele.add(name); p["deleted"] = sorted(dele)
        ds = self._disabled(); ds.discard(name); p["disabled"] = sorted(ds)
        self._wd_save_layout()
        self._words_rebuild(keep_name=nxt)

    def _wd_restore(self):
        if self.screen != "words" or self.wd_carry: return
        p = self._cat_prog()
        if not p.get("deleted"): return
        self._wd_save_layout()
        p["deleted"] = []
        self._save_prog()
        self.wd_blocks = [list(b) for b in self._layout()]
        self._words_rebuild()

    # — navigation / persistence —
    def _wd_nav(self, d):
        if not self.wd_rows: return
        self.wd_del_pending = None
        old = self.wi
        self.wi = max(0, min(self.wi+d, len(self.wd_rows)-1))
        if old != self.wi:
            self._wd_refresh_row(old); self._wd_refresh_row(self.wi)
            self._wd_scroll_to(self.wi)

    def _wd_scroll_to(self, i):
        try:
            fr = self.wd_rows[i]["frame"]
            self.wd_cv.update_idletasks()
            y, rh = fr.winfo_y(), fr.winfo_height()
            total = max(1, self.wd_in.winfo_height())
            ch = self.wd_cv.winfo_height()
            top = self.wd_cv.canvasy(0)
            if y < top + 24:
                self.wd_cv.yview_moveto(max(0, y-40)/total)
            elif y + rh > top + ch - 24:
                self.wd_cv.yview_moveto(max(0, y - ch + rh + 40)/total)
        except Exception: pass

    def _wd_wheel(self, e):
        if self.screen != "words": return
        d = -1 if (getattr(e,"num",0)==4 or getattr(e,"delta",0)>0) else 1
        self.wd_cv.yview_scroll(d, "units")

    def _wd_save_layout(self):
        self._cat_prog()["layout"] = [list(b) for b in self.wd_blocks if b]
        self._save_prog()

    def _wd_done(self):
        if self.wd_carry: self._wd_drop()
        self._wd_save_layout()
        # selection may have shrunk: clamp progress
        self._set_comp(self._comp())
        self._show("setup"); self._build_sr()
        self.si = min(self.si, len(self.sr)-1)
        self._draw_setup()

    # ── Session start ─────────────────────────────────────────────────────────
    def _start(self, mode):
        sel = [k for k,_,_ in COLS if self.cst.get(k, False)]
        if not sel:
            self.su_msg.config(text="Select at least one form."); return
        self.cols = sel
        eb = [b for b in self._enabled_blocks()]
        if not any(eb):
            self.su_msg.config(text="No words selected — edit the word list."); return

        # session blocks: enabled, non-empty, shuffled copies
        idx_of = []          # layout-block-index -> session index
        self.sblocks = []
        for i,b in enumerate(eb):
            idx_of.append(len(self.sblocks) if b else None)
            if b: self.sblocks.append(random.sample(b, len(b)))
        self._starts = []
        acc = 0
        for b in self.sblocks:
            self._starts.append(acc); acc += len(b)
        total = acc

        if mode == "new":
            self._set_comp(0); b0 = 0
        elif mode == "block":
            b0 = idx_of[self.sb] if self.sb < len(idx_of) else None
            if b0 is None:
                self.su_msg.config(text="That block has no words selected."); return
        else:  # continue
            comp = min(self._comp(), total)
            b0 = 0
            for i,s in enumerate(self._starts):
                if s <= comp: b0 = i
            if comp >= total: b0 = 0

        self.ok_n = self.bad_n = self.streak = 0
        self._start_block(b0)

    def _start_block(self, b0):
        self.bidx = b0; self.vidx = 0
        self.blk_ok = self.blk_bad = 0
        self._load_block()

    def _cur_block(self): return self.sblocks[self.bidx]
    def _cur_verb(self):  return self._cur_block()[self.vidx]

    def _block_needed(self, b):
        idx_map = {"base":1,"past":2,"part":3}
        needed = []
        for verb in b:
            for col in self.cols:
                if not self.cache.has_any(verb[1], col):
                    needed.append((verb[1], col, self._pick_answer(verb[idx_map[col]])))
        return list(dict.fromkeys(needed))

    def _load_block(self):
        if self._mode() == "listen":       # audio only, no sentences needed
            self._begin(); return
        needed = self._block_needed(self._cur_block())
        if not needed or not self.key or not GEMINI_OK:
            self._begin(); return
        self._pending = needed
        self._show("load")
        self.ld_msg.config(text="Generating practice sentences…")
        self.ld_err.config(text=""); self.ld_ret.config(text=""); self.ld_off.config(text="")
        self._anim_i = 0; self._animate()
        self.cache.fetch(needed, self.key,
                         lambda r: self.win.after(0, lambda: self._fetch_done(r)))

    def _fetch_done(self, results):
        if self.screen != "load": return
        if results: self._begin()
        else:
            self.ld_msg.config(text="Could not load sentences.")
            self.ld_err.config(text="Check your API key and internet connection.")
            self.ld_ret.config(text="▶ Retry")
            self.ld_off.config(text="▶ Practice without sentences")

    def _retry(self):
        self.ld_err.config(text=""); self.ld_ret.config(text=""); self.ld_off.config(text="")
        self.ld_msg.config(text="Retrying…")
        self._anim_i = 0; self._animate()
        self.cache.fetch(self._pending, self.key,
                         lambda r: self.win.after(0, lambda: self._fetch_done(r)))

    def _animate(self):
        if self.screen != "load": return
        self.ld_dot.config(text=SPIN[self._anim_i % len(SPIN)])
        self._anim_i += 1
        self.win.after(90, self._animate)

    def _bld_load(self):
        f = self.fr["load"]; C = self.C
        self.ld_dot = self._lbl(f,"⠋",30,C["ACC"]); self.ld_dot.place(relx=.5,rely=.30,anchor="center")
        self.ld_msg = self._lbl(f,"Loading…",15,C["FG"])
        self.ld_msg.place(relx=.5,rely=.44,anchor="center")
        self.ld_err = self._lbl(f,"",11,C["RED"]); self.ld_err.place(relx=.5,rely=.56,anchor="center")
        self.ld_ret = self._lbl(f,"",13,C["ACC_D"],cursor="hand2")
        self.ld_ret.place(relx=.5,rely=.68,anchor="center")
        self.ld_off = self._lbl(f,"",13,C["ACC_D"],cursor="hand2")
        self.ld_off.place(relx=.5,rely=.77,anchor="center")
        self.ld_ret.bind("<Button-1>", lambda _: self._retry())
        self.ld_off.bind("<Button-1>", lambda _: self._begin())
        self._hint(f,"Esc Back")

    def _begin(self):
        self._show("prac"); self._load_verb()
        # pre-generate audio for this block (and the next) so playback is instant
        blocks = [self._cur_block()]
        if self.bidx+1 < len(self.sblocks): blocks.append(self.sblocks[self.bidx+1])
        self._prefetch_audio(blocks)
        # prefetch the next block's sentences in the background (reading mode)
        if (self._mode() != "listen" and self.key and GEMINI_OK
                and self.bidx+1 < len(self.sblocks)):
            nxt = self._block_needed(self.sblocks[self.bidx+1])
            if nxt: self.cache.fetch(nxt, self.key, lambda _: None)

    def _prefetch_audio(self, blocks):
        """Generate + cache TTS for every word of the given blocks, one by one."""
        if not audio.TTS_OK: return
        voice = self._get_voice()
        idx_map = {"base":1,"past":2,"part":3}
        words = []
        for b in blocks:
            for verb in b:
                for col in self.cols:
                    words.extend(self._answer_parts(verb[idx_map[col]]))
        def run():
            for w_ in dict.fromkeys(words):
                try: audio.ensure(w_, voice)
                except Exception: pass
        threading.Thread(target=run, daemon=True).start()

    # ── Practice screen ───────────────────────────────────────────────────────
    def _bld_prac(self):
        f = self.fr["prac"]; C = self.C
        self.pr_p = self._lbl(f,"",10,C["FG3"],anchor="w")
        self.pr_p.place(relx=.04,rely=.045,anchor="w")
        self.pr_s = self._lbl(f,"",10,C["FG3"],anchor="e")
        self.pr_s.place(relx=.96,rely=.045,anchor="e")
        self.pr_bar = tk.Canvas(f, height=6, bg=C["TRACK"], highlightthickness=0)
        self.pr_bar.place(relx=.04, rely=.085, relwidth=.92, height=6)
        self.pr_bar.bind("<Configure>", lambda e: self._draw_bar())

        self.pr_card = self._card(f)
        self.pr_card.place(relx=.5, rely=.13, relwidth=.92, relheight=.19, anchor="n")
        self.pr_v = tk.Label(self.pr_card, text="", font=(self.FF,26,"bold"),
                             bg=C["CARD"], fg=C["FG"])
        self.pr_v.place(relx=.5, rely=.42, anchor="center")
        self.pr_vh = tk.Label(self.pr_card, text="", font=(self.FF,11),
                              bg=C["CARD"], fg=C["FG3"])
        self.pr_vh.place(relx=.5, rely=.80, anchor="center")

        self.pr_ff = tk.Frame(f, bg=C["BG"])
        self.pr_ff.place(relx=.5, rely=.35, anchor="n", relwidth=.94, relheight=.50)
        self.pr_fb = self._lbl(f,"",13,C["GREEN"],bold=True)
        self.pr_fb.place(relx=.5,rely=.885,anchor="center")
        self.pr_hint = self._hint(f,"")

    def _draw_bar(self):
        C = self.C; bar = self.pr_bar
        bar.delete("all")
        w = max(1, bar.winfo_width())
        if not self.sblocks: return
        n = len(self._cur_block())
        frac = min(1.0, self.vidx / n) if n else 0
        bar.config(bg=C["TRACK"])
        if frac > 0:
            bar.create_rectangle(0, 0, int(w*frac), 8, fill=C["ACC"], width=0)

    def _load_verb(self):
        if self.fb_id: self.win.after_cancel(self.fb_id); self.fb_id = None
        self.locked = False; self._vt += 1
        blk = self._cur_block()
        if self.vidx >= len(blk): self._blk_done(); return

        C = self.C; verb = self._cur_verb()
        listen = self._mode() == "listen"
        total = sum(len(b) for b in self.sblocks)
        done  = self._starts[self.bidx] + self.vidx
        self.pr_p.config(text=f"Block {self.bidx+1}/{len(self.sblocks)}   ·   "
                              f"Word {self.vidx+1}/{len(blk)}   ·   {done}/{total} total")
        stats = f"✓ {self.ok_n}    ✗ {self.bad_n}"
        if self.streak >= 3: stats += f"    ·    {self.streak} in a row!"
        self.pr_s.config(text=stats)
        self._draw_bar()
        self.pr_fb.config(text="")
        if listen:
            self.pr_v.config(text=AUDIO_ICON+"  Listen…")
            self.pr_vh.config(text=verb[0] if self.prog.get("listen_hint", True)
                              else "type each word you hear")
            self.pr_hint.config(text="Enter Check    Space Hear again    ↑↓ Move    Esc Options")
        else:
            self.pr_v.config(text=verb[0]); self.pr_vh.config(text="")
            self.pr_hint.config(text="Enter Next field / Check    ↑↓ Move    Esc Options")

        for ww in self.pr_ff.winfo_children(): ww.destroy()
        self.entries = {}; self.phrases = {}; self.icons = {}; self._audio = {}
        # listening: the forms come in shuffled order, unlabeled
        self.cur_cols = (random.sample(self.cols, len(self.cols)) if listen
                         else list(self.cols))
        n = len(self.cur_cols); pad = max(6, 26//n)

        idx_map = {"base":1,"past":2,"part":3}
        for col in self.cur_cols:
            ans = self._pick_answer(verb[idx_map[col]])
            fw = tk.Frame(self.pr_ff, bg=C["BG"])

            if listen:
                self.phrases[col] = {"s": None, "a": ans}
                row = tk.Frame(fw, bg=C["BG"]); row.pack()
                ic = tk.Label(row, text=AUDIO_ICON, font=(self.FF,13,"bold"),
                              bg=C["BG"], fg=C["ACC_D"], cursor="hand2", width=19)
                ic.pack(side="left", padx=(0,6))
                ic.bind("<Button-1>", lambda _,c=col: self._play_col(c))
                e = self._mk_entry(row); e.pack(side="left")
                e.bind("<FocusIn>", lambda _,c=col: self._play_col(c))
                # Replay on Space, intercepted at the widget level so the Entry
                # class binding never inserts a literal space (answers are single
                # words, so Space is free to mean "hear it again" here).
                e.bind("<space>", lambda _,c=col: (self._play_col(c), "break")[1])
                self.icons[col] = ic
            else:
                # Reading: cached sentence for the picked answer, else any answer.
                sentences = self.cache.get(verb[1], col, ans)
                if not sentences:
                    fb_ans, fb_sent = self.cache.get_any(verb[1], col)
                    if fb_ans: ans, sentences = fb_ans, fb_sent
                phrase = random.choice(sentences) if sentences else None
                self.phrases[col] = {"s": phrase, "a": ans}
                lbl_text = next(l for k,l,_ in COLS if k==col)
                if phrase:
                    parts = phrase.split("___", 1)
                    self._lbl(fw, lbl_text, 9, C["FG3"]).pack(anchor="center")
                    row = tk.Frame(fw, bg=C["BG"]); row.pack()
                    if parts[0].strip():
                        self._lbl(row, parts[0], 13, C["FG2"]).pack(side="left")
                    e = self._mk_entry(row); e.pack(side="left", padx=4)
                    after = parts[1] if len(parts) > 1 else ""
                    if after.strip():
                        self._lbl(row, after, 13, C["FG2"]).pack(side="left")
                else:
                    self._lbl(fw, lbl_text, 10, C["FG3"]).pack()
                    e = self._mk_entry(fw); e.pack(pady=3)

            self.entries[col] = e
            fw.pack(expand=True, pady=pad)

        self._preload_audio()
        if self.cur_cols: self.entries[self.cur_cols[0]].focus_set()
        self._collect_fonts(self.pr_ff); self._scale_fonts()

    def _preload_audio(self):
        """Resolve the audio file for each answer word (instant when cached)."""
        if not audio.TTS_OK: return
        voice = self._get_voice()
        for col, obj in self.phrases.items():
            ans = obj.get("a") or ""
            if not ans: continue
            path = audio.get_cached(ans, voice)
            if path:
                self._audio[col] = path
                continue
            def gen(c=col, t=ans, v=voice):
                try: self._audio[c] = audio.ensure(t, v)
                except Exception: pass
            threading.Thread(target=gen, daemon=True).start()

    def _play_col(self, col, tries=10, token=None):
        """Play the audio for a column; retry briefly while TTS generates."""
        if not audio.TTS_OK: return
        if token is None: token = self._vt
        if token != self._vt or self.screen != "prac": return
        path = self._audio.get(col)
        if path:
            audio.play_path(path)
        elif tries > 0:
            self.win.after(350, lambda: self._play_col(col, tries-1, token))

    def _mk_entry(self, parent):
        C = self.C
        return tk.Entry(parent, font=(self.FF,13), width=13,
                        bg=C["ENTRY"], fg=C["FG"], insertbackground=C["FG"],
                        disabledbackground=C["ENTRY"], justify="center",
                        bd=0, highlightthickness=1,
                        highlightbackground=C["BORDER"], highlightcolor=C["ACC"],
                        relief="flat")

    def _focused_col(self):
        es = [self.entries[k] for k in self.cur_cols if k in self.entries]
        f = self.win.focus_get()
        if f in es: return self.cur_cols[es.index(f)]
        return self.cur_cols[0] if self.cur_cols else None

    def _mv(self, d):
        if self.locked: return
        es = [self.entries[k] for k in self.cur_cols if k in self.entries]
        f = self.win.focus_get()
        if f not in es:
            if es: es[0].focus_set()
            return
        i = es.index(f) + d
        if 0 <= i < len(es): es[i].focus_set()

    def _pr_enter(self):
        if self.locked:
            # skip the feedback wait
            if self.fb_id: self.win.after_cancel(self.fb_id); self.fb_id = None
            self._advance(); return
        es = [self.entries[k] for k in self.cur_cols if k in self.entries]
        f = self.win.focus_get()
        if f not in es:
            if es: es[0].focus_set()
            return
        i = es.index(f); col = self.cur_cols[i]
        got = " ".join(es[i].get().split()).lower()
        if got in self._expected_set(col):
            if self._mode() == "listen" and col in self.icons:
                # reveal the meaning of this exact form immediately
                self.icons[col].config(text=self._meaning(col), fg=self.C["GREEN"])
            elif audio.TTS_OK:
                audio.play_path(self._audio.get(col))
        if i < len(es)-1: es[i+1].focus_set()
        else: self._validate()

    def _validate(self):
        C = self.C; bad = []
        listen = self._mode() == "listen"
        for col in self.cur_cols:
            e = self.entries[col]
            got = " ".join(e.get().split()).lower()
            ok = got in self._expected_set(col)
            if ok:
                e.config(highlightbackground=C["GREEN"], highlightcolor=C["GREEN"],
                         disabledforeground=C["GREEN"])
            else:
                bad.append(self._expected_main(col))
                if listen:
                    # show the word you should have heard, right in the field
                    e.delete(0, "end"); e.insert(0, self._expected_main(col))
                e.config(highlightbackground=C["RED"], highlightcolor=C["RED"],
                         disabledforeground=C["RED"])
            e.config(state="disabled")
            if listen and col in self.icons:
                # reveal the conjugated Spanish meaning of this form
                self.icons[col].config(text=self._meaning(col),
                                       fg=C["GREEN"] if ok else C["RED"])
        self.locked = True
        if bad:
            self.bad_n += 1; self.blk_bad += 1; self.streak = 0
            fb = "✗" if listen else "✗   " + "  ·  ".join(bad)
            self.pr_fb.config(text=fb, fg=C["RED"])
            delay = FEED_BAD
        else:
            self.ok_n += 1; self.blk_ok += 1; self.streak += 1
            self.pr_fb.config(text="✓  Correct!", fg=C["GREEN"])
            delay = FEED_OK
        self.fb_id = self.win.after(delay, self._advance)

    def _advance(self):
        self.fb_id = None; self.locked = False
        self.vidx += 1; self._load_verb()

    # ── Block / Finish screens ────────────────────────────────────────────────
    def _blk_done(self):
        done = self._starts[self.bidx] + len(self._cur_block())
        self._set_comp(max(self._comp(), done))
        if self.bidx + 1 >= len(self.sblocks): self._show_fin(); return
        self.bi = 0; self._show("blk"); self._draw_blk()

    def _acc_text(self, ok, bad):
        tot = ok + bad
        if not tot: return ""
        return f"✓ {ok}    ✗ {bad}    ·    {round(100*ok/tot)}% accuracy"

    def _bld_blk(self):
        f = self.fr["blk"]; C = self.C
        self._lbl(f,"Block completed!",20,C["FG"],bold=True).place(relx=.5,rely=.16,anchor="center")
        self.blk_p = self._lbl(f,"",13); self.blk_p.place(relx=.5,rely=.28,anchor="center")
        self.blk_a = self._lbl(f,"",13); self.blk_a.place(relx=.5,rely=.37,anchor="center")
        self.blk_rows = []
        for i,y in enumerate((.53,.63,.73)):
            l = self._lbl(f,"",14,cursor="hand2",anchor="w")
            l.place(relx=.34,rely=y,anchor="w"); self.blk_rows.append(l)
            l.bind("<Button-1>", lambda _,i=i: self._click_blk(i))
            l.bind("<Enter>", lambda _,i=i: self._hover_blk(i))
        self._hint(f,"↑↓ Navigate      Enter Select      Esc Menu")

    def _hover_blk(self, i):
        if self.screen=="blk" and self.bi != i: self.bi=i; self._draw_blk()

    def _draw_blk(self):
        C = self.C
        total = sum(len(b) for b in self.sblocks)
        self.blk_p.config(text=f"Progress:  {min(self._comp(),total)} / {total}")
        self.blk_a.config(text=self._acc_text(self.blk_ok, self.blk_bad), fg=C["FG2"])
        for i,(l,txt) in enumerate(zip(self.blk_rows,
                ["Continue to next block","Repeat this block","Back to menu"])):
            l.config(text=(PTR+txt) if i==self.bi else txt,
                     fg=C["FG"] if i==self.bi else C["FG2"])

    def _sel_blk(self):
        if   self.bi==0: self._start_block(self.bidx+1)
        elif self.bi==1: self._start_block(self.bidx)
        else: self._show("menu"); self._draw_menu()

    def _click_blk(self, i): self.bi=i; self._draw_blk(); self._sel_blk()

    def _bld_fin(self):
        f = self.fr["fin"]; C = self.C
        self._lbl(f,"★  All verbs completed!",20,C["FG"],bold=True).place(relx=.5,rely=.18,anchor="center")
        self.fin_p = self._lbl(f,"",13); self.fin_p.place(relx=.5,rely=.32,anchor="center")
        self.fin_a = self._lbl(f,"",13); self.fin_a.place(relx=.5,rely=.41,anchor="center")
        self.fin_rows = []
        for i,y in enumerate((.57,.68)):
            l = self._lbl(f,"",14,cursor="hand2",anchor="w")
            l.place(relx=.34,rely=y,anchor="w"); self.fin_rows.append(l)
            l.bind("<Button-1>", lambda _,i=i: self._click_fin(i))
            l.bind("<Enter>", lambda _,i=i: self._hover_fin(i))
        self._hint(f,"↑↓ Navigate      Enter Select      Esc Menu")

    def _hover_fin(self, i):
        if self.screen=="fin" and self.fi != i: self.fi=i; self._draw_fin()

    def _show_fin(self):
        self.fi = 0; self._show("fin"); self._draw_fin()

    def _draw_fin(self):
        C = self.C
        t = sum(len(b) for b in self.sblocks)
        self.fin_p.config(text=f"Progress:  {t} / {t}")
        self.fin_a.config(text="Session:  " + self._acc_text(self.ok_n, self.bad_n), fg=C["FG2"])
        for i,(l,txt) in enumerate(zip(self.fin_rows, ["Restart cycle","Back to menu"])):
            l.config(text=(PTR+txt) if i==self.fi else txt,
                     fg=C["FG"] if i==self.fi else C["FG2"])

    def _sel_fin(self):
        if self.fi==0: self._set_comp(0); self._open_setup()
        else: self._show("menu"); self._draw_menu()

    def _click_fin(self, i): self.fi=i; self._draw_fin(); self._sel_fin()

    # ── Keyboard dispatch ─────────────────────────────────────────────────────
    def _up(self, _):
        s = self.screen
        if   s=="menu":     self.mi=max(0,self.mi-1);              self._draw_menu()
        elif s=="setup":    self.si=max(0,self.si-1);              self._draw_setup()
        elif s=="words":
            if self.wd_carry: self._wd_carry_move(-1)
            else: self._wd_nav(-1)
        elif s=="prac":     self._mv(-1)
        elif s=="blk":      self.bi=max(0,self.bi-1);              self._draw_blk()
        elif s=="fin":      self.fi=max(0,self.fi-1);              self._draw_fin()
        elif s=="settings": self.sti=max(0,self.sti-1);            self._draw_settings()

    def _dn(self, _):
        s = self.screen
        if   s=="menu":     self.mi=min(2,self.mi+1);              self._draw_menu()
        elif s=="setup":    self.si=min(len(self.sr)-1,self.si+1); self._draw_setup()
        elif s=="words":
            if self.wd_carry: self._wd_carry_move(1)
            else: self._wd_nav(1)
        elif s=="prac":     self._mv(1)
        elif s=="blk":      self.bi=min(2,self.bi+1);              self._draw_blk()
        elif s=="fin":      self.fi=min(1,self.fi+1);              self._draw_fin()
        elif s=="settings": self.sti=min(3,self.sti+1);            self._draw_settings()

    def _lt(self, _):
        s = self.screen
        if s=="menu":
            self.mi=max(0,self.mi-1); self._draw_menu()
        elif s=="setup" and self.sr:
            r = self.sr[self.si]
            if r=="ab": self.sb=max(0,self.sb-1); self._draw_setup()
            elif r=="mode": self._toggle_mode()
        elif s=="words": self._wd_drop()

    def _rt(self, _):
        s = self.screen
        if s=="menu":
            self.mi=min(2,self.mi+1); self._draw_menu()
        elif s=="setup" and self.sr:
            r = self.sr[self.si]
            if r=="ab":
                tot=len(self._layout())
                self.sb=min(tot-1,self.sb+1); self._draw_setup()
            elif r=="mode": self._toggle_mode()
        elif s=="words": self._wd_pick()

    def _en(self, _):
        s = self.screen
        if   s=="menu":     self._menu_go()
        elif s=="setup":    self._sel_setup()
        elif s=="words":
            if self.wd_carry: self._wd_drop()
            else: self._wd_toggle()
        elif s=="prac":     self._pr_enter()
        elif s=="blk":      self._sel_blk()
        elif s=="fin":      self._sel_fin()
        elif s=="settings": self._sel_settings()

    def _sp(self, _):
        if self.screen=="setup": self._tog(); return "break"
        if self.screen=="words":
            if not self.wd_carry: self._wd_toggle()
            return "break"
        if self.screen=="prac" and self._mode()=="listen":
            col = self._focused_col()
            if col: self._play_col(col)
            return "break"

    def _ka(self, _):
        if self.screen=="words":
            if self.wd_rows and not self.wd_carry:
                self._wd_toggle_block(self.wd_rows[self.wi]["bi"])
            return "break"

    def _kn(self, _):
        if self.screen=="words":
            self._wd_new_dialog()
            return "break"

    def _kdel(self, _):
        if self.screen=="words":
            self._wd_delete()
            return "break"

    def _es(self, _):
        s = self.screen
        if   s=="prac":     self._exit_dialog(); return "break"
        elif s=="setup":    self._show("menu"); self._draw_menu()
        elif s=="words":
            if self.wd_carry: self._wd_drop()
            else: self._wd_done()
        elif s=="load":     self._show("setup"); self._draw_setup()
        elif s=="settings": self._show("menu"); self._draw_menu()
        elif s in ("blk","fin"): self._show("menu"); self._draw_menu()

    # ── Exit dialog (Escape during practice) ──────────────────────────────────
    def _exit_dialog(self):
        if self.fb_id: self.win.after_cancel(self.fb_id); self.fb_id = None
        C = self.C

        dlg = tk.Toplevel(self.win)
        dlg.title("Options"); dlg.transient(self.win)
        try: dlg.grab_set()
        except tk.TclError: pass
        dlg.resizable(False, False); dlg.config(bg=C["BG"], padx=24, pady=20)

        tk.Label(dlg, text="What would you like to do?", font=(self.FF,14,"bold"),
                 bg=C["BG"], fg=C["FG"]).pack(pady=(0,14))

        opts = [("reset","Restart block"),("menu","Back to menu"),("cancel","Cancel")]
        sel = [2]; labels = []
        btn_frame = tk.Frame(dlg, bg=C["BG"]); btn_frame.pack()

        def render():
            for i,(_, txt) in enumerate(opts):
                on = (i == sel[0])
                labels[i].config(
                    text=txt,
                    bg=C["SEL"] if on else C["CARD"],
                    fg=C["FG"] if on else C["FG2"],
                    highlightbackground=C["ACC"] if on else C["BORDER"])

        def choose(choice):
            dlg.destroy()
            if choice=="reset":
                self._start_block(self.bidx)
            elif choice=="menu":
                self.locked=False
                self._show("menu"); self._draw_menu()
            else:
                self._resume_practice()

        for i,(key,txt) in enumerate(opts):
            lbl = tk.Label(btn_frame, text=txt, font=(self.FF,12), bg=C["CARD"],
                           fg=C["FG2"], padx=16, pady=10, cursor="hand2",
                           highlightthickness=1, highlightbackground=C["BORDER"])
            lbl.grid(row=0, column=i, padx=6)
            lbl.bind("<Button-1>", lambda _,k=key: choose(k))
            labels.append(lbl)

        tk.Label(dlg, text="←→ Move    Enter Select    Esc Cancel",
                 font=(self.FF,9), bg=C["BG"], fg=C["FG3"]).pack(pady=(14,0))

        def mv(d): sel[0]=max(0,min(sel[0]+d,len(opts)-1)); render()
        dlg.bind("<Left>",   lambda _: mv(-1))
        dlg.bind("<Right>",  lambda _: mv(1))
        dlg.bind("<Return>", lambda _: choose(opts[sel[0]][0]))
        dlg.bind("<Escape>", lambda _: choose("cancel"))
        render()
        dlg.update_idletasks()
        x = self.win.winfo_rootx()+(self.win.winfo_width() -dlg.winfo_width()) //2
        y = self.win.winfo_rooty()+(self.win.winfo_height()-dlg.winfo_height())//2
        dlg.geometry(f"+{max(x,0)}+{max(y,0)}")
        dlg.focus_set(); dlg.wait_window()

    def _resume_practice(self):
        """Cancel-path from the dialog: re-arm feedback if we interrupted it."""
        if self.locked:
            self.fb_id = self.win.after(600, self._advance)
        else:
            es = [self.entries[k] for k in self.cur_cols if k in self.entries]
            if es: es[0].focus_set()

    # ── Responsive fonts ──────────────────────────────────────────────────────
    def _init_fonts(self):
        self._base_fonts = {}
        for fr in self.fr.values(): self._collect_fonts(fr)
        self._scale_fonts()

    def _collect_fonts(self, widget):
        try:
            fo = tkfont.Font(font=widget.cget("font"))
            if widget not in self._base_fonts:
                self._base_fonts[widget] = (fo.actual("family"), int(fo.actual("size")),
                                            fo.actual("weight"), fo.actual("slant"))
        except tk.TclError: pass
        for child in widget.winfo_children(): self._collect_fonts(child)

    def _scale_fonts(self):
        w = max(1, self.win.winfo_width()); h = max(1, self.win.winfo_height())
        scale = min(w/BASE_W, h/BASE_H)
        dead = []
        for widget,(fam,size,wgt,slant) in list(self._base_fonts.items()):
            try:
                if widget.winfo_exists():
                    widget.config(font=(fam, max(1,int(size*scale)), wgt, slant))
                else: dead.append(widget)
            except Exception: dead.append(widget)
        for widget in dead: self._base_fonts.pop(widget, None)

    def _on_resize(self, e):
        if e.widget is not self.win: return
        size = (e.width, e.height)
        if size == self._last_size: return
        self._last_size = size
        if self._resize_job: self.win.after_cancel(self._resize_job)
        self._resize_job = self.win.after(60, self._scale_fonts)

    def run(self): self.win.mainloop()
