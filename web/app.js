/* Verb Practice — web interface logic.
   Mirrors the desktop rules: listening reveals the Spanish meaning while you
   type (neutral colour, never leaking correctness), Space replays audio,
   Enter checks, wrong answers show the correct word in the field. */
"use strict";

const $ = (id) => document.getElementById(id);
const api = async (path, body) => {
  const r = await fetch(path, body === undefined ? {} : {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body)});
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json();
};

const COL_NAMES = {base: "Base form", past: "Past simple", part: "Past participle"};
const FEED_OK = 650, FEED_BAD = 2400;

let state = null;              // /api/state payload
let S = null;                  // current session
let audioEl = new Audio();

/* ── views ─────────────────────────────────────────────────────────────── */
function show(view) {
  for (const v of ["home", "setup", "practice", "done"])
    $("view-" + v).classList.toggle("hidden", v !== view);
}

function applyTheme() {
  document.documentElement.dataset.theme = state.theme;
}

/* ── home ──────────────────────────────────────────────────────────────── */
function renderHome() {
  const wrap = $("cat-cards"); wrap.innerHTML = "";
  for (const [cat, c] of Object.entries(state.cats)) {
    const pct = c.words_on ? Math.round(100 * c.completed / c.words_on) : 0;
    const el = document.createElement("div");
    el.className = "cat-card";
    el.innerHTML = `<h2>${c.title}</h2>
      <div class="sub">${c.words_on} of ${c.words_total} words on · ${c.blocks.length} blocks</div>
      <div class="bar"><div class="bar-fill" style="width:${pct}%"></div></div>
      <div class="pct">${c.completed}/${c.words_on} done</div>`;
    el.onclick = () => openSetup(cat);
    wrap.appendChild(el);
  }
  $("home-note").innerHTML =
    "The word &amp; block editor lives in the desktop app for now — run " +
    "<code>python main.py</code>. It is coming to the web next.";
  show("home");
}

/* ── setup ─────────────────────────────────────────────────────────────── */
const sel = {cat: null, mode: "read", forms: [], block: null};

function openSetup(cat) {
  sel.cat = cat;
  const c = state.cats[cat];
  sel.mode = (state.mode === "listen" && state.audio_ok) ? "listen" : "read";
  sel.forms = ["base", "past"].concat(c.has_part ? ["part"] : []);
  sel.block = null;                       // null = continue
  $("setup-title").textContent = c.title;
  renderSetup();
  show("setup");
}

function renderSetup() {
  const c = state.cats[sel.cat];
  for (const b of $("seg-mode").querySelectorAll("button")) {
    b.classList.toggle("on", b.dataset.mode === sel.mode);
    b.disabled = (b.dataset.mode === "listen" && !state.audio_ok);
    b.onclick = () => { sel.mode = b.dataset.mode; renderSetup(); };
  }
  const chips = $("form-chips"); chips.innerHTML = "";
  for (const f of ["base", "past", "part"]) {
    if (f === "part" && !c.has_part) continue;
    const b = document.createElement("button");
    b.textContent = COL_NAMES[f];
    b.classList.toggle("on", sel.forms.includes(f));
    b.onclick = () => {
      if (sel.forms.includes(f)) {
        if (sel.forms.length > 1) sel.forms = sel.forms.filter(x => x !== f);
      } else sel.forms.push(f);
      renderSetup();
    };
    chips.appendChild(b);
  }
  const bl = $("block-chips"); bl.innerHTML = "";
  const cont = document.createElement("button");
  cont.textContent = `Continue (${c.completed}/${c.words_on})`;
  cont.classList.toggle("on", sel.block === null);
  cont.onclick = () => { sel.block = null; renderSetup(); };
  bl.appendChild(cont);
  c.blocks.forEach((size, i) => {
    const b = document.createElement("button");
    b.textContent = `Block ${i + 1}`;
    b.title = `${size} words`;
    b.classList.toggle("on", sel.block === i);
    b.onclick = () => { sel.block = i; renderSetup(); };
    bl.appendChild(b);
  });
  $("setup-hint").textContent =
    sel.mode === "read"
      ? (state.has_key ? "Fill the blank in an AI-written sentence for each form."
                       : "No API key yet — reading works with blank fields. Add a key in Settings ⚙ or try Listening.")
      : "You hear each form in random order and type the word. The Spanish meaning appears as you type.";
  $("btn-start").textContent =
    sel.block === null ? "Continue practicing" : `Start block ${sel.block + 1}`;
}

