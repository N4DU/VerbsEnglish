/* One global keydown dispatcher. It picks the handler for the current screen,
   lets ","  open Settings from anywhere, and defers to an open dialog first. */
import { app } from "./core.js";
import { homeKeys, renderHome } from "./home.js";
import { setupKeys } from "./setup.js";
import { edKeys } from "./editor.js";
import { practiceKeys, menuKeys } from "./practice.js";
import { openSettings } from "./settings.js";
import { dialogKeydown } from "./confirm.js";

const NAV = ["ArrowUp","ArrowDown","ArrowLeft","ArrowRight"," "];

document.addEventListener("keydown", (ev) => {
  if (dialogKeydown(ev)) return;               // a dialog is open — it handles keys
  const k = ev.key;
  // Settings is reachable from anywhere — "," never appears in an answer, so
  // it's safe even while typing in a practice field.
  if (k === "," && !ev.ctrlKey && !ev.metaKey && !ev.altKey) { ev.preventDefault(); openSettings(); return; }

  switch (app.screen) {
    case "practice":
      practiceKeys(ev); return;
    case "editor":
      if (NAV.includes(k)||k==="Enter"||k==="Delete"||k==="Backspace"||k==="Escape") { ev.preventDefault(); edKeys(k); }
      return;
    case "home":
      if (NAV.includes(k)||k==="Enter") { ev.preventDefault(); homeKeys(k); }
      return;
    case "setup":
      if (NAV.includes(k)||k==="Enter") { ev.preventDefault(); setupKeys(k); }
      else if (k==="Escape") renderHome();
      return;
    case "done":
      if (k==="ArrowUp"||k==="ArrowDown"||k==="Enter") { ev.preventDefault(); menuKeys(k); }
      else if (k==="Escape") renderHome();
      return;
  }
});
