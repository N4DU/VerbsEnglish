"""Static data for Verb Practice: verb lists, themes and constants."""
from pathlib import Path

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

# ── Themes / constants ────────────────────────────────────────────────────────
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
AUDIO_ICON = "♫"  # BMP-safe: astral emoji don't render in some Tk builds

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
