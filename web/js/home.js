/* Home screen: the two category cards you pick to start practising. */
import { $, el, app, show } from "./core.js";
import { openSetup } from "./setup.js";

let homeSel = 0;

export function renderHome() {
  const cats = Object.entries(app.state.cats);
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
    "<kbd>← →</kbd> choose · <kbd>Enter</kbd> start · <kbd>,</kbd> settings";
  markHome(); show("home");
}
function markHome() {
  [...$("cat-cards").children].forEach((c, i) => c.classList.toggle("on", i === homeSel));
}
export function homeKeys(k) {
  const n = Object.keys(app.state.cats).length;
  if (k === "ArrowRight" || k === "ArrowDown") { homeSel = Math.min(n-1, homeSel+1); markHome(); }
  else if (k === "ArrowLeft" || k === "ArrowUp") { homeSel = Math.max(0, homeSel-1); markHome(); }
  else if (k === "Enter") openSetup(Object.keys(app.state.cats)[homeSel]);
}
