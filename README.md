# SEO by Devansh — Content Research Machine

Automated SEO content research. Point it at a company's site and its idea list, and for each topic it produces a **write-ready research bundle**: the target keywords, the competitor gaps, a deep researched dossier, and an article blueprint a writer can build from.

## What's in here

- **`Backlink gets Automated/workflows/`** — the generalized, company-agnostic pipeline (all the code).
- **`Backlink gets Automated/projects/testlify/`** — a fully worked example company (Testlify): the idea list, ranking data, brand context, and the research bundles already produced.
- **`pillar-cluster-strategy/`** — the pillar/cluster content strategy.

## The main command: `/research`

Running the research conductor:

1. **Picks the next topic automatically** from the sheet — `projects/testlify/03-content-machine/research-log.csv`. Nothing to rebuild; it resumes where it left off.
2. Runs the chain: **DataForSEO** (keywords + competitors) → **cannibalization check** (do we already rank?) → **STORM** (deep researched dossier) → **gap-check** → **blueprint** → **write-ready bundle**.
3. Bundles land in `projects/testlify/03-content-machine/research-bundle/<slug>/`.

If a topic has no real keyword demand (an editorial idea), it is marked `skipped` with a remark and the run moves on — it never crashes the queue.

## One-time setup on your machine

The code and all data are in this repo, but a few environment things can't live in a repo:

1. **Rebuild the Python virtual environments.** They're excluded on purpose (a macOS venv won't run elsewhere). Each engine rebuilds from its `requirements.lock`; STORM has a ready script at `Backlink gets Automated/workflows/03-content-machine/11-storm/setup.sh`.
2. **Authenticate the Claude Code CLI.** Every AI step (research, scoring, the dossier, the bundle) runs on the local `claude` command, so it must be logged in.
3. **DataForSEO credits.** Credentials are in `Backlink gets Automated/.env`. **Rotate them** — they were shared with this repo.
4. **(Optional) `VOYAGE_API_KEY`.** Only needed to auto-generate *spokes* (sub-articles). Without it, article research works fully and spokes are simply skipped — nothing breaks.

## Big files (Git LFS)

Two data files are over GitHub's 100MB limit and are stored with **Git LFS**: `content-database.csv` and `traffic-raw.json`. After cloning:

```bash
brew install git-lfs   # if not already installed
git lfs install
git lfs pull            # download the two large data files
```
