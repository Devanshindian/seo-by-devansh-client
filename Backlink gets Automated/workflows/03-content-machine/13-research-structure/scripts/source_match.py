#!/usr/bin/env python3
"""Recover the real source URL for a STORM card whose sentence had no [n] footnote, by matching its text
against the snippets STORM already stored in url_to_info.json. Offline, free, honest: a URL is attached ONLY
when a specific snippet genuinely contains the fact (a shared lifted phrase that INCLUDES the number).

Shared by harvest_storm.py (fix at origin, future articles) and reattach_sources.py (patch existing bundles).

Public API:
    load_snippets(storm_dir)                     -> index (list of (url, snippet, shingles))
    has_number(text)                             -> bool
    recover(verbatim, index, min_overlap=3)      -> (url, evidence_phrase) or (None, None)
"""
import re
import json
import os
import glob

# --- normalization: make "$4,683" == "$4 683", "impact: 40%" == "Impact 40%" -----------------
def _norm(s):
    s = (s or "").lower()
    s = re.sub(r"(\d),(\d)", r"\1\2", s)      # 4,683 -> 4683  (kill thousands separators)
    s = re.sub(r"[^a-z0-9%]+", " ", s)         # punctuation -> space, keep digits + %
    return re.sub(r"\s+", " ", s).strip()

def _tokens(s):
    return _norm(s).split()

def _shingles(s, n=3):
    w = _tokens(s)
    return set(tuple(w[i:i + n]) for i in range(len(w) - n + 1))

_NUMTOK = re.compile(r"\d")
def _is_num_token(tok):
    return bool(_NUMTOK.search(tok)) and len(re.sub(r"[^\d]", "", tok)) >= 2   # ignore 1-digit noise

_NUM = re.compile(r"\$?\d[\d,]*(?:\.\d+)?\s?%?")
def has_number(text):
    return any(len(re.sub(r"[^\d]", "", m)) >= 2 for m in _NUM.findall(text or ""))


def load_snippets(storm_dir):
    """Every snippet STORM stored under this topic dir (all iterations), as (url, snippet, shingle_set)."""
    index = []
    for p in glob.glob(os.path.join(storm_dir, "**", "url_to_info.json"), recursive=True):
        try:
            d = json.load(open(p))
        except Exception:
            continue
        info = d.get("url_to_info", {}) if isinstance(d, dict) else {}
        for url, v in info.items():
            for s in (v.get("snippets", []) if isinstance(v, dict) else []):
                if isinstance(s, str) and s.strip():
                    index.append((url, s, _shingles(s)))
    return index


def _num_windows(cn, pad=16):
    """~32-char windows of the normalized card centered on each number — the number plus its context.
    Kept only if the window carries >= 2 alphabetic tokens (so it's a real phrase, not a bare figure)."""
    for m in re.finditer(r"\d[\d]*%?", cn):
        w = cn[max(0, m.start() - pad):min(len(cn), m.end() + pad)].strip()
        if len([t for t in w.split() if t.isalpha()]) >= 2:
            yield w


def recover(verbatim, index, min_overlap=3):
    """Attach a source ONLY when a specific snippet proves the fact. Two honest signals, either suffices:
      (A) the card shares >= min_overlap 3-grams with a snippet, and at least one shared 3-gram carries the number
          (handles long, paraphrased-but-lifted sentences);
      (B) a number-centered window of the card (the figure + its surrounding words) appears verbatim inside a
          snippet (handles short table/list rows like "| Non-executive | ~$4,683 |" that can't reach 3 3-grams).
    Returns (url, evidence_phrase) or (None, None)."""
    cs = _shingles(verbatim)
    if not cs:
        return None, None

    # --- signal A: 3-gram overlap that includes the number ---
    best_url, best_ov, best_shared = None, 0, None
    for url, _snip, ss in index:
        shared = cs & ss
        if len(shared) > best_ov:
            best_url, best_ov, best_shared = url, len(shared), shared
    if best_ov >= min_overlap and any(any(_is_num_token(t) for t in g) for g in best_shared):
        phrase = " ".join(sorted(best_shared, key=lambda g: -sum(_is_num_token(t) for t in g))[0])
        return best_url, phrase

    # --- signal B: number-window appears verbatim in a snippet (for short high-value rows) ---
    cn = _norm(verbatim)
    windows = list(_num_windows(cn))
    for url, snip, _ss in index:
        sn = _norm(snip)
        for w in windows:
            if w in sn:
                return url, w
    return None, None
