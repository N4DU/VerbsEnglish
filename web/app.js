/* Verb Practice — web interface.
   Full keyboard control on every screen, responsive layout, and visible
   (red) states for errors like a missing API key. Mouse/touch work too. */
"use strict";

const $ = (id) => document.getElementById(id);
const el = (tag, cls, txt) => { const e = document.createElement(tag);
  if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };

async function api(path, body) {
  const opt = body === undefined ? {}
    : {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)};
  const r = await fetch(path, opt);
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.json();
}
function toast(msg, ok) {
  const t = $("toast"); t.textContent = msg; t.className = "toast" + (ok ? " ok" : "");
  clearTimeout(t._t); t._t = setTimeout(() => t.classList.add("hidden"), 3200);
}

const COL = {base:"Base form", past:"Past simple", part:"Past participle"};
const FEED_OK = 650, FEED_BAD = 2400;

let state = null;     // /api/state
let screen = "home";
let S = null;         // practice session
let audioEl = new Audio();

/* ── view routing ──────────────────────────────────────────────────────── */
function show(name) {
  screen = name;
  for (const v of ["home","setup","editor","practice","done"])
    $("view-" + v).classList.toggle("hidden", v !== name);
}
function applyTheme() { document.documentElement.dataset.theme = state.theme; }

/* ═══════════════════════════ HOME ═══════════════════════════ */
let homeSel = 0;
function renderHome() {
  const cats = Object.entries(state.cats);
  const wrap = $("cat-cards"); wrap.innerHTML = "";
  cats.forEach(([cat, c], i) => {
    const pct = c.words_on ? Math.round(100*c.completed/c.words_on) : 0;
    const card = el("div", "cat-card");
    card.innerHTML =
      `<h2>${c.title}</h2>
       <div class="sub">${c.words_on} of ${c.words_total} words · ${c.blocks.length} blocks</div>
       <div class="bar"><div class="bar-fill" style="width:${pct}%"></div></div>
       <div class="pct">${c.completed}/${c.words_on} done</div>`;
    card.onclick = () => openSetup(cat);
    card.onmouseenter = () => { homeSel = i; markHome(); };
    wrap.appendChild(card);
  });
  $("home-keys").innerHTML =
    "<kbd>← →</kbd> choose · <kbd>Enter</kbd> start · <kbd>⚙</kbd> settings";
  markHome(); show("home");
}
function markHome() {
  [...$("cat-cards").children].forEach((c,i) => c.classList.toggle("on", i===homeSel));
}
function homeKeys(k) {
  const n = Object.keys(state.cats).length;
  if (k==="ArrowRight"||k==="ArrowDown") { homeSel=Math.min(n-1,homeSel+1); markHome(); }
  else if (k==="ArrowLeft"||k==="ArrowUp") { homeSel=Math.max(0,homeSel-1); markHome(); }
  else if (k==="Enter") openSetup(Object.keys(state.cats)[homeSel]);
}

/* ═══════════════════════════ SETUP ═══════════════════════════ */
const sel = {cat:null, mode:"read", forms:[], block:null};
let setupGrid = [], setupR = 0, setupC = 0;

function openSetup(cat) {
  sel.cat = cat;
  const c = state.cats[cat];
  sel.mode = (state.mode==="listen" && state.audio_ok) ? "listen" : "read";
  sel.forms = ["base","past"].concat(c.has_part ? ["part"] : []);
  sel.block = null;
  $("setup-title").textContent = c.title;
  setupR = null; setupC = 0;          // null → default the cursor to "Continue practicing"
  renderSetup(); show("setup");
}
/* Setup is a grid of focusable buttons: one row per setting, cells within it.
   ↑↓ walk between rows, ←→ walk within a row, Enter/Space clicks the cell —
   so the highlight always sits on exactly one control, never a whole line. */
