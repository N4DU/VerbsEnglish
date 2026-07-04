# Verb Practice

Práctica de verbos en inglés (regulares e irregulares) con dos maneras de aprender,
integradas en un mismo programa:

- **Reading** — completa la frase: aparece una oración con un hueco `___`
  (generada con Gemini AI) y escribes la forma del verbo que corresponde.
- **Listening** — escucha y escribe: cada forma del verbo suena en audio
  (en orden mezclado, sin etiqueta) y tienes que escribir la palabra que oíste.
  Al comprobar, el icono ♫ revela qué forma era (*Base form*, *Past simple*,
  *Past participle*). La palabra en español puede quedarse como pista pequeña
  o desactivarse.

El modo se elige con una sola opción ("Mode") en la pantalla de configuración.

## Instalación

```
pip install -r requirements.txt
python main.py
```

`tkinter` viene incluido con Python (en Linux: `sudo apt install python3-tk`).

Para las frases del modo Reading necesitas una API key gratuita de
[Google AI Studio](https://aistudio.google.com/apikey) en `config.json`:

```json
{ "gemini_api_key": "TU_KEY_AQUI" }
```

Sin key el programa funciona igual (práctica sin frases, y el modo Listening
no la necesita).

## Controles

| Tecla | Acción |
|---|---|
| ↑ ↓ ← → | Navegar / mover |
| Enter | Seleccionar / comprobar respuesta |
| Espacio | Marcar casillas |
| Esc | Volver / opciones |
| A (en la lista de palabras) | Activar/desactivar un bloque entero |
| F8 | Ventana siempre visible |

En **Edit word list** eliges qué palabras practicar y las mueves de bloque
con ← →. Todo se guarda solo en `progress.json`.

## Archivos del código

| Archivo | Contenido |
|---|---|
| `main.py` | Punto de entrada — el que se ejecuta |
| `verbs_app.py` | Interfaz y lógica de sesión |
| `verbs_data.py` | Listas de verbos, temas y constantes |
| `verbs_audio.py` | Voz: generación, caché en disco y reproducción segura |
| `verbs_phrases.py` | Caché de frases con Gemini AI |

Los audios se guardan en `audio_cache/` (se crea sola); si cambias palabras,
los audios de palabras eliminadas se limpian automáticamente al arrancar.
