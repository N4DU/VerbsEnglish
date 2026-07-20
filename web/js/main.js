/* Entry point. Loads state, wires the header, registers the keyboard handler
   (via the import side-effect), and shows the home screen. */
import { $, app, api, applyTheme, toast } from "./core.js";
import { renderHome } from "./home.js";
import { wireSettings } from "./settings.js";
import "./keyboard.js";   // registers the global keydown listener

async function boot() {
  try { app.state = await api("/api/state"); }
  catch(e) { toast("Could not reach the local server — is python main.py running?"); return; }
  applyTheme(); wireSettings();
  $("brand-home").onclick = renderHome;
  renderHome();
}
boot();