function renderSetup() {
  const c = state.cats[sel.cat];
  const p = $("setup-panel"); p.innerHTML = ""; setupGrid = [];

  // mode
  const modeRow = fieldRow("Mode");
  const modeSeg = el("div","seg"); modeSeg.id = "seg-mode";
  const modeCells = [];
  [["read","Reading","fill the sentence"],["listen","Listening","type what you hear"]]
    .forEach(([m,t,d]) => {
      const b = el("button"); b.innerHTML = `${t}<small>${d}</small>`;
      b.classList.toggle("on", sel.mode===m);
      b.disabled = (m==="listen" && !state.audio_ok);
      b.onclick = () => { if(!b.disabled){ sel.mode=m; renderSetup(); } };
      modeSeg.appendChild(b); if (!b.disabled) modeCells.push(b);
    });
  modeRow.appendChild(modeSeg); p.appendChild(modeRow);
  setupGrid.push(modeCells);

  // forms
  const formRow = fieldRow("Forms");
  const chips = el("div","chips");
  const formCells = [];
  ["base","past","part"].forEach(f => {
    if (f==="part" && !c.has_part) return;
    const b = el("button", null, COL[f]);
    b.classList.toggle("on", sel.forms.includes(f));
    b.onclick = () => toggleForm(f);
    chips.appendChild(b); formCells.push(b);
  });
  formRow.appendChild(chips); p.appendChild(formRow);
  setupGrid.push(formCells);

  // words editor link
  const wordsRow = fieldRow("Words");
  const wl = el("button","rowlink", `Edit word list  (${c.words_on}/${c.words_total} on) →`);
  wl.onclick = () => openEditor(sel.cat);
  wordsRow.appendChild(wl); p.appendChild(wordsRow);
  setupGrid.push([wl]);

  // blocks
  const blockRow = fieldRow("Block");
  const bchips = el("div","chips");
  const blockCells = [];
  const cont = el("button", null, `Continue (${c.completed}/${c.words_on})`);
  cont.classList.toggle("on", sel.block===null);
  cont.onclick = () => { sel.block=null; renderSetup(); };
  bchips.appendChild(cont); blockCells.push(cont);
  c.blocks.forEach((size,i) => {
    const b = el("button", null, `Block ${i+1}`); b.title = `${size} words`;
    b.classList.toggle("on", sel.block===i);
    b.onclick = () => { sel.block=i; renderSetup(); };
    bchips.appendChild(b); blockCells.push(b);
  });
  blockRow.appendChild(bchips); p.appendChild(blockRow);
  setupGrid.push(blockCells);

  // hint (red when no key in reading mode)
  const hint = el("p","hintline");
  if (sel.mode==="read" && !state.has_key) {
    hint.classList.add("warn");
    hint.innerHTML = "⚠ No API key — reading falls back to blank fields. " +
      "Add one in Settings ⚙" + (state.audio_ok ? ", or use Listening (no key needed)." : ".");
  } else {
    hint.textContent = sel.mode==="read"
      ? "Fill the blank in an AI-written sentence for each form."
      : "You hear each form in random order and type the word.";
  }
  p.appendChild(hint);

  // start buttons
  const row = el("div","btnrow");
  const start = el("button","primary big",
    sel.block===null ? "Continue practicing" : `Start block ${sel.block+1}`);
  start.id = "btn-start"; start.onclick = startSession;
  const reset = el("button","ghost","Reset progress"); reset.id = "btn-reset";
  reset.onclick = resetProgress;
  row.append(start, reset); p.appendChild(row);
  setupGrid.push([start, reset]);

  if (setupR===null) { setupR = setupGrid.length-1; setupC = 0; }  // land on "Continue practicing"
  markSetup();
  $("setup-keys").innerHTML =
    "<kbd>↑ ↓ ← →</kbd> move · <kbd>Enter</kbd> choose · <kbd>Esc</kbd> back";
}
function fieldRow(label){ const r=el("div","field-row"); r.appendChild(el("span","lbl",label)); return r; }
function toggleForm(f) {
  if (sel.forms.includes(f)) { if (sel.forms.length>1) sel.forms=sel.forms.filter(x=>x!==f); }
  else sel.forms.push(f);
  renderSetup();
}
function markSetup() {
  setupR = Math.max(0, Math.min(setupR, setupGrid.length-1));
  const row = setupGrid[setupR] || [];
  setupC = Math.max(0, Math.min(setupC, row.length-1));
  setupGrid.flat().forEach(b => b.classList.remove("kfocus"));
  const cell = row[setupC];
  if (cell) { cell.classList.add("kfocus"); cell.scrollIntoView({block:"nearest"}); }
}
function setupKeys(k) {
  if (k==="ArrowDown")       { setupR++; markSetup(); }
  else if (k==="ArrowUp")    { setupR--; markSetup(); }
  else if (k==="ArrowRight") { setupC++; markSetup(); }
  else if (k==="ArrowLeft")  { setupC--; markSetup(); }
  else if (k==="Enter" || k===" ") { (setupGrid[setupR]||[])[setupC]?.click(); }
}
async function resetProgress() {
  await api("/api/progress", {cat:sel.cat, completed:0});
  state.cats[sel.cat].completed = 0; sel.block=null; renderSetup();
}

