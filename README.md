# SEO by Devansh — Content Research and Writing Machine

Point it at a company's site and its idea list, and for each topic it produces a **finished article**: the target keywords, the competitor gaps, a deep researched dossier, an article blueprint, and the written piece itself.

**The six finished articles are live here:** https://devanshindian.github.io/testlify-articles-0c27c5a4/

## What's in here

- **`Backlink gets Automated/workflows/`** — the generalised, company-agnostic pipeline, all the code. Five layers, numbered in run order: `00-foundation`, `01-brand-context`, `02-asset-engine`, `03-content-machine`, `04-write-phase`.
- **`Backlink gets Automated/projects/testlify/`** — one worked example company: its idea list, ranking data, brand context, research bundles, and the six finished articles.
- **`pillar-cluster-strategy/`** — the pillar and cluster content strategy.

## The two commands

**`/research`** turns a topic into a write-ready bundle. It picks the next topic from `projects/testlify/03-content-machine/research-log.csv`, then runs DataForSEO for keywords and competitors, a cannibalisation check, STORM for the deep dossier, a gap check, and finally the blueprint. Bundles land in `03-content-machine/research-bundle/<slug>/`.

A topic with no real keyword demand is marked `skipped` with a remark and the run moves on. It never crashes the queue.

**`/writer`** turns that bundle into a finished article, in four stations: planner, architect, field, writer. The writer itself is nine steps, ending in `readable`, which rewrites the whole piece for a human reader. Output lands in `04-write-phase/out/<slug>/`.

## The six articles

Each one in `04-write-phase/out/<slug>/` contains:

| File | What it is |
|---|---|
| `share/<slug>.md` and `.html` | the finished article, clean, no machinery |
| `writer/draft.md` | the same article with its source markers |
| `planner/`, `architect/`, `writer/` review pages | how each stage decided what it did |
| `index.html` | a per-article index linking all of the above |

The slugs: `a-hiring-assessment-glossary-built`, `ai-recruitment-tools-that-can`, `the-real-cost-recruitment-2026`, `the-resume-statistics-everyone-cites`, `the-validity-numbers-adverse-impact-data`, `video-interview-software-that-actually`.

## What this repo deliberately does NOT contain

Pipeline intermediates are excluded: `_work/` folders, `.npy` embedding caches, `.sqlite` caches, and STORM's per-call debug transcripts. They were 780 MB of machine chatter burying the 40 MB anyone actually reads, and every one of them regenerates from the code that is here.

If you need them, rerun the step that makes them. Nothing here depends on them being present.

## One-time setup on your machine

The code and data are in this repo, but a few things cannot live in one:

1. **Rebuild the Python virtual environments.** Excluded on purpose, since a macOS venv will not run elsewhere. Each engine rebuilds from its `requirements.lock`; STORM has a ready script at `workflows/03-content-machine/11-storm/setup.sh`.
2. **Authenticate the Claude Code CLI.** Every AI step runs on the local `claude` command, so it must be logged in.
3. **DataForSEO credits.** Credentials sit in `Backlink gets Automated/.env`. **Rotate them.** They were shared with this repo, so treat them as burned.
4. **(Optional) `VOYAGE_API_KEY`.** Only needed to auto-generate spokes, the sub-articles under a pillar. Without it, article research works fully and spokes are skipped.

## The one big file (Git LFS)

`content-database.csv` is over GitHub's 100 MB limit and is stored with **Git LFS**. After cloning:

```bash
brew install git-lfs   # if not already installed
git lfs install
git lfs pull
```
