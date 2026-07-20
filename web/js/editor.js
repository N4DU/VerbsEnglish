/* Word-list editor: toggle words on/off, reorder them (keyboard "carry"), add
   or delete words and blocks. All mutations hit /api/editor and re-render. */
import { $, el, app, show, api, toast, refreshStateSoft } from "./core.js";
import { renderSetup } from "./setup.js";
import { askConfirm } from "./confirm.js";

let ed = null;          // editor_state
let edItems = [];       // flat navigable list
let edSel = 0;
let carry = null;       // name being moved

export async function openEditor(cat) {
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
    ? "<kbd>↑ ↓</kbd> slide it · <kbd>←</kbd> drop · <kbd>Esc</kbd> drop"
    : "<kbd>↑ ↓</kbd> move · <kbd>Space</kbd> on/off · <kbd>→</kbd> pick up &amp; reorder · " +
      "<kbd>Del</kbd> / <kbd>⌫</kbd> delete word · <kbd>Esc</kbd> done";
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
export function edKeys(k) {
  if (carry) {
    if (k==="ArrowDown") slideCarry(1);
    else if (k==="ArrowUp") slideCarry(-1);
    else if (k==="ArrowLeft"||k==="Enter"||k==="Escape") dropCarry();
    return;
  }
  if (k==="ArrowDown") { edSel=Math.min(edItems.length-1,edSel+1); markEditor(); }
  else if (k==="ArrowUp") { edSel=Math.max(0,edSel-1); markEditor(); }
  else if (k==="Enter" || k===" ") { edActivate(); }
  else if (k==="ArrowRight") { if (edItems[edSel].kind==="word") pickCarry(edItems[edSel].name); }
  else if (k==="Delete"||k==="Backspace") { if (edItems[edSel].kind==="word") edDeleteWord(edItems[edSel].name); }
  else if (k==="Escape") { show("setup"); refreshStateSoft().then(renderSetup); }
}
/* Pick up by toggling the class on the live row (not a full re-render) so the
   CSS transition plays and the word visibly slides sideways. */
function pickCarry(nm) {
  carry = nm;
  const row = $("editor-list").querySelector(`.ed-row[data-i="${wordIdx(nm)}"]`);
  if (row) { row.classList.remove("focus"); row.classList.add("carry"); }
  $("editor-sub").textContent = `Moving “${nm}” — ↑↓ to slide it, ← or Enter to drop it`;
  $("editor-sub").style.color = "var(--acc)";
  $("editor-keys").innerHTML =
    "<kbd>↑ ↓</kbd> slide · <kbd>←</kbd> drop · <kbd>Esc</kbd> drop";
}
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
