#!/usr/bin/env python3
"""Verb Practice — practice English regular & irregular verbs.

Data files (next to this script):
  progress.json       progress, word selection / block layout, preferences
  phrases_cache.json  cached fill-in-the-blank sentences (Gemini)
  config.json         {"gemini_api_key": "..."}
"""
import tkinter as tk
import tkinter.font as tkfont
import random, json, threading, time
from pathlib import Path

try:
    from google import genai as _genai
    GEMINI_OK = True
except ImportError:
    GEMINI_OK = False

# ── Verb lists ────────────────────────────────────────────────────────────────
verbos_irregulares = [
    ["ser/estar","be","was-were","been"],["tener","have","had","had"],
    ["hacer","do","did","done"],["decir","say","said","said"],
    ["ir","go","went","gone"],["obtener","get","got","gotten"],
    ["hacer/crear","make","made","made"],["saber/conocer","know","knew","known"],
    ["pensar","think","thought","thought"],["tomar","take","took","taken"],
    ["ver","see","saw","seen"],["venir","come","came","come"],
    ["dar","give","gave","given"],["encontrar","find","found","found"],
    ["decir/contar","tell","told","told"],["convertirse","become","became","become"],
    ["mostrar","show","showed","shown"],["dejar/irse","leave","left","left"],
    ["sentir","feel","felt","felt"],["poner","put","put","put"],

    ["traer","bring","brought","brought"],["empezar","begin","began","begun"],
    ["mantener","keep","kept","kept"],["sostener","hold","held","held"],
    ["oír","hear","heard","heard"],["permitir","let","let","let"],
    ["significar","mean","meant","meant"],["establecer","set","set","set"],
    ["conocer/reunirse","meet","met","met"],["correr","run","ran","run"],
    ["pagar","pay","paid","paid"],["sentarse","sit","sat","sat"],
    ["hablar","speak","spoke","spoken"],["acostarse","lie","lay","lain"],
    ["liderar","lead","led","led"],["leer","read","read","read"],
    ["crecer","grow","grew","grown"],["perder","lose","lost","lost"],
    ["enviar","send","sent","sent"],["volar","fly","flew","flown"],

    ["vestir","wear","wore","worn"],["escribir","write","wrote","written"],
    ["beber","drink","drank","drunk"],["estar de pie","stand","stood","stood"],
    ["nadar","swim","swam","swum"],["cantar","sing","sang","sung"],
    ["gastar","spend","spent","spent"],["congelar","freeze","froze","frozen"],
    ["elevarse","rise","rose","risen"],["conducir","drive","drove","driven"],
    ["cortar","cut","cut","cut"],["caer","fall","fell","fallen"],
    ["construir","build","built","built"],["dibujar","draw","drew","drawn"],
    ["comprar","buy","bought","bought"],["entender","understand","understood","understood"],
    ["elegir","choose","chose","chosen"],["comer","eat","ate","eaten"],
    ["olvidar","forget","forgot","forgotten"],["romper","break","broke","broken"],

    ["robar","steal","stole","stolen"],["enseñar","teach","taught","taught"],
    ["lanzar","throw","threw","thrown"],["despertar","wake","woke","woken"],
    ["ganar","win","won","won"],["alimentar","feed","fed","fed"],
    ["atrapar","catch","caught","caught"],["soñar","dream","dreamt","dreamt"],
    ["quemar","burn","burnt","burnt"],["aprender","learn","learnt","learnt"],
    ["oler","smell","smelt","smelt"],["prestar","lend","lent","lent"],
    ["apostar","bet","bet","bet"],["costar","cost","cost","cost"],
    ["golpear fuerte","hit","hit","hit"],["herir","hurt","hurt","hurt"],
    ["cerrar","shut","shut","shut"],["extender","spread","spread","spread"],
    ["dividir","split","split","split"],["pelear","fight","fought","fought"],
]
verbos_regulares = [
    # Bloque 1 - Esenciales cotidianos
    ["querer","want","wanted"],["necesitar","need","needed"],
    ["gustar","like","liked"],["encantar","love","loved"],
    ["odiar","hate","hated"],["usar","use","used"],
    ["trabajar","work","worked"],["llamar","call","called"],
    ["preguntar","ask","asked"],["ayudar","help","helped"],
    ["intentar","try","tried"],["mirar","look","looked"],
    ["ver (mirar algo)","watch","watched"],["escuchar","listen","listened"],
    ["jugar","play","played"],["empezar","start","started"],
    ["parar","stop","stopped"],["terminar","finish","finished"],
    ["darse cuenta","realize","realized"],["vivir","live","lived"],

    # Bloque 2 - Acciones frecuentes
    ["quedarse","stay","stayed"],["hablar","talk","talked"],
    ["abrir","open","opened"],["cerrar","close","closed"],
    ["esperar","wait","waited"],["recordar","remember","remembered"],
    ["buscar","search","searched"],["cambiar","change","changed"],
    ["cocinar","cook","cooked"],["viajar","travel","traveled"],
    ["llegar","arrive","arrived"],["estar de acuerdo","agree","agreed"],
    ["explicar","explain","explained"],["creer","believe","believed"],
    ["mover","move","moved"],["imaginar","imagine","imagined"],
    ["decidir","decide","decided"],["disfrutar","enjoy","enjoyed"],
    ["evitar","avoid","avoided"],["practicar","practice","practiced"],

    # Bloque 3 - Acciones de organización y vida diaria
    ["planear","plan","planned"],["aceptar","accept","accepted"],
    ["recibir","receive","received"],["escribir mensaje","text","texted"],
    ["arreglar","fix","fixed"],["cancelar","cancel","canceled"],
    ["pasar","pass","passed"],["fallar","fail","failed"],
    ["tener éxito","succeed","succeeded"],["gestionar","manage","managed"],
    ["unirse","join","joined"],["apoyar","support","supported"],
    ["llevar","carry","carried"],["preparar","prepare","prepared"],
    ["incluir","include","included"],["guardar","save","saved"],
    ["lavar","wash","washed"],["revisar","review","reviewed"],
    ["verificar","check","checked"],["proteger","protect","protected"],

    # Bloque 4 - Acciones técnicas y comunicación
    ["cubrir","cover","covered"],["reducir","reduce","reduced"],
    ["aumentar","increase","increased"],["grabar","record","recorded"],
    ["anotar","note","noted"],["comparar","compare","compared"],
    ["diseñar","design","designed"],["comunicar","communicate","communicated"],
    ["organizar","organize","organized"],["describir","describe","described"],
    ["discutir","discuss","discussed"],["mencionar","mention","mentioned"],
    ["notar","notice","noticed"],["sugerir","suggest","suggested"],
    ["adivinar","guess","guessed"],["ordenar/pedir","order","ordered"],
    ["recordar a alguien","remind","reminded"],["responder","answer","answered"],
    ["preferir","prefer","preferred"],["visitar","visit","visited"],
]

