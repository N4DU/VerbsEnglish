/* Settings dialog: voice, theme and the Gemini API key. */
import { $, el, app, api, applyTheme } from "./core.js";
import { renderHome } from "./home.js";
import { renderSetup } from "./setup.js";

export function renderSettings() {
  const sv=$("seg-voice"); sv.innerHTML="";
  app.state.voices.forEach(([id,label])=>{ const b=el("button",null,label);
    b.classList.toggle("on",id===app.state.voice);
    b.disabled=!app.state.audio_ok;
    b.onclick=async()=>{ app.state=await api("/api/settings",{voice:id}); renderSettings(); };
    sv.appendChild(b); });
  const stg=$("seg-theme"); stg.innerHTML="";
  app.state.themes.forEach(t=>{ const b=el("button",null,t==="light"?"Light":"Dark");
    b.classList.toggle("on",t===app.state.theme);
    b.onclick=async()=>{ app.state=await api("/api/settings",{theme:t}); applyTheme(); renderSettings(); };
    stg.appendChild(b); });
  const s=$("key-status");
  if (app.state.has_key){ s.textContent="✓ A key is saved on this computer."; s.className="small status ok"; }
  else { s.textContent="⚠ No key saved — Reading mode will use blank fields."; s.className="small status warn"; }
  $("btn-key-remove").style.display = app.state.has_key ? "" : "none";
  if (!app.state.audio_ok) {
    if (!$("voice-warn")) { const w=el("p","small status warn","⚠ Voice needs the edge-tts package (pip install edge-tts).");
      w.id="voice-warn"; $("seg-voice").after(w); }
  }
}
export function openSettings() {
  if (document.querySelector("dialog[open]")) return;   // don't stack over another dialog
  renderSettings(); $("dlg-settings").showModal();
}
export function wireSettings() {
  $("btn-settings").onclick=openSettings;
  $("btn-settings").title = "Settings ( , )";
  $("btn-settings-close").onclick=()=>$("dlg-settings").close();
  $("btn-key-save").onclick=async()=>{ const k=$("inp-key").value.trim(); if(!k) return;
    app.state=await api("/api/settings",{gemini_key:k}); $("inp-key").value=""; renderSettings(); softRefresh(); };
  $("btn-key-remove").onclick=async()=>{ app.state=await api("/api/settings",{gemini_key:""});
    renderSettings(); softRefresh(); };
}
function softRefresh(){ if(app.screen==="home") renderHome(); if(app.screen==="setup") renderSetup(); }