/* ═══════════════════════════ EDITOR ═══════════════════════════ */
let ed = null;          // editor_state
let edItems = [];       // flat navigable list
let edSel = 0;
let carry = null;       // name being moved

async function openEditor(cat) {
  ed = await api("/api/editor/" + cat);
  edSel = 0; carry = null;
  renderEditor(); show("editor");
}
function edBuildItems() {
  edItems = [];
  ed.blocks.forEach((rows, bi) => {
    edItems.push({kind:"header", bi});
    rows.forEach(r => edItems.push({kind:"word", bi, name:r.name, row:r}));
    edItems.push({kind:"add", bi});
    edItems.push({kind:"delblock", bi});
  });
  edItems.push({kind:"newblock"});
  if (ed.deleted > 0) edItems.push({kind:"restore"});
}
function renderEditor(keepName) {
  edBuildItems();
  if (keepName) {
    const i = edItems.findIndex(it => it.kind==="word" && it.name===keepName);
    if (i>=0) edSel = i;
  }
  edSel = Math.max(0, Math.min(edSel, edItems.length-1));
  $("editor-title").textContent = ed.title + " — word list";
  $("editor-sub").textContent = carry
    ? `Moving “${carry}” — ↑↓ to slide it, ← to drop it here`
    : `${ed.on} words on · ${ed.blocks.length} blocks · changes save automatically`;
  if (carry) $("editor-sub").style.color = "var(--acc)"; else $("editor-sub").style.color = "";

  const list = $("editor-list"); list.innerHTML = "";
  let idx = 0;
  ed.blocks.forEach((rows, bi) => {
    const block = el("div","ed-block");
    // header
    const head = el("div","ed-head"); head.dataset.i = idx;
    const on = rows.filter(r=>r.on).length;
    head.append(el("span","bt",`Block ${bi+1}`), el("span","cnt",`${on}/${rows.length} on`),
                el("span","spacer"));
    const tgAll = el("button","mini","Toggle all"); tgAll.onclick = e=>{e.stopPropagation(); edAct(idx,"toggle_block");};
    const delB = el("button","mini danger","Delete block"); delB.style.color="var(--red)";
    delB.onclick = e=>{e.stopPropagation(); edSel=itemIndex("delblock",bi); edActivate();};
    head.append(tgAll, delB);
    head.onclick = () => { edSel = headIdx(bi); markEditor(); };
    if (idx===edSel) head.classList.add("focus");
    block.appendChild(head); idx++;
    // words
    rows.forEach(r => {
      const rowEl = el("div","ed-row" + (r.on?"":" off"));
      rowEl.dataset.i = idx;
      if (r.name===carry) rowEl.classList.add("carry");
      else if (idx===edSel) rowEl.classList.add("focus");
      rowEl.append(el("span","chk", r.on?"☑":"☐"));
      rowEl.append(el("span","forms", r.forms.join(" · ")));
      const es = el("span","es"); es.innerHTML = r.es + (r.custom ? ' <span class="dot">•</span>' : "");
      rowEl.append(es);
      const acts = el("div","acts");
      const up=el("button",null,"▲"), dn=el("button",null,"▼"), rm=el("button","del","✕");
      up.title="Move up"; dn.title="Move down"; rm.title="Remove word";
      const nm = r.name;
      up.onclick=e=>{e.stopPropagation(); edMove(nm,"up");};
      dn.onclick=e=>{e.stopPropagation(); edMove(nm,"down");};
      rm.onclick=e=>{e.stopPropagation(); edDeleteWord(nm);};
      acts.append(up,dn,rm); rowEl.append(acts);
      rowEl.onclick = () => {
        if (carry) { if (nm===carry) dropCarry(); return; }
        edSel = wordIdx(nm); markEditor(); toggleWord(nm);
      };
      block.appendChild(rowEl); idx++;
    });
    // actions
    const acts = el("div","ed-actions");
    const add = el("button","ed-link","＋  Add a word here"); add.dataset.i=idx;
    add.onclick=()=>{ edSel=idx; openWordDialog(bi); };
    if (idx===edSel) add.classList.add("focus"); acts.appendChild(add); idx++;
    const delr = el("button","ed-link danger","🗑  Delete this block"); delr.dataset.i=idx;
    delr.onclick=()=>{ edSel=idx; edActivate(); };
    if (idx===edSel) delr.classList.add("focus"); acts.appendChild(delr); idx++;
    block.appendChild(acts);
    list.appendChild(block);
  });
  const tail = el("div","ed-actions");
  const nb = el("button","ed-link","＋  New block"); nb.dataset.i=idx;
  nb.onclick=()=>{ edSel=idx; edAct(null,"add_block"); };
  if (idx===edSel) nb.classList.add("focus"); tail.appendChild(nb); idx++;
  if (ed.deleted>0) {
    const rs = el("button","ed-link","↩  Restore "+ed.deleted+" deleted"); rs.dataset.i=idx;
    rs.onclick=()=>{ edSel=idx; edAct(null,"restore"); };
    if (idx===edSel) rs.classList.add("focus"); tail.appendChild(rs); idx++;
  }
  list.appendChild(tail);
  scrollEditorTo(edSel);
  $("editor-keys").innerHTML = carry
    ? "<kbd>↑ ↓</kbd> slide · <kbd>←</kbd> drop · <kbd>Esc</kbd> drop"
    : "<kbd>↑ ↓</kbd> move · <kbd>Enter</kbd> select · <kbd>Space</kbd> toggle · " +
      "<kbd>→</kbd> pick up · <kbd>Del</kbd> remove · <kbd>Esc</kbd> done";
}
const headIdx = (bi) => edItems.findIndex(it=>it.kind==="header"&&it.bi===bi);
const wordIdx = (nm) => edItems.findIndex(it=>it.kind==="word"&&it.name===nm);
const itemIndex = (kind,bi) => edItems.findIndex(it=>it.kind===kind&&it.bi===bi);
function markEditor() {
  [...$("editor-list").querySelectorAll("[data-i]")].forEach(node=>{
    const i = +node.dataset.i;
    node.classList.toggle("focus", i===edSel && !(edItems[i]?.kind==="word" && edItems[i].name===carry));
  });
  scrollEditorTo(edSel);
}
function scrollEditorTo(i) {
  const node = $("editor-list").querySelector(`[data-i="${i}"]`);
  if (node) node.scrollIntoView({block:"nearest"});
}
async function edAct(arg, action, extra={}) {
  const body = {cat:ed.cat, action, ...extra};
  if (action==="toggle_block"||action==="delete_block") body.block = edItems[arg]?.bi ?? extra.block;
  if (action==="add_block"||action==="restore") {}
  ed = await api("/api/editor", body);
  await refreshStateSoft();
  renderEditor(extra.keep);
}
async function toggleWord(nm) {
  ed = await api("/api/editor", {cat:ed.cat, action:"toggle_word", name:nm});
  await refreshStateSoft(); renderEditor(nm);
}
async function edMove(nm, dir) {
  ed = await api("/api/editor", {cat:ed.cat, action:"move", name:nm, dir});
  renderEditor(nm);
}
function edActivate() {
  const it = edItems[edSel];
  if (!it) return;
  if (it.kind==="header") edAct(edSel,"toggle_block",{block:it.bi});
  else if (it.kind==="word") { edSel=wordIdx(it.name); toggleWord(it.name); }
  else if (it.kind==="add") openWordDialog(it.bi);
  else if (it.kind==="delblock") askDeleteBlock(it.bi);
  else if (it.kind==="newblock") edAct(null,"add_block");
  else if (it.kind==="restore") edAct(null,"restore");
}
function edKeys(k) {
  if (carry) {
    if (k==="ArrowDown") slideCarry(1);
    else if (k==="ArrowUp") slideCarry(-1);
    else if (k==="ArrowLeft"||k==="Enter"||k==="Escape") dropCarry();
    return;
  }
  if (k==="ArrowDown") { edSel=Math.min(edItems.length-1,edSel+1); markEditor(); }
  else if (k==="ArrowUp") { edSel=Math.max(0,edSel-1); markEditor(); }
  else if (k==="Enter" || k===" ") { if(k===" " && edItems[edSel].kind!=="word" && edItems[edSel].kind!=="header"){} edActivate(); }
  else if (k==="ArrowRight") { if (edItems[edSel].kind==="word") pickCarry(edItems[edSel].name); }
  else if (k==="Delete") { if (edItems[edSel].kind==="word") edDeleteWord(edItems[edSel].name); }
  else if (k==="Escape") { show("setup"); refreshStateSoft().then(renderSetup); }
}
function pickCarry(nm) { carry = nm; renderEditor(nm); }
function dropCarry() { const nm=carry; carry=null; renderEditor(nm); refreshStateSoft(); }
async function slideCarry(d) {
  const nm = carry;
  ed = await api("/api/editor", {cat:ed.cat, action:"move", name:nm, dir:d>0?"down":"up"});
  renderEditor(nm);
}
function edDeleteWord(nm) {
  const row = ed.blocks.flat().find(r=>r.name===nm);
  askConfirm(`Remove “${nm}”?`, row && row.custom
      ? "This is one of your own words — it can't be restored."
      : "You can bring it back later with Restore.",
    [["Remove", async()=>{ ed=await api("/api/editor",{cat:ed.cat,action:"delete_word",name:nm});
        await refreshStateSoft(); renderEditor(); }, true],
     ["Cancel", null]]);
}
function askDeleteBlock(bi) {
  const n = ed.blocks[bi].length;
  if (ed.blocks.length<=1) { toast("This is the only block — it can't be deleted."); return; }
  if (n===0) { edAct(null,"delete_block",{block:bi}); return; }
  askConfirm(`Delete block ${bi+1}?`, `It has ${n} word${n!==1?"s":""}. What should happen to them?`,
    [["Keep words (move them over)", async()=>{ ed=await api("/api/editor",
        {cat:ed.cat,action:"delete_block",block:bi,keep_words:true}); await refreshStateSoft(); renderEditor(); }],
     ["Delete the words too", async()=>{ ed=await api("/api/editor",
        {cat:ed.cat,action:"delete_block",block:bi,keep_words:false}); await refreshStateSoft(); renderEditor(); }, true],
     ["Cancel", null]]);
}