# Alternative spellings that are also correct answers (both directions).
ALT_FORMS = {
    "dreamt":("dreamed",), "dreamed":("dreamt",),
    "burnt":("burned",),   "burned":("burnt",),
    "learnt":("learned",), "learned":("learnt",),
    "smelt":("smelled",),  "smelled":("smelt",),
    "gotten":("got",),
    "canceled":("cancelled",), "cancelled":("canceled",),
    "traveled":("travelled",), "travelled":("traveled",),
    "practiced":("practised",), "practised":("practiced",),
    "realized":("realised",),   "realised":("realized",),
    "organized":("organised",), "organised":("organized",),
}

# ── Constants ─────────────────────────────────────────────────────
THEMES = {
    "light": dict(BG="#F4F7FA", CARD="#FFFFFF", HOVER="#EAF1F5", SEL="#E3F2F1",
                  FG="#101826", FG2="#4A5568", FG3="#93A0B4", BORDER="#DFE7EE",
                  ACC="#0E9F9F", ACC_D="#0B7E7E", RED="#DC2626", GREEN="#15913B",
                  ENTRY="#FFFFFF", TRACK="#E2E8F0"),
    "dark":  dict(BG="#0F172A", CARD="#1B2437", HOVER="#243149", SEL="#12403C",
                  FG="#E7ECF4", FG2="#A8B2C3", FG3="#67748B", BORDER="#2B3752",
                  ACC="#2DD4BF", ACC_D="#14B8A6", RED="#F87171", GREEN="#4ADE80",
                  ENTRY="#111B31", TRACK="#26324B"),
}
PTR = "▶ "
BLOCK = 20
FEED_OK  = 650    # ms feedback when everything is correct
FEED_BAD = 2400   # ms feedback when something is wrong (Enter skips)
BASE_W, BASE_H = 780, 560