async function startSession() {
  const body = {cat: sel.cat, mode: sel.mode, forms: sel.forms};
  if (sel.block !== null) body.start = sel.block;
  const s = await api("/api/session", body);
  S = {cat: sel.cat, mode: sel.mode, forms: sel.forms,
       sizes: s.sizes, block: s.start, total: s.total,
       ok: 0, bad: 0, streak: 0};
  await api("/api/settings", {mode: sel.mode});    // remember preference
  state.mode = sel.mode;
  await startBlock(S.block);
}

/* ── practice ──────────────────────────────────────────────────────────── */
async function startBlock(i) {
  S.block = i; S.idx = 0; S.blkOk = 0; S.blkBad = 0; S.locked = false;
  $("prompt-main").textContent = "…";
  $("prompt-sub").textContent = "Loading block…";
  $("prac-fields").innerHTML = ""; $("prac-feedback").textContent = "";
  show("practice");
  const r = await api("/api/block", {cat: S.cat, mode: S.mode,
                                     forms: S.forms, block: i});
  S.words = r.words;
  loadWord();
}

function blockStartOffset() {
  return S.sizes.slice(0, S.block).reduce((a, b) => a + b, 0);
}

function loadWord() {
  clearTimeout(S.timer); S.locked = false;
  if (S.idx >= S.words.length) { blockDone(); return; }
  const w = S.words[S.idx];
  const done = blockStartOffset() + S.idx;
  $("prac-pos").textContent =
    `Block ${S.block + 1}/${S.sizes.length} · Word ${S.idx + 1}/${S.words.length} · ${done}/${S.total} total`;
  let st = `✓ ${S.ok}   ✗ ${S.bad}`;
  if (S.streak >= 3) st += `   ·   ${S.streak} in a row!`;
  $("prac-stats").textContent = st;
  $("prac-bar").style.width = `${100 * S.idx / S.words.length}%`;
  $("prac-feedback").textContent = ""; $("prac-feedback").className = "";

  if (S.mode === "listen") {
    $("prompt-main").textContent = "♫  Listen…";
    $("prompt-sub").textContent =
      state.listen_hint ? w.es : "type each word you hear";
    $("prac-keys").textContent =
      "Enter Check · Space Hear again · ↑↓ Move · Esc Options";
  } else {
    $("prompt-main").textContent = w.es;
    $("prompt-sub").textContent = "";
    $("prac-keys").textContent = "Enter Next field / Check · ↑↓ Move · Esc Options";
  }

  const wrap = $("prac-fields"); wrap.innerHTML = "";
  w.fields.forEach((f, fi) => {
    const line = document.createElement("div");
    line.className = "fieldline";
    if (S.mode === "listen") {
      const play = document.createElement("button");
      play.className = "play-btn"; play.textContent = "♫";
      play.title = "Play (Space)";
      play.onclick = () => playWord(f.answer);
      const inp = mkInput(fi);
      inp.addEventListener("focus", () => playWord(f.answer));
      inp.addEventListener("input", () => {
        const m = line.querySelector(".meaning");
        m.textContent = inp.value.trim() ? f.meaning : "";
        m.className = "meaning";
      });
      const meaning = document.createElement("span");
      meaning.className = "meaning";
      line.append(play, inp, meaning);
    } else if (f.sentence) {
      const [before, after] = f.sentence.split("___");
      const lab = document.createElement("span");
      lab.className = "lab"; lab.textContent = COL_NAMES[f.col];
      const s1 = document.createElement("span");
      s1.className = "sent"; s1.textContent = before ?? "";
      const s2 = document.createElement("span");
      s2.className = "sent"; s2.textContent = after ?? "";
      line.append(lab, s1, mkInput(fi), s2);
    } else {
      const lab = document.createElement("span");
      lab.className = "lab"; lab.textContent = COL_NAMES[f.col];
      line.append(lab, mkInput(fi));
    }
    wrap.appendChild(line);
  });
  inputs()[0]?.focus();
}

