/* The small "are you sure?" dialog, plus the keyboard handling for any open
   dialog (so global shortcuts don't fire while a modal is up). */
import { $, el } from "./core.js";

let confirmState = null;

export function askConfirm(title, msg, opts) {
  $("confirm-title").textContent = title; $("confirm-msg").textContent = msg;
  const list = $("confirm-list"); list.innerHTML = "";
  opts.forEach(([label, fn, danger], i) => {
    const b = el("button", danger ? "danger" : null, label);
    b.onclick = () => { $("dlg-confirm").close(); if (fn) fn(); };
    b.onmouseenter = () => { confirmState.sel = i; markConfirm(); };
    list.appendChild(b);
  });
  confirmState = {opts, sel: opts.length - 1};
  markConfirm(); $("dlg-confirm").showModal();
}
function markConfirm() {
  [...$("confirm-list").children].forEach((b, i) => b.classList.toggle("on", i === confirmState.sel));
}

/* Returns true if a dialog is open (and thus swallowed the key), so the global
   handler knows to stop. The confirm dialog gets arrow/Enter navigation; other
   dialogs just let Esc close them natively. */
export function dialogKeydown(ev) {
  const open = document.querySelector("dialog[open]");
  if (!open) return false;
  if (open.id === "dlg-confirm" && confirmState) {
    if (ev.key === "ArrowDown") { ev.preventDefault(); confirmState.sel = Math.min(confirmState.opts.length-1, confirmState.sel+1); markConfirm(); }
    else if (ev.key === "ArrowUp") { ev.preventDefault(); confirmState.sel = Math.max(0, confirmState.sel-1); markConfirm(); }
    else if (ev.key === "Enter") { ev.preventDefault(); const o = confirmState.opts[confirmState.sel]; $("dlg-confirm").close(); if (o[1]) o[1](); }
    else if (ev.key === "Escape") { $("dlg-confirm").close(); }
  }
  return true;
}