/* new-word dialog */
function openWordDialog(bi) {
  const c = state.cats[sel.cat] || ed;
  const has_part = ed.has_part;
  const specs = [["es","Spanish — meaning (e.g. comer)",false],
                 ["base","English — base form",false],
                 ["past","English — past simple",false]];
  if (has_part) specs.push(["part","English — past participle",false]);
  specs.push(["es_past","Spanish — past (optional, e.g. comí)",true]);
  if (has_part) specs.push(["es_part","Spanish — participle (optional, e.g. comido)",true]);
  const grid = $("word-fields"); grid.innerHTML = "";
  const inputs = {};
  specs.forEach(([k,label,opt]) => {
    const l = el("label", opt?"opt":null); l.appendChild(el("span",null,label));
    const inp = el("input"); inp.type="text"; inp.autocomplete="off"; inp.spellcheck=false;
    l.appendChild(inp); grid.appendChild(l); inputs[k]=inp;
  });
  const bl = $("word-block"); bl.innerHTML=""; let target=bi;
  ed.blocks.forEach((_,i)=>{ const b=el("button",null,`Block ${i+1}`);
    b.classList.toggle("on", i===target);
    b.onclick=()=>{ target=i; [...bl.children].forEach((x,j)=>x.classList.toggle("on",j===target)); };
    bl.appendChild(b); });
  $("word-err").textContent = "";
  const dlg = $("dlg-word");
  $("btn-word-save").onclick = async () => {
    const body = {cat:ed.cat, action:"create", block:target};
    ["es","base","past","part","es_past","es_part"].forEach(k=>{ if(inputs[k]) body[k]=inputs[k].value; });
    if (!body.es?.trim() || !body.base?.trim() || !body.past?.trim() || (has_part && !body.part?.trim())) {
      $("word-err").textContent = "Fill in the required fields."; return; }
    const res = await api("/api/editor", body);
    if (res.error==="invalid") { $("word-err").textContent = "That word already exists (or has a “|”)."; return; }
    ed = res; await refreshStateSoft(); dlg.close(); renderEditor(body.base.trim().toLowerCase());
  };
  $("btn-word-cancel").onclick = () => dlg.close();
  dlg.showModal(); inputs.es.focus();
}

