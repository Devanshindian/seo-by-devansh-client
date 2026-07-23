"""Parse the DIRECT competitor domains from competitors.md; domain-suffix matching.
The one authoritative no-cite list = the '## Direct competitors' section of
`asset-engine/competitor-study/output/competitors.md` (path in config.COMPETITORS_MD).
Adjacent content leaders and any other competitor lists are intentionally IGNORED.

Reads: config.COMPETITORS_MD. Exposes: direct_domains() -> set, is_competitor(url, domains) -> bool.
"""
import re, os
from urllib.parse import urlparse
import config


def direct_domains():
    """Set of registrable domains from the '## Direct competitors' section only.
    Returns an empty set (filter drops nothing) if the file/section is missing — never crashes."""
    if not os.path.exists(config.COMPETITORS_MD):
        return set()
    md = open(config.COMPETITORS_MD, encoding="utf-8").read()
    if "## Direct competitors" not in md:
        return set()
    seg = md.split("## Direct competitors", 1)[1].split("\n## ", 1)[0]   # up to the next H2
    # each line is "- Name — domain.tld (desc)"; capture the domain right after the em-dash
    return set(re.findall(r"—\s*([a-z0-9.-]+\.[a-z]{2,})", seg))


def _reg(url):
    try:
        h = urlparse(url).netloc.lower()
    except Exception:
        return ""
    return h[4:] if h.startswith("www.") else h


def is_competitor(url, domains):
    """True if url's domain equals or is a subdomain of any competitor domain (blog.testgorilla.com → testgorilla.com)."""
    d = _reg(url)
    return bool(d) and any(d == c or d.endswith("." + c) for c in domains)
