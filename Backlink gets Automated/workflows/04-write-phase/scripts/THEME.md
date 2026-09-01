<!-- sutra-managed: theme v3 -->
```space-style
/* Sutra theme v3 — generated from panel.css tokens (2.224.x). Keyed on SB's own
   html[data-theme], which SilverBullet derives from prefers-color-scheme; the
   desktop shell drives that scheme via nativeTheme (sutra:theme IPC), so the
   iframe follows the panel toggle. Values are MIRRORED panel tokens — the
   iframe is cross-origin and cannot read the panel's variables. */
html[data-theme="light"] {
  --root-background-color: #ffffff;   /* panel --surface (doc column) */
  --root-color: #1c1917;              /* panel --ink */
  --ui-accent-color: #8A5D2E;         /* panel --acc */
  --top-background-color: #ffffff;
  --ui-font: -apple-system, "Segoe UI", Roboto, sans-serif;
  --editor-font: -apple-system, "Segoe UI", Roboto, sans-serif;
}
html[data-theme="dark"] {
  --root-background-color: #161412;   /* panel --surface */
  --root-color: #F5F0E8;              /* panel --ink */
  --ui-accent-color: #C4956A;         /* panel --acc */
  --top-background-color: #161412;
  --ui-font: -apple-system, "Segoe UI", Roboto, sans-serif;
  --editor-font: -apple-system, "Segoe UI", Roboto, sans-serif;
}
/* The panel renders its own breadcrumb, title context and save state (mock 07),
   so SB's top bar duplicates chrome the design does not have. NARROW selector,
   pinned to SB 2.10.0 (#sb-top verified in its DOM); a broader selector could
   swallow a future read-only or error affordance. Editing and autosave do not
   depend on the bar (verified: PUT persists with it hidden). */
#sb-top { display: none; }
/* Serif headings per the locked mock (panel --serif stack). Pinned-version
   compatibility selectors: SB 2.10.0 renders headings as .sb-line-h1/h2/h3. */
#sb-editor .sb-line-h1, #sb-editor .sb-line-h2, #sb-editor .sb-line-h3 {
  font-family: ui-serif, "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
}
/* v3 (reviewer round-3 minor 3): the EDIT surface reads at the same scale as
   the panel's read view — 13.5px proportional body, mock-07's restraint —
   instead of the stock oversized editor face. Pinned to SB 2.10.0's editor
   container; code blocks keep mono via SB's own inner classes. */
#sb-editor .cm-editor { font-size: 13.5px; line-height: 1.65; }
#sb-editor .cm-content { padding-top: 8px; }
```