/* ═══════════════════════════ PRACTICE ═══════════════════════════ */
async function startSession() {
  try {
    const body = {cat:sel.cat, mode:sel.mode, forms:sel.forms};
    if (sel.block!==null) body.start = sel.block;
    const s = await api("/api/session", body);
    S = {cat:sel.cat, mode:sel.mode, forms:sel.forms, sizes:s.sizes, block:s.start,
         total:s.total, ok:0, bad:0, streak:0};
    await api("/api/settings", {mode:sel.mode}); state.mode = sel.mode;
    startBlock(S.block);
  } catch(e) { toast("Could not start: " + e.message); }
}
async function startBlock(i) {
  S.block=i; S.idx=0; S.blkOk=0; S.blkBad=0; S.locked=false;
  $("prompt-main").textContent="…"; $("prompt-sub").textContent="Loading block…";
  $("prac-fields").innerHTML=""; $("prac-feedback").textContent=""; $("prac-feedback").className="";
  show("practice");
  try {
    const r = await api("/api/block", {cat:S.cat, mode:S.mode, forms:S.forms, block:i});
    S.words = r.words; loadWord();
  } catch(e) { toast("Could not load block: " + e.message); }
}
const blockOffset = () => S.sizes.slice(0,S.block).reduce((a,b)=>a+b,0);
function loadWord() {
  clearTimeout(S.timer); S.locked=false;
  if (S.idx>=S.words.length) { blockDone(); return; }
  const w = S.words[S.idx];
  const done = blockOffset()+S.idx;
  $("prac-pos").textContent =
    `Block ${S.block+1}/${S.sizes.length} · Word ${S.idx+1}/${S.words.length} · ${done}/${S.total} total`;
  let st = `✓ ${S.ok}   ✗ ${S.bad}`; if (S.streak>=3) st += `   ·   ${S.streak} in a row!`;
  $("prac-stats").textContent = st;
  $("prac-bar").style.width = `${100*S.idx/S.words.length}%`;
  $("prac-feedback").textContent=""; $("prac-feedback").className="";
  if (S.mode==="listen") {
    $("prompt-main").textContent = "♫  Listen…";
    $("prompt-sub").textContent = state.listen_hint ? w.es : "type each word you hear";
    $("prac-keys").innerHTML="<kbd>Enter</kbd> check · <kbd>Space</kbd> hear again · <kbd>↑↓</kbd> move · <kbd>Esc</kbd> options";
  } else {
    $("prompt-main").textContent = w.es; $("prompt-sub").textContent="";
    $("prac-keys").innerHTML="<kbd>Enter</kbd> next / check · <kbd>↑↓</kbd> move · <kbd>Esc</kbd> options";
  }
  const wrap = $("prac-fields"); wrap.innerHTML="";
  w.fields.forEach((f,fi) => {
    const line = el("div","fieldline");
    if (S.mode==="listen") {
      const play=el("button","play-btn","♫"); play.title="Play (Space)"; play.onclick=()=>playWord(f.answer);
      const inp=mkInput(fi); inp.addEventListener("focus",()=>playWord(f.answer));
      const meaning=el("span","meaning");
      inp.addEventListener("input",()=>{ meaning.textContent=inp.value.trim()?f.meaning:""; meaning.className="meaning"; });
      line.append(play,inp,meaning);
    } else if (f.sentence) {
      const [b,a] = f.sentence.split("___");
      line.append(el("span","lab",COL[f.col]), el("span","sent",b??""), mkInput(fi), el("span","sent",a??""));
    } else {
      line.append(el("span","lab",COL[f.col]), mkInput(fi));
    }
    wrap.appendChild(line);
  });
  inputs()[0]?.focus();
}
function mkInput(fi){ const i=el("input"); i.type="text"; i.dataset.fi=fi; i.autocomplete="off"; i.spellcheck=false; return i; }
const inputs = () => [...$("prac-fields").querySelectorAll("input")];
function playWord(word){ if(!state.audio_ok) return; audioEl.pause();
  audioEl=new Audio("/api/audio/"+encodeURIComponent(word)); audioEl.play().catch(()=>{}); }
