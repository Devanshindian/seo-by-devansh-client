"""Step 1 (STORM) — turn STORM dossiers into cards.
For the hub dossier AND every gap-fill iteration: split the polished article on its top-level (#) sections,
run one parallel call per section to emit cards, verify each verbatim really exists, and resolve its [n]
markers to source URLs via that dossier's url_to_info.json.

Card: { id, gloss, verbatim, source_urls[], internal_link=None, tag="storm", origin }
"""
import os, re, sys, json, glob
from concurrent.futures import ThreadPoolExecutor
import config, llm

TEMPLATE = llm.load_prompt("harvest-storm.md")
_CITE = re.compile(r"\[(\d+)\]")


def _norm(s):
    """Normalise for the verbatim-exists check: collapse whitespace, unify quotes."""
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip().lower()


def _load_citations(dossier_dir):
    """{n: {url, title}} from url_to_info.json (url_to_unified_index inverted + titles)."""
    p = os.path.join(dossier_dir, "url_to_info.json")
    if not os.path.exists(p):
        return {}
    d = json.load(open(p))
    idx = d.get("url_to_unified_index", {})
    info = d.get("url_to_info", {})
    out = {}
    for url, n in idx.items():
        out[int(n)] = {"url": url, "title": (info.get(url, {}) or {}).get("title", "")}
    return out


def _split_sections(text):
    """Split on top-level '# ' headings -> [{title, text}]. Skip the polish 'summary' lead."""
    sections, title, buf = [], None, []
    for line in text.splitlines():
        m = re.match(r"^#\s+(.*)", line)          # single-hash top-level only
        if m and not line.startswith("##"):
            if title is not None:
                sections.append({"title": title, "text": "\n".join(buf).strip()})
            title, buf = m.group(1).strip(), []
        else:
            buf.append(line)
    if title is not None:
        sections.append({"title": title, "text": "\n".join(buf).strip()})
    return [s for s in sections if s["text"] and s["title"].lower() != "summary"]


def _dossier_dirs(topic_dir):
    """The hub dossier + any iteration-<n>/ dirs under it."""
    dirs = [topic_dir]
    dirs += sorted(glob.glob(os.path.join(topic_dir, "iteration-*")))
    return [d for d in dirs if os.path.exists(os.path.join(d, "storm_gen_article_polished.txt"))]


def _extract_section(sec):
    """Extract cards from one section. Re-run up to HARVEST_RETRIES extra times if it yields nothing."""
    prompt = TEMPLATE.replace("{{SECTION_TITLE}}", sec["title"]).replace("{{SECTION_TEXT}}", sec["text"])
    for _ in range(config.HARVEST_RETRIES + 1):
        try:
            out = llm.call_json(prompt)
            if out:
                return out
        except Exception:
            pass
    print(f"    !! section '{sec['title'][:45]}' produced NO cards after {config.HARVEST_RETRIES + 1} tries")
    return []


def harvest(topic_dir):
    cards, dropped, failed = [], 0, []
    for dd in _dossier_dirs(topic_dir):
        name = os.path.basename(dd)
        text = open(os.path.join(dd, "storm_gen_article_polished.txt")).read()
        cites = _load_citations(dd)
        sections = _split_sections(text)
        print(f"  dossier {name}: {len(sections)} sections")
        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as ex:
            raw = list(ex.map(lambda s: (s, _extract_section(s)), sections))
        for sec, out in raw:
            if not out:
                failed.append(f"{name}/{sec['title'][:45]}")
            norm_sec = _norm(sec["text"])
            for c in out:
                vb = (c.get("verbatim") or "").strip()
                gloss = (c.get("gloss") or "").strip()
                if not vb or not gloss:
                    continue
                if _norm(vb) not in norm_sec:            # anti-hallucination: must really exist
                    dropped += 1
                    continue
                urls = []
                for n in {int(x) for x in _CITE.findall(vb)}:
                    if n in cites:
                        urls.append(cites[n]["url"])
                cards.append({"gloss": gloss, "verbatim": vb, "source_urls": urls,
                              "internal_link": None, "tag": "storm",
                              "origin": f"storm/{name}/{sec['title'][:50]}"})
    print(f"  STORM: {len(cards)} cards ({dropped} dropped for not matching source)")
    if failed:
        print(f"  !! STORM: {len(failed)} section(s) produced NO cards after retries: {failed}")
    return cards


if __name__ == "__main__":
    topic_dir, out_path = sys.argv[1], sys.argv[2]
    cards = harvest(topic_dir)
    for i, c in enumerate(cards, 1):                     # continuous ids (STORM is first)
        c["id"] = i
    config.write_json(out_path, cards)
    print(f"-> {out_path}")
    for c in cards[:5]:
        print(f"  [{c['id']}] {c['gloss'][:70]}  (src: {len(c['source_urls'])})")
