/* Shared foundation for every screen module: tiny DOM helpers, the JSON API
   client, view routing, and the one piece of mutable state everyone reads
   (`app`).  Kept dependency-free so every other module can import it safely. */

export const $ = (id) => document.getElementById(id);
export const el = (tag, cls, txt) => { const e = document.createElement(tag);
  if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };

export async function api(path, body) {
  const opt = body === undefined ? {}
    : {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)};
  const r = await fetch(path, opt);
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.json();
}

export function toast(msg, ok) {
  const t = $("toast"); t.textContent = msg; t.className = "toast" + (ok ? " ok" : "");
  clearTimeout(t._t); t._t = setTimeout(() => t.classList.add("hidden"), 3200);
}

export const COL = {base:"Base form", past:"Past simple", part:"Past participle"};
export const FEED_OK = 650, FEED_BAD = 2400;

/* The whole app's shared, mutable state lives on this single object so any
   module can read/write it by reference (ES module `let` exports are read-only
   for importers, which is why we hang the fields off an object instead). */
export const app = {
  state: null,     // last /api/state payload
  screen: "home",  // which view is showing
};

export function show(name) {
  app.screen = name;
  for (const v of ["home","setup","editor","practice","done"])
    $("view-" + v).classList.toggle("hidden", v !== name);
}
export function applyTheme() { document.documentElement.dataset.theme = app.state.theme; }
export async function refreshStateSoft() { try { app.state = await api("/api/state"); } catch(_){} }
