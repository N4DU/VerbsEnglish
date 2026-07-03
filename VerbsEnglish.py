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
    ["preferir","prefer","preferred"],["imaginar","imagine","imagined"],
]

# ── Constants ─────────────────────────────────────────────────────
BG   = "#F5FBFC"; BG_H = "#E6EEF2"; FG  = "#0F1723"; FG2 = "#4B5563"
FG3  = "#A3A3A3"; HL  = "#CBD5DF";  HL2 = "#0EA5A5"
RED  = "#DC2626"; OK  = "#16A34A";  PTR = "▶ "
BLOCK = 20; FEED = 500; BASE_W = 600; BASE_H = 380

PROG_F = Path(__file__).with_name("progress.json")
PHRA_F = Path(__file__).with_name("phrases_cache.json")
CONF_F = Path(__file__).with_name("config.json")

VOICES = [("en-US-AriaNeural", "Aria (Female)"), ("en-US-GuyNeural", "Guy (Male)")]
COLS   = [("base","Base form",1), ("past","Past simple",2), ("part","Past participle",3)]
CATS   = {
    "regular":   {"title":"REGULAR VERBS",   "verbs":verbos_regulares,   "has_part":False},
    "irregular": {"title":"IRREGULAR VERBS", "verbs":verbos_irregulares, "has_part":True},
}


# ── TTS helpers ───────────────────────────────────────────────────────────────────
try:
    import edge_tts as _edge_tts
    import pygame as _pygame
    import asyncio as _asyncio
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
    """Play mp3 bytes via a temp file (instant since bytes already in memory)."""
    try:
        with _tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(data); fname = f.name
        _pygame.mixer.music.load(fname)
        _pygame.mixer.music.play()
        import time
        while _pygame.mixer.music.get_busy(): time.sleep(0.04)
    except: pass
    finally:
        try: _os.unlink(fname)
        except: pass


# ── Phrase cache ──────────────────────────────────────────────────────────────────
# Cache key: "verb|col|answer"  e.g. "go|past|went", "be|past|was", "be|past|were"
# Value: list of sentence strings with ___ placeholder
class Cache:
    def __init__(self):
        self._lock = threading.Lock(); self._d = {}
        try:
            if PHRA_F.exists():
                d = json.loads(PHRA_F.read_text("utf-8"))
                if isinstance(d, dict): self._d = d
        except: pass

    def _save(self):
        try: PHRA_F.write_text(json.dumps(self._d, indent=2, ensure_ascii=False), "utf-8")
        except: pass

    def get(self, verb, col, answer):
        """Get cached sentences for a specific verb+col+answer."""
        with self._lock: return self._d.get(f"{verb}|{col}|{answer}")

    def has_any(self, verb, col):
        """True if ANY answer is cached for this verb+col."""
        prefix = f"{verb}|{col}|"
        with self._lock: return any(k.startswith(prefix) for k in self._d)

    def get_any(self, verb, col):
        """Return (answer, sentences) for any cached answer for this verb+col."""
        prefix = f"{verb}|{col}|"
        with self._lock:
            for k, v in self._d.items():
                if k.startswith(prefix):
                    return k[len(prefix):], v
        return None, None

    def put(self, verb, col, answer, sentences):
        with self._lock:
            self._d[f"{verb}|{col}|{answer}"] = sentences
            self._save()

    def fetch(self, needed, api_key, cb):
        """needed = [(verb_base, col, answer), ...]"""
        def run():
            if not GEMINI_OK: cb(None); return
            lines = "\n".join(
                f"- verb={v}, tense={c}, answer={a}" for v,c,a in needed
            )
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
                    resp = client.models.generate_content(model="models/gemini-2.5-flash", contents=prompt)
                    break
                except Exception as e:
                    if "503" in str(e) or "UNAVAILABLE" in str(e): time.sleep(5*(att+1))
                    else: cb(None); return
            if not resp: cb(None); return
            try:
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
            except: cb(None)
        threading.Thread(target=run, daemon=True).start()


