#!/usr/bin/env python3
"""Verb Practice — entry point.

Run:  python VerbsEnglish.py

The code lives in:
  verbs_data.py     verb lists, themes, constants
  verbs_audio.py    text-to-speech (edge-tts + pygame)
  verbs_phrases.py  sentence cache backed by Gemini AI
  verbs_app.py      the application (UI + session logic)
"""
from verbs_app import App

if __name__ == "__main__":
    App().run()