const norm = (s) => s.trim().toLowerCase().split(/\s+/).join(" ");
function pracEnter() {
  if (S.locked) { clearTimeout(S.timer); advance(); return; }
  const es=inputs(); const i=es.indexOf(document.activeElement);
  if (i===-1) { es[0]?.focus(); return; }
  const f=S.words[S.idx].fields[i];
  if (S.mode==="read" && f.accept.includes(norm(es[i].value))) playWord(f.answer);
  if (i<es.length-1) es[i+1].focus(); else validate();
}
function moveField(d){ const es=inputs(); const i=es.indexOf(document.activeElement);
  const j=i===-1?0:i+d; if(j>=0&&j<es.length) es[j].focus(); }
function validate() {
  const w=S.words[S.idx]; const es=inputs(); const bad=[];
  w.fields.forEach((f,i)=>{
    const good=f.accept.includes(norm(es[i].value));
    es[i].classList.add(good?"good":"bad"); es[i].disabled=true;
    if (!good) { bad.push(f.answer); if (S.mode==="listen") es[i].value=f.answer; }
    if (S.mode==="listen") { const m=es[i].closest(".fieldline").querySelector(".meaning");
      m.textContent=f.meaning; m.className="meaning "+(good?"good":"bad"); }
  });
  S.locked=true; const fb=$("prac-feedback");
  if (bad.length) { S.bad++; S.blkBad++; S.streak=0;
    fb.textContent = S.mode==="listen" ? "✗" : "✗   "+bad.join("  ·  "); fb.className="bad";
    S.timer=setTimeout(advance,FEED_BAD);
  } else { S.ok++; S.blkOk++; S.streak++; fb.textContent="✓  Correct!"; fb.className="good";
    S.timer=setTimeout(advance,FEED_OK); }
}
function advance(){ S.locked=false; S.idx++; loadWord(); }
async function blockDone() {
  const doneCount = blockOffset()+S.words.length;
  const c = state.cats[S.cat];
  const newComp = Math.max(c.completed, doneCount);
  try { await api("/api/progress",{cat:S.cat,completed:newComp}); } catch(_){}
  c.completed = Math.min(newComp, c.words_on);
  const last = S.block+1>=S.sizes.length;
  $("done-title").textContent = last ? "★  All verbs completed!" : "Block completed!";
  const t=S.blkOk+S.blkBad;
  $("done-stats").textContent = `✓ ${S.blkOk}   ✗ ${S.blkBad}` +
    (t?`   ·   ${Math.round(100*S.blkOk/t)}% accuracy`:"") +
    `   ·   ${Math.min(doneCount,S.total)}/${S.total} total`;
  const opts = last
    ? [["Start over from zero", async()=>{ await api("/api/progress",{cat:S.cat,completed:0}); c.completed=0; renderHome(); }],
       ["Back to home", renderHome]]
    : [["Continue to next block", ()=>startBlock(S.block+1)],
       ["Repeat this block", ()=>startBlock(S.block)],
       ["Back to home", renderHome]];
  renderMenu($("done-list"), opts, 0, "done");
  $("done-keys").innerHTML="<kbd>↑ ↓</kbd> move · <kbd>Enter</kbd> select · <kbd>Esc</kbd> home";
  show("done");
}