PROG_F = Path(__file__).with_name("progress.json")
PHRA_F = Path(__file__).with_name("phrases_cache.json")
CONF_F = Path(__file__).with_name("config.json")

VOICES = [("en-US-AriaNeural", "Aria (Female)"), ("en-US-GuyNeural", "Guy (Male)")]
COLS   = [("base","Base form",1), ("past","Past simple",2), ("part","Past participle",3)]
CATS   = {
    "regular":   {"title":"Regular verbs",   "verbs":verbos_regulares,   "has_part":False},
    "irregular": {"title":"Irregular verbs", "verbs":verbos_irregulares, "has_part":True},
}
SPIN = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]


# ── TTS helpers ───────────────────────────────────────────────────────────────
try:
    import edge_tts as _edge_tts
    import pygame as _pygame
    import os as _os, tempfile as _tempfile
    _pygame.mixer.init()
    TTS_OK = True
except Exception:
    TTS_OK = False

def _tts_generate(text, voice):
    """Generate TTS and return mp3 bytes. Runs in its own thread."""
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

def _tts_play(data):
    """Play mp3 bytes via a temp file."""
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


# ── Phrase cache ──────────────────────────────────────────────────────────────
# Cache key: "verb|col|answer"  e.g. "go|past|went", "be|past|was"
# Value: list of sentence strings with ___ placeholder
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