# ── App ──────────────────────────────────────────────────────────────────────────────
class App:
    def __init__(self):
        w = self.win = tk.Tk()
        w.title("Verb Practice"); w.geometry("600x380")
        w.config(bg=BG); w.resizable(True, True)
        w.protocol("WM_DELETE_WINDOW", self._on_close)
        w.bind("<F8>", lambda _: w.attributes("-topmost", not w.attributes("-topmost")))

        self.cache  = Cache()
        self.prog   = self._load_prog()
        self.key    = self._load_key()
        self._audio = {}  # col -> mp3 bytes (pre-generated)

        self.cat = "regular"; self.verbs = []; self.cols = ["base","past"]
        self.cst = {"base":True,"past":True,"part":False}
        self.idx = self.blk_end = 0
        self.phrases = {}; self.entries = {}; self.fb_id = None
        self.mi = self.si = self.sb = self.bi = self.fi = self.sti = 0
        self.sr = []; self._pending = None; self._anim_i = 0; self.screen = "menu"

        self._build()
        for key, fn in [("<Up>",self._up),("<Down>",self._dn),("<Left>",self._lt),
                        ("<Right>",self._rt),("<Return>",self._en),
                        ("<space>",self._sp),("<Escape>",self._es),
                        ("<Configure>",self._on_resize)]:
            w.bind(key, fn)
        self._init_fonts()
        self._show("menu"); self._draw_menu()

    # ── Lifecycle ──────────────────────────────────────────────────────────────────────────
    def _on_close(self):
        if TTS_OK:
            try: _pygame.mixer.quit()
            except: pass
        self.win.destroy()

    # ── Answer picking ────────────────────────────────────────────────────────────────────────
    def _pick_answer(self, raw):
        """Pick one answer from verblist value. 'was-were' -> 'was' or 'were' randomly."""
        parts = [p.strip() for p in raw.replace("/", "-").split("-") if p.strip()]
        return random.choice(parts) if parts else raw.strip()

    # ── Progress / config ──────────────────────────────────────────────────────────────
    def _load_prog(self):
        try:
            if PROG_F.exists():
                d = json.loads(PROG_F.read_text("utf-8"))
                if isinstance(d, dict): return d
        except: pass
        return {"regular":{"completed":0},"irregular":{"completed":0},"voice":"en-US-AriaNeural"}

    def _save_prog(self):
        try: PROG_F.write_text(json.dumps(self.prog, indent=2), "utf-8")
        except: pass

    def _comp(self): return int(self.prog.get(self.cat,{}).get("completed",0))
    def _set_comp(self, n):
        self.prog[self.cat] = {"completed": max(0, min(n, len(self.verbs)))}
        self._save_prog()

    def _load_key(self):
        try:
            d = json.loads(CONF_F.read_text("utf-8"))
            k = str(d.get("gemini_api_key","")).strip()
            if k and k != "PONER_LA_KEY_AQUI": return k
        except: pass
        return None

    def _get_voice(self): return self.prog.get("voice", "en-US-AriaNeural")
    def _set_voice(self, v): self.prog["voice"] = v; self._save_prog()

    # ── UI build ──────────────────────────────────────────────────────────────────────────────
    def _build(self):
        self.fr = {n: tk.Frame(self.win, bg=BG)
                   for n in ["menu","setup","load","prac","blk","fin","settings"]}
        self._bld_menu(); self._bld_setup(); self._bld_load()
        self._bld_prac(); self._bld_blk(); self._bld_fin(); self._bld_settings()

    def _lbl(self, parent, text, size, fg=FG2, **kw):
        return tk.Label(parent, text=text, font=("Arial",size), bg=BG, fg=fg, **kw)

    def _bld_menu(self):
        f = self.fr["menu"]
        self._lbl(f,"ENGLISH PRACTICE",11,FG3).place(relx=.5,rely=.07,anchor="n")
        self._lbl(f,"What do you want to practice?",20,FG).place(relx=.5,rely=.22,anchor="n")
        self.m0 = self._lbl(f,"",15,anchor="w"); self.m0.place(relx=.28,rely=.44,anchor="w")
        self.m1 = self._lbl(f,"",15,anchor="w"); self.m1.place(relx=.28,rely=.57,anchor="w")
        self.m2 = self._lbl(f,"",14,FG3,anchor="w"); self.m2.place(relx=.28,rely=.70,anchor="w")
        self._lbl(f,"↑↓ Navigate   Enter Select",10,FG3).place(relx=.5,rely=.92,anchor="center")
        self.m0.bind("<Button-1>", lambda _: self._click_menu(0))
        self.m1.bind("<Button-1>", lambda _: self._click_menu(1))
        self.m2.bind("<Button-1>", lambda _: self._click_menu(2))

    def _bld_setup(self):
        f = self.fr["setup"]
        self.su_t = self._lbl(f,"",20,FG); self.su_t.place(relx=.5,rely=.05,anchor="n")
        self._lbl(f,"Select what to practice:",12).place(relx=.18,rely=.21,anchor="w")
        self.su_base = self._lbl(f,"",13,anchor="w"); self.su_base.place(relx=.23,rely=.32,anchor="w")
        self.su_past = self._lbl(f,"",13,anchor="w"); self.su_past.place(relx=.23,rely=.42,anchor="w")
        self.su_part = self._lbl(f,"",13,anchor="w"); self.su_part.place(relx=.23,rely=.52,anchor="w")
        self._lbl(f,"-"*30,9,FG3).place(relx=.5,rely=.62,anchor="center")
        self.su_c = self._lbl(f,"",13,anchor="w"); self.su_c.place(relx=.23,rely=.71,anchor="w")
        self.su_b = self._lbl(f,"",13,anchor="w"); self.su_b.place(relx=.23,rely=.80,anchor="w")
        self.su_n = self._lbl(f,"",13,anchor="w"); self.su_n.place(relx=.23,rely=.89,anchor="w")
        self.su_msg = self._lbl(f,"",10,RED); self.su_msg.place(relx=.5,rely=.96,anchor="center")
        self._lbl(f,"Space Toggle  ↑↓  ←→ Block  Enter  Esc Back",9,FG3).place(relx=.5,rely=.995,anchor="s")
        self.su_wm = {"col_base":self.su_base,"col_past":self.su_past,"col_part":self.su_part,
                      "ac":self.su_c,"ab":self.su_b,"an":self.su_n}
        for k,ww in self.su_wm.items():
            ww.bind("<Button-1>", lambda _,k=k: self._click_setup(k))

    def _bld_load(self):
        f = self.fr["load"]
        self._lbl(f,"Loading phrases...",20,FG).place(relx=.5,rely=.26,anchor="center")
        self.ld_msg = self._lbl(f,"Connecting to Gemini AI",13)
        self.ld_msg.place(relx=.5,rely=.44,anchor="center")
        self.ld_dot = self._lbl(f,"...",22,HL2); self.ld_dot.place(relx=.5,rely=.60,anchor="center")
        self.ld_err = self._lbl(f,"",11,RED); self.ld_err.place(relx=.5,rely=.74,anchor="center")
        self.ld_ret = self._lbl(f,"",13,HL2,cursor="hand2")
        self.ld_ret.place(relx=.5,rely=.87,anchor="center")

    def _bld_prac(self):
        f = self.fr["prac"]
        self.pr_p = self._lbl(f,"",10,FG3,anchor="w"); self.pr_p.place(relx=.03,rely=.035,anchor="w")
        self.pr_v = tk.Label(f,font=("Arial",28),bg=BG_H,fg=FG)
        self.pr_v.place(relx=.5,rely=.10,anchor="n",relwidth=1,relheight=.22)
        self.pr_ff = tk.Frame(f,bg=BG)
        self.pr_ff.place(relx=.5,rely=.34,anchor="n",relwidth=.97,relheight=.52)
        self.pr_fb = self._lbl(f,"",13,OK); self.pr_fb.place(relx=.5,rely=.89,anchor="center")
        self._lbl(f,"Enter: next field   ↑↓: move   Esc: options",9,FG3).place(relx=.5,rely=.97,anchor="center")

    def _bld_blk(self):
        f = self.fr["blk"]
        self._lbl(f,"Block completed!",22,FG).place(relx=.5,rely=.20,anchor="center")
        self.blk_p = self._lbl(f,"",14); self.blk_p.place(relx=.5,rely=.38,anchor="center")
        self.blk_c = self._lbl(f,"",14,anchor="w"); self.blk_c.place(relx=.28,rely=.56,anchor="w")
        self.blk_m = self._lbl(f,"",14,anchor="w"); self.blk_m.place(relx=.28,rely=.68,anchor="w")
        self.blk_c.bind("<Button-1>", lambda _: self._click_blk(0))
        self.blk_m.bind("<Button-1>", lambda _: self._click_blk(1))
        self._lbl(f,"↑↓ Navigate   Enter Select",10,FG3).place(relx=.5,rely=.92,anchor="center")

    def _bld_fin(self):
        f = self.fr["fin"]
        self._lbl(f,"All verbs completed!",22,FG).place(relx=.5,rely=.20,anchor="center")
        self.fin_p = self._lbl(f,"",14); self.fin_p.place(relx=.5,rely=.38,anchor="center")
        self.fin_r = self._lbl(f,"",14,anchor="w"); self.fin_r.place(relx=.28,rely=.56,anchor="w")
        self.fin_m = self._lbl(f,"",14,anchor="w"); self.fin_m.place(relx=.28,rely=.68,anchor="w")
        self.fin_r.bind("<Button-1>", lambda _: self._click_fin(0))
        self.fin_m.bind("<Button-1>", lambda _: self._click_fin(1))
        self._lbl(f,"↑↓ Navigate   Enter Select",10,FG3).place(relx=.5,rely=.92,anchor="center")

    def _bld_settings(self):
        f = self.fr["settings"]
        self._lbl(f,"SETTINGS",20,FG).place(relx=.5,rely=.10,anchor="n")
        self._lbl(f,"TTS Voice:",12).place(relx=.22,rely=.34,anchor="w")
        self.st0 = self._lbl(f,"",13,anchor="w"); self.st0.place(relx=.28,rely=.50,anchor="w")
        self.st1 = self._lbl(f,"",13,anchor="w"); self.st1.place(relx=.28,rely=.63,anchor="w")
        if not TTS_OK:
            self._lbl(f,"(edge-tts / pygame not installed)",10,RED).place(relx=.5,rely=.78,anchor="center")
        self.st0.bind("<Button-1>", lambda _: self._click_settings(0))
        self.st1.bind("<Button-1>", lambda _: self._click_settings(1))
        self._lbl(f,"↑↓ Navigate   Enter Select   Esc Back",9,FG3).place(relx=.5,rely=.92,anchor="center")

    def _show(self, name):
        for fr in self.fr.values(): fr.place_forget()
        self.fr[name].place(relwidth=1,relheight=1); self.screen = name

    # ── Keyboard ─────────────────────────────────────────────────────────────────────────────
    def _up(self, _):
        s = self.screen
        if   s=="menu":     self.mi=max(0,self.mi-1);               self._draw_menu()
        elif s=="setup":    self.si=max(0,self.si-1);               self._draw_setup()
        elif s=="prac":     self._mv(-1)
        elif s=="blk":      self.bi=max(0,self.bi-1);               self._draw_blk()
        elif s=="fin":      self.fi=max(0,self.fi-1);               self._draw_fin()
        elif s=="settings": self.sti=max(0,self.sti-1);             self._draw_settings()

    def _dn(self, _):
        s = self.screen
        if   s=="menu":     self.mi=min(2,self.mi+1);               self._draw_menu()
        elif s=="setup":    self.si=min(len(self.sr)-1,self.si+1);  self._draw_setup()
        elif s=="prac":     self._mv(1)
        elif s=="blk":      self.bi=min(1,self.bi+1);               self._draw_blk()
        elif s=="fin":      self.fi=min(1,self.fi+1);               self._draw_fin()
        elif s=="settings": self.sti=min(1,self.sti+1);             self._draw_settings()

    def _lt(self, _):
        if self.screen=="setup" and self.sr and self.sr[self.si]=="ab":
            self.sb=max(0,self.sb-1); self._draw_setup()

    def _rt(self, _):
        if self.screen=="setup" and self.sr and self.sr[self.si]=="ab":
            tot=max(1,(len(CATS[self.cat]["verbs"])+BLOCK-1)//BLOCK)
            self.sb=min(tot-1,self.sb+1); self._draw_setup()

    def _en(self, _):
        s = self.screen
        if   s=="menu":
            if   self.mi==0: self.cat="regular";   self._open_setup()
            elif self.mi==1: self.cat="irregular";  self._open_setup()
            else:            self._open_settings()
        elif s=="setup":    self._sel_setup()
        elif s=="prac":     self._pr_enter()
        elif s=="blk":      self._sel_blk()
        elif s=="fin":      self._sel_fin()
        elif s=="settings": self._sel_settings()

    def _sp(self, _):
        if self.screen=="setup": self._tog(); return "break"

    def _es(self, _):
        s = self.screen
        if s=="prac":     self._exit_dialog(); return "break"
        if s=="setup":    self._show("menu"); self._draw_menu()
        if s=="load":     self._show("setup"); self._draw_setup()
        if s=="settings": self._show("menu"); self._draw_menu()

    # ── Exit dialog (Escape during practice) ─────────────────────────────────────────────
    def _exit_dialog(self):
        if self.fb_id: self.win.after_cancel(self.fb_id); self.fb_id = None

        dlg = tk.Toplevel(self.win)
        dlg.title("Options"); dlg.transient(self.win); dlg.grab_set()
        dlg.resizable(False,False); dlg.config(bg=BG,padx=20,pady=20)

        tk.Label(dlg,text="What would you like to do?",font=("Arial",14),bg=BG,fg=FG).pack(pady=(0,14))

        opts = [("reset","Reset block"),("menu","Back to menu"),("cancel","Cancel")]
        sel  = [1]; labels = []

        btn_frame = tk.Frame(dlg,bg=BG); btn_frame.pack()

        def render():
            for i,(_, txt) in enumerate(opts):
                labels[i].config(
                    text=(PTR+txt) if i==sel[0] else txt,
                    bg=BG_H if i==sel[0] else BG,
                    fg=FG  if i==sel[0] else FG2,
                )

        def choose(choice):
            dlg.destroy()
            if choice=="reset":
                blk_start = (self.idx//BLOCK)*BLOCK
                self.idx = blk_start
                self.blk_end = min(blk_start+BLOCK, len(self.verbs))
                self._load_verb()
            elif choice=="menu":
                self._show("menu"); self._draw_menu()

        result = [None]
        for i,(key,txt) in enumerate(opts):
            lbl = tk.Label(btn_frame,text=txt,font=("Arial",12),bg=BG,fg=FG2,
                           padx=14,pady=10,bd=1,relief="solid")
            lbl.grid(row=0,column=i,padx=6)
            lbl.bind("<Button-1>", lambda _,k=key: choose(k))
            labels.append(lbl)

        tk.Label(dlg,text="←→ Move   Enter Select   Esc Cancel",
                 font=("Arial",9),bg=BG,fg=FG3).pack(pady=(14,0))

        def mv(d): sel[0]=max(0,min(sel[0]+d,len(opts)-1)); render()
        dlg.bind("<Left>",  lambda _: mv(-1))
        dlg.bind("<Right>", lambda _: mv(1))
        dlg.bind("<Return>",lambda _: choose(opts[sel[0]][0]))
        dlg.bind("<Escape>",lambda _: choose("cancel"))
        render()
        dlg.update_idletasks()
        x = self.win.winfo_rootx()+(self.win.winfo_width() -dlg.winfo_width()) //2
        y = self.win.winfo_rooty()+(self.win.winfo_height()-dlg.winfo_height())//2
        dlg.geometry(f"+{max(x,0)}+{max(y,0)}")
        dlg.focus_set(); dlg.wait_window()

    # ── Menu ────────────────────────────────────────────────────────────────────────────────
    def _draw_menu(self):
        for i,(ww,t) in enumerate([(self.m0,"Regular Verbs"),(self.m1,"Irregular Verbs"),(self.m2,"Settings")]):
            ww.config(text=(PTR+t) if i==self.mi else t)

    def _click_menu(self, i):
        self.mi=i; self._draw_menu()
        if i==0: self.cat="regular";  self._open_setup()
        elif i==1: self.cat="irregular"; self._open_setup()
        else: self._open_settings()

    # ── Settings ─────────────────────────────────────────────────────────────────────────────
    def _open_settings(self):
        cur = self._get_voice()
        self.sti = next((i for i,(k,_) in enumerate(VOICES) if k==cur), 0)
        self._show("settings"); self._draw_settings()

    def _draw_settings(self):
        cur = self._get_voice()
        for i,(k,lbl),(ww) in zip(range(2),VOICES,[self.st0,self.st1]):
            mark = "● " if k==cur else "○ "
            ww.config(text=(PTR+mark+lbl) if i==self.sti else (mark+lbl))

    def _sel_settings(self):
        k,_ = VOICES[self.sti]; self._set_voice(k); self._draw_settings()

    def _click_settings(self, i):
        self.sti=i; self._sel_settings()

    # ── Setup ────────────────────────────────────────────────────────────────────────────────
    def _open_setup(self):
        info = CATS[self.cat]
        self.cst = {"base":True,"past":True,"part":info["has_part"]}
        self.sb = self._comp()//BLOCK; self.su_msg.config(text="")
        self._build_sr()
        self.si = self.sr.index("ac") if "ac" in self.sr else self.sr.index("an")
        self._show("setup"); self._draw_setup()

    def _build_sr(self):
        has_c = 0 < self._comp() < len(CATS[self.cat]["verbs"])
        self.sr = ["col_base","col_past","col_part"]
        if has_c: self.sr.append("ac")
        self.sr += ["ab","an"]

    def _draw_setup(self):
        info=CATS[self.cat]; total=len(info["verbs"]); comp=self._comp()
        tblk=max(1,(total+BLOCK-1)//BLOCK)
        self.su_t.config(text=info["title"])
        def cb(ww,k,lbl,en):
            if not en: self.cst[k]=False
            m="[x]" if self.cst[k] else "[ ]"
            ww.config(text=f"{m} {lbl}"+("" if en else " (N/A)"),fg=FG2 if en else FG3)
        cb(self.su_base,"base","Base form",True)
        cb(self.su_past,"past","Past simple",True)
        cb(self.su_part,"part","Past participle",info["has_part"])
        self.su_c.config(text=f"Continue session ({comp}/{total})" if "ac" in self.sr else "")
        self.su_b.config(text=f"Choose block: < Block {self.sb+1}/{tblk} >")
        self.su_n.config(text="New session")
        for i,r in enumerate(self.sr):
            ww=self.su_wm[r]; t=ww.cget("text")
            if t.startswith(PTR): t=t[len(PTR):]
            ww.config(text=(PTR+t) if i==self.si else t)

    def _tog(self):
        r=self.sr[self.si]
        if not r.startswith("col_"): return
        k=r[4:]
        if k=="part" and not CATS[self.cat]["has_part"]: return
        if self.cst[k] and sum(self.cst.values())==1:
            self.su_msg.config(text="Select at least one."); return
        self.su_msg.config(text=""); self.cst[k]=not self.cst[k]; self._draw_setup()

    def _sel_setup(self):
        r=self.sr[self.si]
        if r.startswith("col_"): self._tog()
        elif r=="ac": self._start()
        elif r=="ab": self._start(start=self.sb*BLOCK)
        elif r=="an": self._start(new=True)

    def _click_setup(self, k):
        if k not in self.sr: return
        self.si=self.sr.index(k); self._draw_setup(); self._sel_setup()

    # ── Session start ────────────────────────────────────────────────────────────────────────
    def _start(self, new=False, start=None):
        sel=[k for k,_,_ in COLS if self.cst.get(k,False)]
        if not sel: self.su_msg.config(text="Select at least one."); return
        self.cols=sel
        orig=CATS[self.cat]["verbs"]; blks=[]
        for i in range(0,len(orig),BLOCK):
            b=orig[i:i+BLOCK].copy(); random.shuffle(b); blks.extend(b)
        self.verbs=blks
        if new: self._set_comp(0); self.idx=0
        elif start is not None: self.idx=max(0,min(start,len(self.verbs)-1))
        else: self.idx=self._comp()
        self.blk_end=min(self.idx+BLOCK,len(self.verbs))
        self._load_block()

    def _load_block(self):
        needed=[]
        idx_map={"base":1,"past":2,"part":3}
        for i in range(self.idx,self.blk_end):
            verb=self.verbs[i]
            for col in self.cols:
                if not self.cache.has_any(verb[1], col):
                    ans=self._pick_answer(verb[idx_map[col]])
                    needed.append((verb[1], col, ans))
        if not needed: self._begin(); return
        self._pending=needed
        self._show("load")
        self.ld_msg.config(text="Connecting to Gemini AI")
        self.ld_err.config(text=""); self.ld_ret.config(text="")
        self._anim_i=0; self._animate()
        self.cache.fetch(needed, self.key,
                         lambda r: self.win.after(0, lambda: self._fetch_done(r)))

    def _fetch_done(self, results):
        if self.screen!="load": return
        if results: self._begin()
        else:
            self.ld_msg.config(text="Could not load phrases.")
            self.ld_err.config(text="Check your API key and internet connection.")
            self.ld_ret.config(text="▶ Retry")
            self.ld_ret.bind("<Button-1>", lambda _: self._retry())

    def _retry(self):
        self.ld_err.config(text=""); self.ld_ret.config(text="")
        self.ld_msg.config(text="Retrying...")
        self._anim_i=0; self._animate()
        self.cache.fetch(self._pending,self.key,
                         lambda r: self.win.after(0,lambda: self._fetch_done(r)))

    def _animate(self):
        if self.screen!="load": return
        frames=[".  ",".. ","..."," .","  .","   "]
        self.ld_dot.config(text=frames[self._anim_i%len(frames)])
        self._anim_i+=1; self.win.after(200,self._animate)

    def _begin(self):
        self._show("prac"); self._load_verb()
        idx_map={"base":1,"past":2,"part":3}
        ns,ne=self.blk_end,min(self.blk_end+BLOCK,len(self.verbs))
        nxt=[]
        for i in range(ns,ne):
            verb=self.verbs[i]
            for col in self.cols:
                if not self.cache.has_any(verb[1], col):
                    ans=self._pick_answer(verb[idx_map[col]])
                    nxt.append((verb[1], col, ans))
        if nxt: self.cache.fetch(nxt, self.key, lambda _: None)

    # ── Practice ───────────────────────────────────────────────────────────────────────────────
    def _load_verb(self):
        if self.fb_id: self.win.after_cancel(self.fb_id); self.fb_id=None
        if self.idx>=self.blk_end: self._blk_done(); return

        verb=self.verbs[self.idx]
        self.pr_p.config(text=f"Verb {self.idx+1} / {len(self.verbs)}")
        self.pr_v.config(text=verb[0]); self.pr_fb.config(text="")

        for ww in self.pr_ff.winfo_children(): ww.destroy()
        self.entries={}; self.phrases={}; self._audio={}
        n=len(self.cols); pad=max(6,28//n)

        idx_map={"base":1,"past":2,"part":3}
        for col in self.cols:
            # Pick answer from verblist, then look for cached sentences for that answer.
            # If not found (e.g. picked "were" but only "was" cached), fall back to any.
            ans=self._pick_answer(verb[idx_map[col]])
            sentences=self.cache.get(verb[1], col, ans)
            if not sentences:
                fallback_ans, fallback_sentences = self.cache.get_any(verb[1], col)
                if fallback_ans:
                    ans, sentences = fallback_ans, fallback_sentences
            phrase=random.choice(sentences) if sentences else None
            self.phrases[col]={"s": phrase, "a": ans}

            fw=tk.Frame(self.pr_ff,bg=BG)
            lbl_text=next(l for k,l,_ in COLS if k==col)

            if phrase:
                parts=phrase.split("___",1)
                self._lbl(fw,lbl_text+":",9,FG3).pack(anchor="center")
                row=tk.Frame(fw,bg=BG); row.pack()
                if parts[0].strip():
                    self._lbl(row,parts[0],13,FG2).pack(side="left")
                e=self._mk_entry(row); e.pack(side="left",padx=4)
                after=parts[1] if len(parts)>1 else ""
                if after.strip():
                    self._lbl(row,after,13,FG2).pack(side="left")
            else:
                self._lbl(fw,lbl_text+":",11,FG2).pack()
                e=self._mk_entry(fw); e.pack(pady=3)

            self.entries[col]=e
            fw.pack(expand=True,pady=pad)

        if self.cols: self.entries[self.cols[0]].focus_set()
        self._collect_fonts(self.pr_ff); self._scale_fonts()
        self._preload_audio()

    def _preload_audio(self):
        """Pre-generate TTS for the answer word only."""
        if not TTS_OK: return
        voice=self._get_voice()
        for col,obj in self.phrases.items():
            ans=obj.get("a") or ""
            if not ans: continue
            col_s,ans_s=col,ans
            def gen(c=col_s,t=ans_s,v=voice):
                try: self._audio[c]=_tts_generate(t,v)
                except: pass
            threading.Thread(target=gen,daemon=True).start()

    def _mk_entry(self, parent):
        return tk.Entry(parent,font=("Arial",13),width=13,bg="white",fg=FG,
                        bd=0,highlightthickness=1,
                        highlightbackground=HL,highlightcolor=HL2,relief="flat")

    def _mv(self, d):
        es=[self.entries[k] for k in self.cols if k in self.entries]
        f=self.win.focus_get()
        if f not in es: (es[0].focus_set() if es else None); return
        i=es.index(f)+d
        if 0<=i<len(es): es[i].focus_set()

    def _get_expected(self, col):
        """Return the pre-chosen answer for this column. Single source of truth."""
        obj=self.phrases.get(col)
        if obj and obj.get("a"):
            return obj["a"].strip().lower()
        # absolute fallback: verblist (first option if compound)
        idx_map={"base":1,"past":2,"part":3}
        raw=self.verbs[self.idx][idx_map[col]].strip().lower()
        return self._pick_answer(raw)

    def _pr_enter(self):
        es=[self.entries[k] for k in self.cols if k in self.entries]
        f=self.win.focus_get()
        if f not in es: (es[0].focus_set() if es else None); return
        i=es.index(f); col=self.cols[i]
        got=es[i].get().strip().lower()
        exp=self._get_expected(col)
        if got==exp and TTS_OK:
            data=self._audio.get(col)
            if data: threading.Thread(target=_tts_play,args=(data,),daemon=True).start()
        if i<len(es)-1: es[i+1].focus_set()
        else: self._validate()

    def _validate(self):
        bad=[]
        for col in self.cols:
            e=self.entries[col]
            got=e.get().strip().lower()
            exp=self._get_expected(col)
            if got==exp: e.config(highlightbackground=HL2,highlightcolor=HL2)
            else:
                e.config(highlightbackground=RED,highlightcolor=RED)
                bad.append(exp)
            e.config(state="disabled")
        if bad: self.pr_fb.config(text=f"X  {' / '.join(bad)}",fg=RED)
        else:   self.pr_fb.config(text="Correct!",fg=OK)
        self.fb_id=self.win.after(FEED,self._advance)

    def _advance(self):
        self.fb_id=None; self.idx+=1; self._load_verb()

    # ── Block / Finish ──────────────────────────────────────────────────────────────────────────
    def _blk_done(self):
        self._set_comp(max(self._comp(),self.blk_end))
        if self.blk_end>=len(self.verbs): self._show_fin(); return
        self.bi=0; self._show("blk"); self._draw_blk()

    def _draw_blk(self):
        c=self._comp(); t=len(self.verbs)
        self.blk_p.config(text=f"Progress: {c} / {t}")
        self.blk_c.config(text=(PTR+"Continue") if self.bi==0 else "Continue")
        self.blk_m.config(text=(PTR+"Back to menu") if self.bi==1 else "Back to menu")

    def _sel_blk(self):
        if self.bi==0:
            self.idx=self._comp()
            self.blk_end=min(self.idx+BLOCK,len(self.verbs))
            self._load_block()
        else: self._show("menu"); self._draw_menu()

    def _click_blk(self,i): self.bi=i; self._draw_blk(); self._sel_blk()

    def _show_fin(self):
        self.fi=0; self._show("fin"); self._draw_fin()

    def _draw_fin(self):
        t=len(self.verbs); self.fin_p.config(text=f"Progress: {t} / {t}")
        self.fin_r.config(text=(PTR+"Restart cycle") if self.fi==0 else "Restart cycle")
        self.fin_m.config(text=(PTR+"Back to menu") if self.fi==1 else "Back to menu")

    def _sel_fin(self):
        if self.fi==0: self._set_comp(0); self._open_setup()
        else: self._show("menu"); self._draw_menu()

    def _click_fin(self,i): self.fi=i; self._draw_fin(); self._sel_fin()

    # ── Responsive fonts ───────────────────────────────────────────────────────────────────────
    def _init_fonts(self):
        self._base_fonts={}
        for fr in self.fr.values(): self._collect_fonts(fr)
        self._scale_fonts()

    def _collect_fonts(self, widget):
        try:
            fo=tkfont.Font(font=widget.cget("font"))
            self._base_fonts[widget]=(fo.actual("family"),int(fo.actual("size")),
                                       fo.actual("weight"),fo.actual("slant"))
        except tk.TclError: pass
        for child in widget.winfo_children(): self._collect_fonts(child)

    def _scale_fonts(self):
        w=max(1,self.win.winfo_width()); h=max(1,self.win.winfo_height())
        scale=min(w/BASE_W,h/BASE_H)
        for widget,(fam,size,wgt,slant) in list(self._base_fonts.items()):
            try:
                if widget.winfo_exists():
                    widget.config(font=(fam,max(1,int(size*scale)),wgt,slant))
            except: pass

    def _on_resize(self, _=None):
        self._scale_fonts()

    def run(self): self.win.mainloop()


if __name__ == "__main__":
    App().run()