/* vertical menu with keyboard (used by done screen) */
let menuState = null;
function renderMenu(container, opts, sel0, tag) {
  container.innerHTML="";
  opts.forEach(([label,fn],i)=>{ const b=el("button",null,label);
    b.onclick=fn; b.onmouseenter=()=>{ menuState.sel=i; markMenu(); };
    container.appendChild(b); });
  menuState={container,opts,sel:sel0,tag}; markMenu();
}
function markMenu(){ [...menuState.container.children].forEach((b,i)=>b.classList.toggle("on",i===menuState.sel)); }
function menuKeys(k){
  if (!menuState) return;
  if (k==="ArrowDown"){ menuState.sel=Math.min(menuState.opts.length-1,menuState.sel+1); markMenu(); }
  else if (k==="ArrowUp"){ menuState.sel=Math.max(0,menuState.sel-1); markMenu(); }
  else if (k==="Enter"){ menuState.opts[menuState.sel][1](); }
}

/* ═══════════════════════════ SETTINGS ═══════════════════════════ */
function renderSettings() {
  const sv=$("seg-voice"); sv.innerHTML="";
  state.voices.forEach(([id,label])=>{ const b=el("button",null,label);
    b.classList.toggle("on",id===state.voice);
    b.disabled=!state.audio_ok;
    b.onclick=async()=>{ state=await api("/api/settings",{voice:id}); renderSettings(); };
    sv.appendChild(b); });
  const stg=$("seg-theme"); stg.innerHTML="";
  state.themes.forEach(t=>{ const b=el("button",null,t==="light"?"Light":"Dark");
    b.classList.toggle("on",t===state.theme);
    b.onclick=async()=>{ state=await api("/api/settings",{theme:t}); applyTheme(); renderSettings(); };
    stg.appendChild(b); });
  const s=$("key-status");
  if (state.has_key){ s.textContent="✓ A key is saved on this computer."; s.className="small status ok"; }
  else { s.textContent="⚠ No key saved — Reading mode will use blank fields."; s.className="small status warn"; }
  $("btn-key-remove").style.display = state.has_key ? "" : "none";
  if (!state.audio_ok) {
    if (!$("voice-warn")) { const w=el("p","small status warn","⚠ Voice needs the edge-tts package (pip install edge-tts).");
      w.id="voice-warn"; $("seg-voice").after(w); }
  }
}
function wireSettings() {
  $("btn-settings").onclick=()=>{ renderSettings(); $("dlg-settings").showModal(); };
  $("btn-settings-close").onclick=()=>$("dlg-settings").close();
  $("btn-key-save").onclick=async()=>{ const k=$("inp-key").value.trim(); if(!k) return;
    state=await api("/api/settings",{gemini_key:k}); $("inp-key").value=""; renderSettings(); softRefresh(); };
  $("btn-key-remove").onclick=async()=>{ state=await api("/api/settings",{gemini_key:""});
    renderSettings(); softRefresh(); };
}
function softRefresh(){ if(screen==="home") renderHome(); if(screen==="setup") renderSetup(); }
async function refreshStateSoft(){ try{ state=await api("/api/state"); }catch(_){}}

