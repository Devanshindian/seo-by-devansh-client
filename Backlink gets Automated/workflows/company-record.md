---
type: standard (the company record — the tenant contract every engine reads)
reusable: any company
reads: nothing (this IS the schema; instances are filled at onboarding)
produces: the contract for projects/<company>/company.json — one instance per company
last_updated: 2026-07-18
---

# The company record — `projects/<company>/company.json`

## What this is

The ONE file holding every **company-level fact** the research engines need. Every engine reads it; no engine
ever hardcodes a company fact again. One instance per company, always at `projects/<company>/company.json`.
The `COMPANY` environment variable picks which company's folder (and therefore which record) a run uses.

**The rule that governs it (single source of truth, F1):** a fact lives HERE and nowhere else. If a value is
also needed in a prompt, the prompt carries a placeholder (`{{BRAND}}`, `{{NICHE_DEFINITION}}`, `{{DOMAIN}}`)
that the engine fills from this record at run time.

**Fail closed:** for any company other than the bootstrap default, a missing record stops the run loudly at the
engine boundary. A run must never silently fall through to another company's values.

**Secrets NEVER live here.** This file is committed to git. API logins (`DFS_LOGIN`/`DFS_PW`,
`VOYAGE_API_KEY`) stay in git-ignored `.env` files / environment variables (convention D3).

## The fields

| Field | What it means | Who provides it |
|---|---|---|
| `company` | The folder slug — lowercase, matches `projects/<company>/` | Human, at onboarding |
| `brand` | The display name used in prompts ("Testlify", not "testlify") | Human, at onboarding |
| `brand_oneliner` | One sentence: what the company sells. Fed to every relevance judge | Human today; from Phase 3 the **brand-voice builder drafts it** from the company's pages and the human confirms |
| `domain` | The company's own website domain. Used for "are WE cited?" checks — never assumed to be `<brand>.com` | Human, at onboarding |
| `wordpress_url` | The site base URL for the WordPress content pull | Human, at onboarding |
| `location` | The audience market (DataForSEO `location_name`, e.g. "United States") | Human, at onboarding |
| `language` | The audience language code (e.g. "en") | Human, at onboarding |
| `niche_definition` | One sentence: what counts as ON-TOPIC for this company. Steers seed vetting and keyword judging | Human today; drafted by the brand-voice builder from Phase 3, human-confirmed |

**What does NOT belong here (decided 2026-07-18):** engine thresholds — the keyword volume floor, the
keyword-difficulty ceiling, the paid-run credit guard, batch sizes, depths. Those are **method knobs**, not
company facts; they live in each engine's `config.py` (one constant pair everywhere: volume ≥ 100, KD ≤ 40).
The record holds ONLY brand identity: who the company is, what it sells, where it plays.

Underscore-prefixed keys (`_what`, …) are comments for humans — engines ignore them.

The schema is **versioned by growth**: as Phase 3 scripts the onboarding builders, new company facts they
surface join this table (and every instance file) deliberately — see revamp-phase-plan.md Phase 3.4.

## The template (copy per company, fill every field)

```json
{
  "company": "<slug>",
  "brand": "<Display Name>",
  "brand_oneliner": "<Brand — what it sells, one sentence>",
  "domain": "<example.com>",
  "wordpress_url": "https://<example.com>",
  "location": "<United States>",
  "language": "<en>",
  "niche_definition": "<one sentence: what is on-topic for this company>"
}
```

## Worked instance

`projects/testlify/company.json` — the first instance, bootstrapped by lifting the values that previously sat
in engine code (each value's origin is documented inside the file itself).
