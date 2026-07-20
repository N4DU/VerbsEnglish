#!/usr/bin/env python3
"""Verb Practice — an English verb trainer for Spanish speakers.

Run:  python main.py

Starts a small local web server (standard library only — nothing leaves your
computer except the optional Gemini / TTS requests) and opens the app in your
browser.  Your computer is the server; the browser is just the interface.

All the real code lives in the `verbs` package:
    verbs/paths.py    where user data is stored
    verbs/data.py     verb lists and constants
    verbs/store.py    progress, word layout, answer rules
    verbs/phrases.py  Gemini fill-in-the-blank sentence cache (lazy import)
    verbs/audio.py    edge-tts voice generation (lazy import)
    verbs/server.py   the HTTP server and API
"""
from verbs.server import main

if __name__ == "__main__":
    main()
