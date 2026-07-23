#!/usr/bin/env python3
"""Shared helper — load the scraped Posts tab and render each post as a 'content card' string.
Used by 2a (phrases), 2c (assign), 2d (records). One place reads the xlsx (F1)."""
import os, sys
import config as c
import openpyxl


def load_posts():
    """Return the Posts tab as a list of dicts (every column), in sheet order."""
    if not os.path.exists(c.SCRAPE_XLSX):
        sys.exit(f"!! no scrape at {c.rel(c.SCRAPE_XLSX)} — run Phase A (reddit-scrape.py) first")
    ws = openpyxl.load_workbook(c.SCRAPE_XLSX, read_only=True)["Posts"]
    rows = list(ws.iter_rows(values_only=True))
    hdr = list(rows[0])
    return [dict(zip(hdr, r)) for r in rows[1:] if r[hdr.index("post_id")]]


def card(post, comment_chars=1400, body_chars=1200):
    """One post rendered as a compact content card for the LLM (title+body+image+top comments)."""
    def clip(x, n):
        x = (str(x) if x is not None else "").strip()
        return x[:n]
    return (f"### {post.get('post_id')} | r/{post.get('subreddit')} | "
            f"{post.get('score', 0)}up {post.get('comment_count', 0)}c\n"
            f"TITLE: {clip(post.get('title'), 300)}\n"
            f"BODY: {clip(post.get('body'), body_chars)}\n"
            f"IMG_TEXT: {clip(post.get('image_text'), 400)}\n"
            f"TOP_COMMENTS: {clip(post.get('top_comments'), comment_chars)}")