function mkInput(fi) {
  const inp = document.createElement("input");
  inp.type = "text"; inp.dataset.fi = fi;
  inp.autocomplete = "off"; inp.spellcheck = false;
  return inp;
}
const inputs = () => [...$("prac-fields").querySelectorAll("input")];

function playWord(word) {
  if (!state.audio_ok) return;
  audioEl.pause();
  audioEl = new Audio("/api/audio/" + encodeURIComponent(word));
  audioEl.play().catch(() => {});
}

const norm = (s) => s.trim().toLowerCase().split(/\s+/).join(" ");

function onEnter() {
  if (S.locked) { clearTimeout(S.timer); advance(); return; }
  const es = inputs();
  const cur = document.activeElement;
  const i = es.indexOf(cur);
  if (i === -1) { es[0]?.focus(); return; }
  const f = S.words[S.idx].fields[i];
  if (S.mode === "read" && f.accept.includes(norm(cur.value))) playWord(f.answer);
  if (i < es.length - 1) es[i + 1].focus();
  else validate();
}

function validate() {
  const w = S.words[S.idx];
  const es = inputs();
  let bad = [];
  w.fields.forEach((f, i) => {
    const good = f.accept.includes(norm(es[i].value));
    es[i].classList.add(good ? "good" : "bad");
    es[i].disabled = true;
    if (!good) {
      bad.push(f.answer);
      if (S.mode === "listen") es[i].value = f.answer;
    }
    if (S.mode === "listen") {
      const m = es[i].closest(".fieldline").querySelector(".meaning");
      m.textContent = f.meaning;
      m.className = "meaning " + (good ? "good" : "bad");
    }
  });
  S.locked = true;
  const fb = $("prac-feedback");
  if (bad.length) {
    S.bad++; S.blkBad++; S.streak = 0;
    fb.textContent = S.mode === "listen" ? "✗" : "✗   " + bad.join("  ·  ");
    fb.className = "bad";
    S.timer = setTimeout(advance, FEED_BAD);
  } else {
    S.ok++; S.blkOk++; S.streak++;
    fb.textContent = "✓  Correct!";
    fb.className = "good";
    S.timer = setTimeout(advance, FEED_OK);
  }
}

function advance() { S.locked = false; S.idx++; loadWord(); }

async function blockDone() {
  const doneCount = blockStartOffset() + S.words.length;
  const c = state.cats[S.cat];
  const newComp = Math.max(c.completed, doneCount);
  await api("/api/progress", {cat: S.cat, completed: newComp});
  c.completed = Math.min(newComp, c.words_on);
  const last = S.block + 1 >= S.sizes.length;
  $("done-title").textContent = last ? "★  All verbs completed!" : "Block completed!";
  const t = S.blkOk + S.blkBad;
  $("done-stats").textContent =
    `✓ ${S.blkOk}   ✗ ${S.blkBad}` +
    (t ? `   ·   ${Math.round(100 * S.blkOk / t)}% accuracy` : "") +
    `   ·   ${Math.min(doneCount, S.total)}/${S.total} total`;
  $("btn-next").textContent = last ? "Start over from zero" : "Continue to next block";
  $("btn-next").onclick = async () => {
    if (last) { await api("/api/progress", {cat: S.cat, completed: 0});
                c.completed = 0; renderHome(); }
    else startBlock(S.block + 1);
  };
  show("done");
}