/* ═══════════════════════════ CONFIRM DIALOG ═══════════════════════════ */
let confirmState=null;
function askConfirm(title,msg,opts){
  $("confirm-title").textContent=title; $("confirm-msg").textContent=msg;
  const list=$("confirm-list"); list.innerHTML="";
  opts.forEach(([label,fn,danger],i)=>{ const b=el("button", danger?"danger":null, label);
    b.onclick=()=>{ $("dlg-confirm").close(); if(fn) fn(); };
    b.onmouseenter=()=>{ confirmState.sel=i; markConfirm(); };
    list.appendChild(b); });
  confirmState={opts,sel:opts.length-1};
  markConfirm(); $("dlg-confirm").showModal();
}
function markConfirm(){ [...$("confirm-list").children].forEach((b,i)=>b.classList.toggle("on",i===confirmState.sel)); }

/* ═══════════════════════════ GLOBAL KEYBOARD ═══════════════════════════ */
document.addEventListener("keydown",(ev)=>{
  const open = document.querySelector("dialog[open]");
  if (open) {
    if (open.id==="dlg-confirm" && confirmState) {
      if (ev.key==="ArrowDown"){ev.preventDefault(); confirmState.sel=Math.min(confirmState.opts.length-1,confirmState.sel+1); markConfirm();}
      else if (ev.key==="ArrowUp"){ev.preventDefault(); confirmState.sel=Math.max(0,confirmState.sel-1); markConfirm();}
      else if (ev.key==="Enter"){ev.preventDefault(); const o=confirmState.opts[confirmState.sel]; $("dlg-confirm").close(); if(o[1])o[1]();}
      else if (ev.key==="Escape"){ $("dlg-confirm").close(); }
    }
    return; // dialogs handle their own keys / Esc closes them natively
  }
  const k = ev.key;
  const nav = ["ArrowUp","ArrowDown","ArrowLeft","ArrowRight"," "];
  if (screen==="practice") {
    if (k==="Enter"){ev.preventDefault(); pracEnter();}
    else if (k==="ArrowDown"){ev.preventDefault(); if(!S.locked) moveField(1);}
    else if (k==="ArrowUp"){ev.preventDefault(); if(!S.locked) moveField(-1);}
    else if (k===" " && S.mode==="listen"){ev.preventDefault();
      const es=inputs(); const i=Math.max(0,es.indexOf(document.activeElement));
      const f=S.words[S.idx]?.fields[i]; if(f) playWord(f.answer);}
    else if (k==="Escape"){ clearTimeout(S.timer);
      show("setup"); refreshStateSoft().then(renderSetup); }
    return;
  }
  if (screen==="editor") { if(nav.includes(k)||k==="Enter"||k==="Delete"||k==="Escape"){ev.preventDefault(); edKeys(k);} return; }
  if (screen==="home")  { if(nav.includes(k)||k==="Enter"){ev.preventDefault(); homeKeys(k);} else if(k==="Escape"){} return; }
  if (screen==="setup") { if(nav.includes(k)||k==="Enter"){ev.preventDefault(); setupKeys(k);} else if(k==="Escape"){renderHome();} return; }
  if (screen==="done")  { if(k==="ArrowUp"||k==="ArrowDown"||k==="Enter"){ev.preventDefault(); menuKeys(k);} else if(k==="Escape"){renderHome();} return; }
});

/* ═══════════════════════════ BOOT ═══════════════════════════ */
async function boot() {
  try { state = await api("/api/state"); }
  catch(e) { toast("Could not reach the local server — is python main.py running?"); return; }
  applyTheme(); wireSettings();
  $("brand-home").onclick = renderHome;
  renderHome();
}
boot();
