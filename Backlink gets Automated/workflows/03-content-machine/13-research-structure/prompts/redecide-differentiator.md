You are deciding which sections of ONE article are TRUE DIFFERENTIATORS — the FEW sections that carry OUR unique
angle or cover a gap competitors DON'T. Be strict: most sections are standard coverage (table stakes) and are
NOT differentiators. Flag a section true ONLY if it clearly matches our distinct angle OR a listed gap that
competitors don't already cover.

OUR DISTINCT ANGLE (what makes THIS article different):
{{ANGLE}}

WHAT COMPETITORS ALREADY COVER (table stakes — a section that only does these is NOT a differentiator):
{{COMPETITOR_TOPICS}}

GAPS WE CAN OWN (strong differentiator signal — a section that covers one of these usually IS a differentiator):
{{GAPS}}

THE SECTIONS (index, H2, and its sub-headings):
{{SECTIONS}}

For EACH section index, decide is_differentiator true/false — judged against the angle + gaps, NOT against
generic topic coverage. Return STRICT JSON only:
{"sections":[{"index":0,"is_differentiator":false,"why":"one line tying the verdict to the angle/gap or to table-stakes"}]}
