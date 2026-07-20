/* Practice screen (reading & listening), the block-complete screen, and the
   keyboard handling for both. `S` is the live session; it never leaves here. */
import { $, el, app, show, api, toast, refreshStateSoft, COL, FEED_OK, FEED_BAD } from "./core.js";
import { sel, renderSetup } from "./setup.js";
import { renderHome } from "./home.js";

let S = null;               // practice session
let audioEl = new Audio();

export async function startSession() {
  try {
    const body = {cat:sel.cat, mode:sel.mode, forms:sel.forms};
    if (sel.block!==null) body.start = sel.block;
    const s = await api("/api/session", body);
    S = {cat:sel.cat, mode:sel.mode, forms:sel.forms, sizes:s.sizes, block:s.start,
         total:s.total, ok:0, bad:0, streak:0};
    await api("/api/settings", {mode:sel.mode}); app.state.mode = sel.mode;
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
    $("prompt-sub").textContent = app.state.listen_hint ? w.es : "type each word you hear";
    $("prac-keys").innerHTML="<kbd>Enter</kbd> check · <kbd>Space</kbd> hear again · <kbd>↑↓</kbd> move · <kbd>,</kbd> settings · <kbd>Esc</kbd> back";
  } else {
    $("prompt-main").textContent = w.es; $("prompt-sub").textContent="";
    $("prac-keys").innerHTML="<kbd>Enter</kbd> next / check · <kbd>↑↓</kbd> move · <kbd>,</kbd> settings · <kbd>Esc</kbd> back";
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
function playWord(word){ if(!app.state.audio_ok) return; audioEl.pause();
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
  const c = app.state.cats[S.cat];
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
  renderMenu($("done-list"), opts, 0);
  $("done-keys").innerHTML="<kbd>↑ ↓</kbd> move · <kbd>Enter</kbd> select · <kbd>,</kbd> settings · <kbd>Esc</kbd> home";
  show("done");
}

/* vertical menu with keyboard (used by the done screen) */
let menuState = null;
function renderMenu(container, opts, sel0) {
  container.innerHTML="";
  opts.forEach(([label,fn],i)=>{ const b=el("button",null,label);
    b.onclick=fn; b.onmouseenter=()=>{ menuState.sel=i; markMenu(); };
    container.appendChild(b); });
  menuState={container,opts,sel:sel0}; markMenu();
}
function markMenu(){ [...menuState.container.children].forEach((b,i)=>b.classList.toggle("on",i===menuState.sel)); }
export function menuKeys(k){
  if (!menuState) return;
  if (k==="ArrowDown"){ menuState.sel=Math.min(menuState.opts.length-1,menuState.sel+1); markMenu(); }
  else if (k==="ArrowUp"){ menuState.sel=Math.max(0,menuState.sel-1); markMenu(); }
  else if (k==="Enter"){ menuState.opts[menuState.sel][1](); }
}

/* keyboard for the practice screen (delegated from the global dispatcher) */
export function practiceKeys(ev) {
  const k = ev.key;
  if (k==="Enter"){ ev.preventDefault(); pracEnter(); }
  else if (k==="ArrowDown"){ ev.preventDefault(); if(!S.locked) moveField(1); }
  else if (k==="ArrowUp"){ ev.preventDefault(); if(!S.locked) moveField(-1); }
  else if (k===" " && S.mode==="listen"){ ev.preventDefault();
    const es=inputs(); const i=Math.max(0,es.indexOf(document.activeElement));
    const f=S.words[S.idx]?.fields[i]; if(f) playWord(f.answer); }
  else if (k==="Escape"){ clearTimeout(S.timer);
    show("setup"); refreshStateSoft().then(renderSetup); }
}