# ── App ───────────────────────────────────────────────────────────────────────
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
        self._audio = {}   # col -> mp3 bytes (pre-generated)

        # session state
        self.cat = "regular"; self.cols = ["base","past"]
        self.cst = {"base":True,"past":True,"part":False}
        self.sblocks = []; self._starts = []
        self.bidx = self.vidx = 0
        self.ok_n = self.bad_n = self.blk_ok = self.blk_bad = 0
        self.phrases = {}; self.entries = {}; self.fb_id = None
        self.locked = False
        # per-screen cursors
        self.mi = self.si = self.sb = self.bi = self.fi = self.sti = self.li = self.wi = 0
        self.sr = []; self._pending = None; self._then = None
        self._anim_i = 0; self.screen = "menu"
        self._last_size = (0,0); self._resize_job = None

        self._build()
        for key, fn in [("<Up>",self._up),("<Down>",self._dn),("<Left>",self._lt),
                        ("<Right>",self._rt),("<Return>",self._en),
                        ("<space>",self._sp),("<Escape>",self._es),
                        ("<Key-a>",self._ka)]:
            w.bind(key, fn)
        w.bind("<Configure>", self._on_resize)
        self._init_fonts()
        self._show("menu"); self._draw_menu()

    # ── Lifecycle / misc ──────────────────────────────────────────────────────
    def _on_close(self):
        if TTS_OK:
            try: _pygame.mixer.quit()
            except Exception: pass
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
        if not obj.get("s"):
            # no sentence context: any listed form (was/were) is acceptable
            for p in self._answer_parts(raw):
                ok.add(p); ok.update(ALT_FORMS.get(p, ()))
        return ok

    def _expected_main(self, col):
        obj = self.phrases.get(col) or {}
        if obj.get("a"): return obj["a"]
        idx_map = {"base":1,"past":2,"part":3}
        return self._cur_verb()[idx_map[col]]

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
        for cat in CATS:
            p = d.get(cat)
            if not isinstance(p, dict): p = {"completed":0}
            p["completed"] = int(p.get("completed",0) or 0)
            d[cat] = p
        d.setdefault("voice", "en-US-AriaNeural")
        d.setdefault("theme", "light")
        return d

    def _save_prog(self):
        try: PROG_F.write_text(json.dumps(self.prog, indent=2, ensure_ascii=False), "utf-8")
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
        try:
            d = json.loads(CONF_F.read_text("utf-8"))
            k = str(d.get("gemini_api_key","")).strip()
            if k and k != "PONER_LA_KEY_AQUI": return k
        except Exception: pass
        return None

    def _get_voice(self): return self.prog.get("voice", "en-US-AriaNeural")
    def _set_voice(self, v): self.prog["voice"] = v; self._save_prog()

    # ── Word layout (blocks + enabled/disabled words) ─────────────────────────
    def _vdict(self, cat=None):
        return {v[1]: v for v in CATS[cat or self.cat]["verbs"]}

    def _layout(self, cat=None):
        """Blocks of verb base-names for a category; reconciled and persisted."""
        cat = cat or self.cat
        names = [v[1] for v in CATS[cat]["verbs"]]
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
        return [[vd[n] for n in blk if n not in ds] for blk in self._layout(cat)]

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
        self._lbl(parent, text, 9, self.C["FG3"]).place(relx=.5, rely=.97, anchor="center")

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
        total = len(CATS[cat]["verbs"]); en = self._enabled_count(cat)
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
        if not TTS_OK:
            self._lbl(f,"(voice disabled: edge-tts / pygame not installed)",10,C["RED"])\
                .place(relx=.5,rely=.78,anchor="center")
        for i,l in enumerate(self.st_rows):
            l.bind("<Button-1>", lambda _,i=i: self._click_settings(i))
        self._hint(f,"↑↓ Navigate      Enter Apply      Esc Back")

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
        self.su_t = self._lbl(f,"",18,C["FG"],bold=True); self.su_t.place(relx=.5,rely=.05,anchor="n")
        self.su_sub = self._lbl(f,"",10,C["FG3"]); self.su_sub.place(relx=.5,rely=.115,anchor="n")

        self._lbl(f,"Practice",10,C["FG3"]).place(relx=.16,rely=.20,anchor="w")
        self.su_base = self._lbl(f,"",13,cursor="hand2",anchor="w"); self.su_base.place(relx=.19,rely=.27,anchor="w")
        self.su_past = self._lbl(f,"",13,cursor="hand2",anchor="w"); self.su_past.place(relx=.19,rely=.345,anchor="w")
        self.su_part = self._lbl(f,"",13,cursor="hand2",anchor="w"); self.su_part.place(relx=.19,rely=.42,anchor="w")

        self._lbl(f,"Words",10,C["FG3"]).place(relx=.16,rely=.50,anchor="w")
        self.su_w = self._lbl(f,"",13,cursor="hand2",anchor="w"); self.su_w.place(relx=.19,rely=.57,anchor="w")

        self._lbl(f,"Start",10,C["FG3"]).place(relx=.16,rely=.65,anchor="w")
        self.su_c = self._lbl(f,"",13,cursor="hand2",anchor="w"); self.su_c.place(relx=.19,rely=.72,anchor="w")
        self.su_b = self._lbl(f,"",13,cursor="hand2",anchor="w"); self.su_b.place(relx=.19,rely=.795,anchor="w")
        self.su_bp = self._lbl(f,"",9,C["FG3"],anchor="w");        self.su_bp.place(relx=.23,rely=.845,anchor="w")
        self.su_n = self._lbl(f,"",13,cursor="hand2",anchor="w"); self.su_n.place(relx=.19,rely=.90,anchor="w")

        self.su_msg = self._lbl(f,"",10,C["RED"]); self.su_msg.place(relx=.5,rely=.945,anchor="center")
        self._hint(f,"Space Toggle    ↑↓ Move    ←→ Block    Enter Select    Esc Back")
        self.su_wm = {"col_base":self.su_base,"col_past":self.su_past,"col_part":self.su_part,
                      "words":self.su_w,"ac":self.su_c,"ab":self.su_b,"an":self.su_n}
        for k,ww in self.su_wm.items():
            ww.bind("<Button-1>", lambda _,k=k: self._click_setup(k))

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
        self.sr = ["col_base","col_past","col_part","words"]
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
        self.su_w.config(text=f"Edit word list   ({total}/{len(info['verbs'])} selected)")
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
        # rows not in sr get cleared pointer
        for r,ww in self.su_wm.items():
            if r not in self.sr and r=="ac": ww.config(text="")

    def _tog(self):
        r = self.sr[self.si]
        if not r.startswith("col_"): return
        k = r[4:]
        if k=="part" and not CATS[self.cat]["has_part"]: return
        if self.cst[k] and sum(self.cst.values())==1:
            self.su_msg.config(text="Select at least one form."); return
        self.su_msg.config(text=""); self.cst[k] = not self.cst[k]; self._draw_setup()

    def _sel_setup(self):
        r = self.sr[self.si]
        if r.startswith("col_"): self._tog()
        elif r=="words": self._open_words()
        elif r=="ac": self._start("continue")
        elif r=="ab": self._start("block")
        elif r=="an": self._start("new")

    def _click_setup(self, k):
        if k not in self.sr: return
        self.si = self.sr.index(k); self._draw_setup(); self._sel_setup()

    # ── Words screen (choose words + blocks) ──────────────────────────────────
    def _bld_words(self):
        f = self.fr["words"]; C = self.C
        self.wd_t = self._lbl(f,"",16,C["FG"],bold=True)
        self.wd_t.place(relx=.5,rely=.035,anchor="n")
        self.wd_sub = self._lbl(f,"",9,C["FG3"])
        self.wd_sub.place(relx=.5,rely=.095,anchor="n")

        self.wd_cv = tk.Canvas(f, bg=C["BG"], highlightthickness=0)
        self.wd_scr = tk.Scrollbar(f, orient="vertical", command=self.wd_cv.yview)
        self.wd_cv.config(yscrollcommand=self.wd_scr.set)
        self.wd_cv.place(relx=.06, rely=.15, relwidth=.86, relheight=.77)
        self.wd_scr.place(relx=.93, rely=.15, relwidth=.02, relheight=.77)
        self.wd_in = tk.Frame(self.wd_cv, bg=C["BG"])
        self.wd_win = self.wd_cv.create_window((0,0), window=self.wd_in, anchor="nw")
        self.wd_in.bind("<Configure>",
            lambda e: self.wd_cv.config(scrollregion=self.wd_cv.bbox("all") or (0,0,0,0)))
        self.wd_cv.bind("<Configure>",
            lambda e: self.wd_cv.itemconfig(self.wd_win, width=e.width))
        self._hint(f,"Space/Click Toggle    ↑↓ Move    ←→ Move word to prev/next block    A Toggle block    Esc Done")

    def _open_words(self):
        self.wd_t.config(text=f"{CATS[self.cat]['title'].upper()} — WORD LIST")
        self.wi = 0
        self._words_rebuild()
        self._show("words")

    def _words_rebuild(self, keep_name=None):
        C = self.C
        for ch in self.wd_in.winfo_children(): ch.destroy()
        self.wd_rows = []; self.wd_heads = {}
        vd, ds = self._vdict(), self._disabled()
        lay = self._layout()
        has_part = CATS[self.cat]["has_part"]

        for bi, blk in enumerate(lay):
            head = tk.Frame(self.wd_in, bg=C["BG"]); head.pack(fill="x", pady=(10 if bi else 2, 3))
            hl = tk.Label(head, text="", font=(self.FF,11,"bold"), bg=C["BG"], fg=C["ACC_D"])
            hl.pack(side="left", padx=(2,8))
            ha = tk.Label(head, text="[ toggle all ]", font=(self.FF,9), bg=C["BG"],
                          fg=C["FG3"], cursor="hand2")
            ha.pack(side="left")
            ha.bind("<Button-1>", lambda _,b=bi: self._wd_toggle_block(b))
            self.wd_heads[bi] = hl

            for name in blk:
                v = vd[name]
                row = tk.Frame(self.wd_in, bg=C["BG"], cursor="hand2")
                row.pack(fill="x", pady=1)
                forms = " · ".join(v[1:4] if has_part else v[1:3])
                l = tk.Label(row, text="", font=(self.FF,11), bg=C["BG"], anchor="w")
                l.pack(side="left", padx=(14,0))
                r = tk.Label(row, text=v[0], font=(self.FF,10), bg=C["BG"],
                             fg=C["FG3"], anchor="e")
                r.pack(side="right", padx=(0,14))
                rec = {"name":name,"bi":bi,"frame":row,"l":l,"r":r,"forms":forms}
                idx = len(self.wd_rows)
                for w in (row,l,r):
                    w.bind("<Button-1>", lambda _,i=idx: self._wd_click(i))
                self.wd_rows.append(rec)

        if keep_name:
            self.wi = next((i for i,r in enumerate(self.wd_rows)
                            if r["name"]==keep_name), 0)
        self.wi = max(0, min(self.wi, len(self.wd_rows)-1))
        self._wd_refresh_all()
        self._collect_fonts(self.wd_in); self._scale_fonts()
        self.wd_cv.yview_moveto(0)
        if keep_name: self.win.after(50, lambda: self._wd_scroll_to(self.wi))

    def _wd_refresh_all(self):
        ds = self._disabled(); lay = self._layout()
        for i in range(len(self.wd_rows)): self._wd_refresh_row(i)
        en_total = 0
        for bi, blk in enumerate(lay):
            en = sum(1 for n in blk if n not in ds); en_total += en
            self.wd_heads[bi].config(text=f"Block {bi+1}  —  {en}/{len(blk)} selected")
        self.wd_sub.config(text=f"{en_total} words selected  ·  "
                                f"{len(lay)} blocks  ·  changes are saved automatically")

    def _wd_refresh_row(self, i):
        C = self.C; rec = self.wd_rows[i]
        ds = self._disabled()
        on  = rec["name"] not in ds
        sel = (i == self.wi)
        bg  = C["SEL"] if sel else C["BG"]
        mark = "☑" if on else "☐"
        rec["frame"].config(bg=bg)
        rec["l"].config(text=f"{mark}  {rec['forms']}", bg=bg,
                        fg=(C["FG"] if sel else C["FG2"]) if on else C["FG3"])
        rec["r"].config(bg=bg, fg=C["FG2"] if sel else C["FG3"])

    def _wd_click(self, i):
        old = self.wi; self.wi = i
        self._wd_refresh_row(old); self._wd_refresh_row(i)
        self._wd_toggle()

    def _wd_toggle(self):
        if not self.wd_rows: return
        rec = self.wd_rows[self.wi]; ds = self._disabled()
        if rec["name"] in ds: ds.discard(rec["name"])
        else: ds.add(rec["name"])
        self._set_disabled(ds)
        self._wd_refresh_all()

    def _wd_toggle_block(self, bi):
        blk = self._layout()[bi]; ds = self._disabled()
        if any(n in ds for n in blk): ds.difference_update(blk)
        else: ds.update(blk)
        self._set_disabled(ds)
        self._wd_refresh_all()

    def _wd_move(self, d):
        """Move selected word to the previous/next block."""
        if not self.wd_rows: return
        rec = self.wd_rows[self.wi]; lay = self._layout()
        bi = rec["bi"]; tgt = bi + d
        if tgt < 0: return
        if tgt >= len(lay):
            if len(lay[bi]) <= 1: return          # would just recreate same block
            lay.append([])
        lay[bi].remove(rec["name"])
        lay[tgt].append(rec["name"])
        self._cat_prog()["layout"] = [b for b in lay if b]
        self._save_prog()
        self._words_rebuild(keep_name=rec["name"])

    def _wd_nav(self, d):
        if not self.wd_rows: return
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

    def _wd_done(self):
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

        self.ok_n = self.bad_n = 0
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
        # prefetch the next block in the background
        if self.key and GEMINI_OK and self.bidx+1 < len(self.sblocks):
            nxt = self._block_needed(self.sblocks[self.bidx+1])
            if nxt: self.cache.fetch(nxt, self.key, lambda _: None)

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
        self.pr_v.place(relx=.5, rely=.5, anchor="center")

        self.pr_ff = tk.Frame(f, bg=C["BG"])
        self.pr_ff.place(relx=.5, rely=.35, anchor="n", relwidth=.94, relheight=.50)
        self.pr_fb = self._lbl(f,"",13,C["GREEN"],bold=True)
        self.pr_fb.place(relx=.5,rely=.885,anchor="center")
        self._hint(f,"Enter Next field / Check    ↑↓ Move    Esc Options")

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
        self.locked = False
        blk = self._cur_block()
        if self.vidx >= len(blk): self._blk_done(); return

        C = self.C; verb = self._cur_verb()
        total = sum(len(b) for b in self.sblocks)
        done  = self._starts[self.bidx] + self.vidx
        self.pr_p.config(text=f"Block {self.bidx+1}/{len(self.sblocks)}   ·   "
                              f"Word {self.vidx+1}/{len(blk)}   ·   {done}/{total} total")
        self.pr_s.config(text=f"✓ {self.ok_n}    ✗ {self.bad_n}")
        self._draw_bar()
        self.pr_v.config(text=verb[0]); self.pr_fb.config(text="")

        for ww in self.pr_ff.winfo_children(): ww.destroy()
        self.entries = {}; self.phrases = {}; self._audio = {}
        n = len(self.cols); pad = max(6, 26//n)

        idx_map = {"base":1,"past":2,"part":3}
        for col in self.cols:
            # Pick an answer, then look for cached sentences for that answer.
            # If not found (e.g. picked "were" but only "was" cached), fall back.
            ans = self._pick_answer(verb[idx_map[col]])
            sentences = self.cache.get(verb[1], col, ans)
            if not sentences:
                fb_ans, fb_sent = self.cache.get_any(verb[1], col)
                if fb_ans: ans, sentences = fb_ans, fb_sent
            phrase = random.choice(sentences) if sentences else None
            self.phrases[col] = {"s": phrase, "a": ans}

            fw = tk.Frame(self.pr_ff, bg=C["BG"])
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

        if self.cols: self.entries[self.cols[0]].focus_set()
        self._collect_fonts(self.pr_ff); self._scale_fonts()
        self._preload_audio()

    def _preload_audio(self):
        """Pre-generate TTS for the answer word only."""
        if not TTS_OK: return
        voice = self._get_voice()
        for col, obj in self.phrases.items():
            ans = obj.get("a") or ""
            if not ans: continue
            def gen(c=col, t=ans, v=voice):
                try: self._audio[c] = _tts_generate(t, v)
                except Exception: pass
            threading.Thread(target=gen, daemon=True).start()

    def _mk_entry(self, parent):
        C = self.C
        return tk.Entry(parent, font=(self.FF,13), width=13,
                        bg=C["ENTRY"], fg=C["FG"], insertbackground=C["FG"],
                        disabledbackground=C["ENTRY"], justify="center",
                        bd=0, highlightthickness=1,
                        highlightbackground=C["BORDER"], highlightcolor=C["ACC"],
                        relief="flat")

    def _mv(self, d):
        if self.locked: return
        es = [self.entries[k] for k in self.cols if k in self.entries]
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
        es = [self.entries[k] for k in self.cols if k in self.entries]
        f = self.win.focus_get()
        if f not in es:
            if es: es[0].focus_set()
            return
        i = es.index(f); col = self.cols[i]
        got = " ".join(es[i].get().split()).lower()
        if got in self._expected_set(col) and TTS_OK:
            data = self._audio.get(col)
            if data: threading.Thread(target=_tts_play, args=(data,), daemon=True).start()
        if i < len(es)-1: es[i+1].focus_set()
        else: self._validate()

    def _validate(self):
        C = self.C; bad = []
        for col in self.cols:
            e = self.entries[col]
            got = " ".join(e.get().split()).lower()
            if got in self._expected_set(col):
                e.config(highlightbackground=C["GREEN"], highlightcolor=C["GREEN"],
                         disabledforeground=C["GREEN"])
            else:
                e.config(highlightbackground=C["RED"], highlightcolor=C["RED"],
                         disabledforeground=C["RED"])
                bad.append(self._expected_main(col))
            e.config(state="disabled")
        self.locked = True
        if bad:
            self.bad_n += 1; self.blk_bad += 1
            self.pr_fb.config(text="✗   " + "  ·  ".join(bad), fg=C["RED"])
            delay = FEED_BAD
        else:
            self.ok_n += 1; self.blk_ok += 1
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
        self._hint(f,"↑↓ Navigate      Enter Select      Esc Menu")

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
        self._lbl(f,"🎉  All verbs completed!",20,C["FG"],bold=True).place(relx=.5,rely=.18,anchor="center")
        self.fin_p = self._lbl(f,"",13); self.fin_p.place(relx=.5,rely=.32,anchor="center")
        self.fin_a = self._lbl(f,"",13); self.fin_a.place(relx=.5,rely=.41,anchor="center")
        self.fin_rows = []
        for i,y in enumerate((.57,.68)):
            l = self._lbl(f,"",14,cursor="hand2",anchor="w")
            l.place(relx=.34,rely=y,anchor="w"); self.fin_rows.append(l)
            l.bind("<Button-1>", lambda _,i=i: self._click_fin(i))
        self._hint(f,"↑↓ Navigate      Enter Select      Esc Menu")

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
        elif s=="words":    self._wd_nav(-1)
        elif s=="prac":     self._mv(-1)
        elif s=="blk":      self.bi=max(0,self.bi-1);              self._draw_blk()
        elif s=="fin":      self.fi=max(0,self.fi-1);              self._draw_fin()
        elif s=="settings": self.sti=max(0,self.sti-1);            self._draw_settings()

    def _dn(self, _):
        s = self.screen
        if   s=="menu":     self.mi=min(2,self.mi+1);              self._draw_menu()
        elif s=="setup":    self.si=min(len(self.sr)-1,self.si+1); self._draw_setup()
        elif s=="words":    self._wd_nav(1)
        elif s=="prac":     self._mv(1)
        elif s=="blk":      self.bi=min(2,self.bi+1);              self._draw_blk()
        elif s=="fin":      self.fi=min(1,self.fi+1);              self._draw_fin()
        elif s=="settings": self.sti=min(3,self.sti+1);            self._draw_settings()

    def _lt(self, _):
        s = self.screen
        if s=="menu":
            self.mi=max(0,self.mi-1); self._draw_menu()
        elif s=="setup" and self.sr and self.sr[self.si]=="ab":
            self.sb=max(0,self.sb-1); self._draw_setup()
        elif s=="words": self._wd_move(-1)

    def _rt(self, _):
        s = self.screen
        if s=="menu":
            self.mi=min(2,self.mi+1); self._draw_menu()
        elif s=="setup" and self.sr and self.sr[self.si]=="ab":
            tot=len(self._layout())
            self.sb=min(tot-1,self.sb+1); self._draw_setup()
        elif s=="words": self._wd_move(1)

    def _en(self, _):
        s = self.screen
        if   s=="menu":     self._menu_go()
        elif s=="setup":    self._sel_setup()
        elif s=="words":    self._wd_toggle()
        elif s=="prac":     self._pr_enter()
        elif s=="blk":      self._sel_blk()
        elif s=="fin":      self._sel_fin()
        elif s=="settings": self._sel_settings()

    def _sp(self, _):
        if self.screen=="setup": self._tog(); return "break"
        if self.screen=="words": self._wd_toggle(); return "break"

    def _ka(self, _):
        if self.screen=="words":
            if self.wd_rows: self._wd_toggle_block(self.wd_rows[self.wi]["bi"])
            return "break"

    def _es(self, _):
        s = self.screen
        if   s=="prac":     self._exit_dialog(); return "break"
        elif s=="setup":    self._show("menu"); self._draw_menu()
        elif s=="words":    self._wd_done()
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
                self._load_verb_resume()

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

    def _load_verb_resume(self):
        """Cancel-path from the dialog: re-arm feedback if we interrupted it."""
        if self.locked:
            self.fb_id = self.win.after(600, self._advance)
        else:
            es = [self.entries[k] for k in self.cols if k in self.entries]
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


if __name__ == "__main__":
    App().run()
