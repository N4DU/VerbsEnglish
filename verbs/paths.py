"""Filesystem locations.

Every piece of user data (progress, config, caches) lives at the project
root — next to main.py — so it stays put no matter where the package is
imported from.  Paths are anchored to the repo root, not to this module.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WEB_DIR   = ROOT / "web"
PROG_F    = ROOT / "progress.json"
PHRA_F    = ROOT / "phrases_cache.json"
CONF_F    = ROOT / "config.json"
AUDIO_DIR = ROOT / "audio_cache"
