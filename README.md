# Verb Practice

Práctica de verbos en inglés (regulares e irregulares) con dos maneras de aprender,
integradas en una misma app web local:

- **Reading** — completa la frase: aparece una oración con un hueco `___`
  (generada con Gemini AI) y escribes la forma del verbo que corresponde.
- **Listening** — escucha y escribe: cada forma del verbo suena en audio
  (en orden mezclado, sin etiqueta) y tienes que escribir la palabra que oíste.
  Al comprobar, el icono ♫ revela qué forma era (*Base form*, *Past simple*,
  *Past participle*). La palabra en español puede quedarse como pista pequeña
  o desactivarse.

El modo se elige con una sola opción ("Mode") en la pantalla de configuración.

## Cómo funciona

Tu computadora es el servidor y el navegador es la interfaz. `python main.py`
levanta un servidor web local (solo con la librería estándar) y abre la app en
tu navegador. Nada sale de tu computadora salvo las peticiones opcionales a
Gemini (frases) y al servicio de voz (audio).

## Instalación

```
pip install -r requirements.txt
python main.py
```

Las dependencias son **opcionales**: sin ellas la app funciona igual (lectura
con campos en blanco y escucha sin voz). Se cargan solo cuando de verdad
practicas, así que el arranque es instantáneo.

La API key de Gemini (gratuita, de
[Google AI Studio](https://aistudio.google.com/apikey)) se configura **desde la
propia app**, en **⚙ Settings** — se guarda solo en tu computadora, en
`config.json`. También puedes usar la variable de entorno `GEMINI_API_KEY`.

## Controles

Todo se maneja con teclado (y también con mouse/touch):

| Tecla | Acción |
|---|---|
| ↑ ↓ ← → | Navegar / mover |
| Enter | Seleccionar / comprobar respuesta |
| Espacio | Activar/desactivar · oír de nuevo (Listening) |
| `,` | Abrir Settings (desde cualquier pantalla) |
| Esc | Volver atrás |

En **Edit word list** eliges qué palabras practicar, las reordenas (→ para
tomar una y ↑↓ para deslizarla) y borras con `Del` / `⌫`. Todo se guarda solo
en `progress.json`.

## Estructura del código

Backend (paquete `verbs/`), pensado para arrancar rápido — nada pesado se
importa hasta que hace falta:

| Archivo | Contenido |
|---|---|
| `main.py` | Punto de entrada — lanza el servidor |
| `verbs/paths.py` | Dónde se guardan los datos (progreso, config, cachés) |
| `verbs/data.py` | Listas de verbos, significados y constantes |
| `verbs/store.py` | Progreso, distribución de palabras y reglas de respuesta |
| `verbs/phrases.py` | Caché de frases con Gemini AI (import perezoso) |
| `verbs/audio.py` | Voz con edge-tts y caché en disco (import perezoso) |
| `verbs/server.py` | Servidor HTTP y API |

Frontend (`web/`), un módulo por pantalla:

| Archivo | Contenido |
|---|---|
| `web/index.html`, `web/style.css` | Estructura y estilos |
| `web/js/core.js` | Utilidades compartidas, estado y ruteo de vistas |
| `web/js/home.js`, `setup.js`, `editor.js`, `practice.js` | Cada pantalla |
| `web/js/settings.js`, `confirm.js` | Diálogos |
| `web/js/keyboard.js` | Atajos globales de teclado |
| `web/js/main.js` | Arranque de la interfaz |

Los audios se guardan en `audio_cache/` (se crea sola); si cambias palabras,
los audios de palabras eliminadas se limpian automáticamente al arrancar.
