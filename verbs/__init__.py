"""Verb Practice — English verb trainer for Spanish speakers.

The package is import-light on purpose: nothing here pulls in edge-tts or
google-genai at import time, so `python main.py` starts almost instantly.
Those heavy dependencies load lazily, only when you actually practise.
"""
__version__ = "2.0"
