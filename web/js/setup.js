/* Setup screen: pick mode / forms / block, then start. A grid of focusable
   buttons — ↑↓ walk rows, ←→ walk cells — so the highlight sits on exactly one
   control. `sel` holds the current choices and is shared with practice/editor. */
import { $, el, app, show, toast, api, COL } from "./core.js";
import { openEditor } from "./editor.js";
import { startSession } from "./practice.js";
import { askConfirm } from "./confirm.js";

export const sel = {cat:null, mode:"read", forms:[], block:null};
let setupGrid = [], setupR = 0, setupC = 0;

export function openSetup(cat) {
  sel.cat = cat;
  const c = app.state.cats[cat];
  sel.mode = (app.state.mode === "listen" && app.state.audio_ok) ? "listen" : "read";
  sel.forms = ["base","past"].concat(c.has_part ? ["part"] : []);
  sel.block = null;
  $("setup-title").textContent = c.title;
  setupR = null; setupC = 0;          // null → default the cursor to "Continue practicing"
  renderSetup(); show("setup");
}

export function renderSetup() {
  const c = app.state.cats[sel.cat];
  const p = $("setup-panel"); p.innerHTML = ""; setupGrid = [];

  // mode
  const modeRow = fieldRow("Mode");
  const modeSeg = el("div","seg"); modeSeg.id = "seg-mode";
  const modeCells = [];
  [["read","Reading","fill the sentence"],["listen","Listening","type what you hear"]]
    .forEach(([m,t,d]) => {
      const b = el("button"); b.innerHTML = `${t}<small>${d}</small>`;
      b.classList.toggle("on", sel.mode===m);
      b.disabled = (m==="listen" && !app.state.audio_ok);
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
  if (sel.mode==="read" && !app.state.has_key) {
    hint.classList.add("warn");
    hint.innerHTML = "⚠ No API key — reading falls back to blank fields. " +
      "Add one in Settings ⚙" + (app.state.audio_ok ? ", or use Listening (no key needed)." : ".");
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
    "<kbd>↑ ↓ ← →</kbd> move · <kbd>Enter</kbd> choose · <kbd>,</kbd> settings · <kbd>Esc</kbd> back";
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
export function setupKeys(k) {
  if (k==="ArrowDown")       { setupR++; markSetup(); }
  else if (k==="ArrowUp")    { setupR--; markSetup(); }
  else if (k==="ArrowRight") { setupC++; markSetup(); }
  else if (k==="ArrowLeft")  { setupC--; markSetup(); }
  else if (k==="Enter" || k===" ") { (setupGrid[setupR]||[])[setupC]?.click(); }
}
export function resetProgress() {
  const c = app.state.cats[sel.cat];
  if (!c.completed) { toast("Progress is already at zero."); return; }
  askConfirm("Reset progress?",
    `This clears the ${c.completed}/${c.words_on} words you've completed in ${c.title.toLowerCase()}.`,
    [["Reset progress", async()=>{ await api("/api/progress",{cat:sel.cat,completed:0});
        c.completed=0; sel.block=null; renderSetup(); }, true],
     ["Cancel", null]]);
}
