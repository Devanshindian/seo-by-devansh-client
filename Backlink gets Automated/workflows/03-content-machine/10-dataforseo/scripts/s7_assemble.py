#!/usr/bin/env python3
"""Step 7 — assemble the section files into the reader-first brief + the agent-commentary notes.
PURE ASSEMBLY: the Keywords / SERP snapshot / Winners / AEO sections are LIFTED VERBATIM from their proof files
(every bullet preserved — no re-summarizing, no inline-compression). The LLM writes ONLY the two synthesis blocks
that don't exist in proof: the Verdict + the Build spec.

Reads:  <run_dir>/proof/{03-keywords,04-serp-snapshot,05-winners,06-aeo}.md + config.CHECKLIST + pool/shortlist sizes.
Writes: <run_dir>/research-doc-<slug>.md · <run_dir>/research-notes.md
"""
import os, re, sys, json, argparse
import config, llm

ASSEMBLE = llm.load_prompt("assemble.md")   # now returns {verdict, build_spec} only
NOTES = llm.load_prompt("notes.md")


def _read(path, fallback=""):
    return open(path).read() if os.path.exists(path) else fallback


def _lift(path, header):
    """Lift a section file VERBATIM under `header`. Only strip: the machine-only ```readlist fenced block and the
    file's own leading ### heading. Everything else (every bullet, table, note) is kept exactly."""
    txt = _read(path)
    txt = re.sub(r"```readlist.*?```", "", txt, flags=re.S).strip()   # drop the machine block only
    lines = txt.splitlines()
    if lines and lines[0].lstrip().startswith("#"):   # drop the file's own heading; we add our own
        lines = lines[1:]
    return header + "\n\n" + "\n".join(lines).strip()


def _pool_stats(proof):
    def _n(f):
        try: return len(json.load(open(os.path.join(proof, f))))
        except Exception: return "?"
    return f"pool {_n('01-pool.json')} -> shortlist {_n('02-shortlist.json')}"


def _completeness(proof, asset, angle, verdict, build_spec):
    """Compute each box against the artefact it claims, and return (markdown, failed_labels).

    A box is ticked ONLY when its check passes. A claim we cannot verify from here (e.g. "nothing was
    dropped upstream") is not emitted at all — an unverifiable tick is a lie, not a checklist.
    """
    def filled(name):
        return bool(_read(os.path.join(proof, name)).strip())

    checks = [
        ("Anchors (title + distinct angle)", bool(asset.strip()) and bool(angle.strip())),
        ("Keywords — primary + variations + secondaries + in-body", filled("03-keywords.md")),
        ("SERP snapshot · PAA · related", filled("04-serp-snapshot.md")),
        ("What the winners cover + gaps", filled("05-winners.md")),
        ("AI answer landscape status", filled("06-aeo.md")),
        ("Verdict", bool(verdict)),
        ("Build spec", bool(build_spec)),
    ]
    md = "\n".join(f"- [{'x' if ok else ' '}] {label}" for label, ok in checks)
    return md, [label for label, ok in checks if not ok]


def run(run_dir, slug, asset, angle):
    proof = os.path.join(run_dir, "proof")
    kw = _read(os.path.join(proof, "03-keywords.md"))
    serp = _read(os.path.join(proof, "04-serp-snapshot.md"))
    win = _read(os.path.join(proof, "05-winners.md"))
    aeo = _read(os.path.join(proof, "06-aeo.md"))
    checklist = _read(config.CHECKLIST)

    # LLM: ONLY the Verdict + Build spec (the parts not in any proof file)
    ap = (ASSEMBLE.replace("{{BRAND}}", config.BRAND).replace("{{ASSET_TOPIC}}", asset)
          .replace("{{DISTINCT_ANGLE}}", angle).replace("{{KEYWORDS}}", kw)
          .replace("{{SERP_SNAPSHOT}}", serp).replace("{{WINNERS}}", win).replace("{{CHECKLIST}}", checklist))
    syn = llm.call_json(ap)
    verdict = (syn.get("verdict") or "").strip()
    build_spec = (syn.get("build_spec") or "").strip()

    short = asset.split(":")[0].strip()
    proof_map = ("\n".join([
        "| Section | Proof |", "|---|---|",
        "| Keywords | `03-keywords.md`, `spoke-candidates.md` |",
        "| SERP snapshot | `04-serp-snapshot.md` |",
        "| What the winners cover | `05-winners.md` |",
        "| AI answer landscape | `06-aeo.md` |",
        "| Build spec | `seo-aeo-geo-checklist.md` |"]))
    completeness, missing = _completeness(proof, asset, angle, verdict, build_spec)

    # ---- assemble the doc in CODE (verbatim lifts; LLM only for verdict/build_spec) ----
    doc = "\n\n".join([
        f"# Research doc — {short}",
        f"> **Asset:** {asset}\n>\n> **Distinct angle:** {angle}",
        "---",
        "## Verdict\n\n" + verdict,
        _lift(os.path.join(proof, "03-keywords.md"), "## Keywords"),
        _lift(os.path.join(proof, "04-serp-snapshot.md"), "## SERP snapshot"),
        _lift(os.path.join(proof, "05-winners.md"), "## What the winners cover"),
        _lift(os.path.join(proof, "06-aeo.md"), "## AI answer landscape"),
        "## Build spec\n\n" + build_spec,
        "---",
        "## Proof map (traceability)\n\n" + proof_map,
        "## Completeness (computed at assembly — each box is a real check)\n\n" + completeness,
    ])
    doc_path = os.path.join(run_dir, f"research-doc-{slug}.md")
    config.write_text(doc_path, doc.rstrip() + "\n")
    if missing:
        print(f"  !! INCOMPLETE brief — {len(missing)} check(s) failed: {'; '.join(missing)}", file=sys.stderr)

    npt = (NOTES.replace("{{ASSET_TOPIC}}", asset)   # notes.md has no {{BRAND}} slot — no-op fill removed
           .replace("{{DISTINCT_ANGLE}}", angle).replace("{{KEYWORDS}}", kw)
           .replace("{{POOL_STATS}}", _pool_stats(proof)).replace("{{SERP_SNAPSHOT}}", serp)
           .replace("{{WINNERS}}", win).replace("{{AEO}}", aeo))
    notes = llm.call_text(npt)
    config.write_text(os.path.join(run_dir, "research-notes.md"), notes.rstrip() + "\n")

    print(f"  -> {os.path.basename(doc_path)} + research-notes.md  (sections lifted verbatim)")
    return doc_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir"); ap.add_argument("--slug", required=True)
    ap.add_argument("--asset", required=True); ap.add_argument("--angle", default="")
    a = ap.parse_args()
    run(a.run_dir, a.slug, a.asset, a.angle)