/* ── settings ──────────────────────────────────────────────────────────── */
function renderSettings() {
  const sv = $("seg-voice"); sv.innerHTML = "";
  for (const [id, label] of state.voices) {
    const b = document.createElement("button");
    b.textContent = label;
    b.classList.toggle("on", id === state.voice);
    b.onclick = async () => { state = await api("/api/settings", {voice: id});
                              renderSettings(); };
    sv.appendChild(b);
  }
  const st = $("seg-theme"); st.innerHTML = "";
  for (const t of state.themes) {
    const b = document.createElement("button");
    b.textContent = t === "light" ? "Light" : "Dark";
    b.classList.toggle("on", t === state.theme);
    b.onclick = async () => { state = await api("/api/settings", {theme: t});
                              applyTheme(); renderSettings(); };
    st.appendChild(b);
  }
  $("key-status").textContent = state.has_key
    ? "✓ A key is saved on this computer."
    : "No key saved — reading mode will use blank fields.";
  $("btn-key-remove").style.display = state.has_key ? "" : "none";
}

function wireSettings() {
  $("btn-settings").onclick = () => { renderSettings(); $("dlg-settings").showModal(); };
  $("btn-settings-close").onclick = () => $("dlg-settings").close();
  $("btn-key-save").onclick = async () => {
    const k = $("inp-key").value.trim();
    if (!k) return;
    state = await api("/api/settings", {gemini_key: k});
    $("inp-key").value = "";
    renderSettings(); renderHomeSoft();
  };
  $("btn-key-remove").onclick = async () => {
    state = await api("/api/settings", {gemini_key: ""});
    renderSettings(); renderHomeSoft();
  };
}
function renderHomeSoft() {
  if (!$("view-home").classList.contains("hidden")) renderHome();
  if (!$("view-setup").classList.contains("hidden")) renderSetup();
}

/* ── keyboard ──────────────────────────────────────────────────────────── */
function moveFocus(d) {
  const es = inputs();
  const i = es.indexOf(document.activeElement);
  const j = i === -1 ? 0 : i + d;
  if (j >= 0 && j < es.length) es[j].focus();
}

document.addEventListener("keydown", (ev) => {
  const practicing = !$("view-practice").classList.contains("hidden");
  if (!practicing) return;
  if (ev.key === "Enter") { ev.preventDefault(); onEnter(); }
  else if (ev.key === "ArrowDown") { ev.preventDefault(); if (!S.locked) moveFocus(1); }
  else if (ev.key === "ArrowUp") { ev.preventDefault(); if (!S.locked) moveFocus(-1); }
  else if (ev.key === " " && S.mode === "listen") {
    ev.preventDefault();
    const es = inputs();
    const i = Math.max(0, es.indexOf(document.activeElement));
    const f = S.words[S.idx]?.fields[i];
    if (f) playWord(f.answer);
  } else if (ev.key === "Escape") {
    clearTimeout(S.timer);
    $("dlg-quit").showModal();
  }
});

/* ── boot ──────────────────────────────────────────────────────────────── */
async function boot() {
  state = await api("/api/state");
  applyTheme();
  wireSettings();
  $("brand-home").onclick = () => renderHome();
  $("btn-start").onclick = () => startSession().catch(console.error);
  $("btn-restart").onclick = async () => {
    await api("/api/progress", {cat: sel.cat, completed: 0});
    state.cats[sel.cat].completed = 0;
    sel.block = null; renderSetup();
  };
  $("btn-repeat").onclick = () => startBlock(S.block);
  $("btn-home").onclick = () => renderHome();
  $("btn-quit-cancel").onclick = () => {
    $("dlg-quit").close();
    if (S?.locked) S.timer = setTimeout(advance, 600);
    else inputs()[0]?.focus();
  };
  $("btn-quit-restart").onclick = () => { $("dlg-quit").close(); startBlock(S.block); };
  $("btn-quit-home").onclick = () => { $("dlg-quit").close(); renderHome(); };
  renderHome();
}
boot().catch((e) => {
  document.body.insertAdjacentHTML("beforeend",
    `<p style="color:#dc2626">Could not reach the local server: ${e}</p>`);
});
