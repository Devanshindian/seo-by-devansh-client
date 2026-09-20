import json
import logging
import os
import re
from typing import Union, List

import dspy
import requests
from bs4 import BeautifulSoup

from ... import brief

# Our researcher-picker prompt (LOCAL PATCH 2026-08-03) lives with the other tool prompts:
# modules/ -> storm_wiki -> knowledge_storm -> engine -> 11-storm -> prompts/pick-researchers.md
_PROMPTS_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "prompts"))


def _extract_json(text):
    """First balanced JSON object/array in `text`, tolerating ```json fences and stray prose."""
    t = text.strip()
    if "```" in t:
        for p in t.split("```"):
            p = p.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            if p.startswith("{") or p.startswith("["):
                t = p
                break
    start = next((i for i, c in enumerate(t) if c in "{["), None)
    if start is None:
        raise ValueError("no JSON found in model output")
    open_ch, close_ch = t[start], ("}" if t[start] == "{" else "]")
    depth, in_str, esc = 0, False, False
    for i in range(start, len(t)):
        c = t[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return json.loads(t[start:i + 1])
    raise ValueError("unbalanced JSON in model output")


def get_wiki_page_title_and_toc(url):
    """Get the main title and table of contents from an url of a Wikipedia page."""

    # Wikipedia now returns 403 to requests with no descriptive User-Agent -> no <h1> -> the persona
    # step degrades to "N/A" personas (thin article downstream). Send a UA. (First-party fix, 2026-07-13.)
    # LOCAL PATCH (revamp Phase 1.6): the UA is tenant-branded via the RESEARCH_UA env (set by run_storm.py
    # from the company record) — it was hardcoded TestlifyResearch, announcing every tenant as Testlify.
    import os as _os
    response = requests.get(url, headers={
        "User-Agent": _os.environ.get("RESEARCH_UA",
            "Mozilla/5.0 (compatible; ContentResearchBot/1.0)")})
    soup = BeautifulSoup(response.content, "html.parser")

    # Get the main title from the first h1 tag
    h1 = soup.find("h1")
    if h1 is None:
        raise ValueError(f"no <h1> for {url} (status {response.status_code})")
    main_title = h1.text.replace("[edit]", "").strip().replace("\xa0", " ")

    toc = ""
    levels = []
    excluded_sections = {
        "Contents",
        "See also",
        "Notes",
        "References",
        "External links",
    }

    # Start processing from h2 to exclude the main title from TOC
    for header in soup.find_all(["h2", "h3", "h4", "h5", "h6"]):
        level = int(
            header.name[1]
        )  # Extract the numeric part of the header tag (e.g., '2' from 'h2')
        section_title = header.text.replace("[edit]", "").strip().replace("\xa0", " ")
        if section_title in excluded_sections:
            continue

        while levels and level <= levels[-1]:
            levels.pop()
        levels.append(level)

        indentation = "  " * (len(levels) - 1)
        toc += f"{indentation}{section_title}\n"

    return main_title, toc.strip()


class FindRelatedTopic(dspy.Signature):
    """I'm writing a Wikipedia page for a topic mentioned below. Please identify and recommend some Wikipedia pages on closely related subjects. I'm looking for examples that provide insights into interesting aspects commonly associated with this topic, or examples that help me understand the typical content and structure included in Wikipedia pages for similar topics.
    Please list the urls in separate lines."""

    topic = dspy.InputField(prefix="Topic of interest:", format=str)
    related_topics = dspy.OutputField(format=str)


class GenPersona(dspy.Signature):
    """You need to select a group of Wikipedia editors who will work together to create a comprehensive article on the topic. Each of them represents a different perspective, role, or affiliation related to this topic. You can use other Wikipedia pages of related topics for inspiration. For each editor, add a description of what they will focus on.
    Give your answer in the following format: 1. short summary of editor 1: description\n2. short summary of editor 2: description\n...
    """

    topic = dspy.InputField(prefix="Topic of interest:", format=str)
    examples = dspy.InputField(
        prefix="Wiki page outlines of related topics for inspiration:\n", format=str
    )
    personas = dspy.OutputField(format=str)


class CreateWriterWithPersona(dspy.Module):
    """Discover different perspectives of researching the topic by reading Wikipedia pages of related topics."""

    def __init__(self, engine: Union[dspy.dsp.LM, dspy.dsp.HFModel]):
        super().__init__()
        self.find_related_topic = dspy.ChainOfThought(FindRelatedTopic)
        self.gen_persona = dspy.ChainOfThought(GenPersona)
        self.engine = engine

    def forward(self, topic: str, draft=None):
        with dspy.settings.context(lm=self.engine):
            # Get section names from wiki pages of relevant topics for inspiration.
            related_topics = self.find_related_topic(topic=topic).related_topics
            urls = []
            for s in related_topics.split("\n"):
                if "http" in s:
                    urls.append(s[s.find("http") :])
            examples = []
            for url in urls:
                try:
                    title, toc = get_wiki_page_title_and_toc(url)
                    examples.append(f"Title: {title}\nTable of Contents: {toc}")
                except Exception as e:
                    logging.error(f"Error occurs when processing {url}: {e}")
                    continue
            if len(examples) == 0:
                examples.append("N/A")
            gen_persona_output = self.gen_persona(
                topic=topic, examples="\n----------\n".join(examples)
            ).personas

        personas = []
        for s in gen_persona_output.split("\n"):
            match = re.search(r"\d+\.\s*(.*)", s)
            if match:
                personas.append(match.group(1))

        sorted_personas = personas

        return dspy.Prediction(
            personas=personas,
            raw_personas_output=sorted_personas,
            related_topics=related_topics,
        )


class PickResearchTeam:
    """LOCAL PATCH (2026-08-03): our own researcher picker — replaces the Wikipedia route when a brief
    is set. The Wikipedia route chose researchers from encyclopedia tables of contents, which is how a
    hiring-hackathon article got staffed with a public-prize-event organiser; it also broke a whole run
    once when Wikipedia started returning 403s. This picker chooses the team from what we already know
    (title, angle, spine, about/not-about), and requires a mixed team with a sceptic. The prompt lives in
    11-storm/prompts/pick-researchers.md."""

    def __init__(self, engine: Union[dspy.dsp.LM, dspy.dsp.HFModel]):
        self.engine = engine

    def pick(self, n: int) -> List[str]:
        b = brief.get_brief()
        tmpl = open(os.path.join(_PROMPTS_DIR, "pick-researchers.md")).read()
        prompt = (tmpl.replace("{{TITLE}}", b.get("title") or "(untitled)")
                  .replace("{{ANGLE}}", b.get("angle") or "(no distinct angle recorded)")
                  .replace("{{SPINE}}", b.get("spine") or "(no spine recorded)")
                  .replace("{{ABOUT}}", b.get("about") or "(not stated)")
                  .replace("{{NOT_ABOUT}}", b.get("not_about") or "(not stated)")
                  .replace("{{BRAND}}", b.get("brand") or "(the publisher)")
                  .replace("{{ABOUT_BRAND}}", b.get("about_brand") or "(no description on file)")
                  .replace("{{N}}", str(n)))
        last_err = None
        for _ in range(2):                      # one retry on a parse failure
            try:
                out = self.engine(prompt)
                text = out[0] if isinstance(out, list) else str(out)
                got = _extract_json(text)
                team = [f"{r['role'].strip()}: {r['focus'].strip()}"
                        for r in (got.get("researchers") or [])
                        if isinstance(r, dict) and str(r.get("role", "")).strip() and str(r.get("focus", "")).strip()]
                if len(team) >= 2:              # a usable team; trim any overshoot
                    return team[:n]
                last_err = ValueError(f"picker returned {len(team)} usable researcher(s)")
            except Exception as e:
                last_err = e
        raise RuntimeError(f"researcher picker failed: {last_err}")


class StormPersonaGenerator:
    """
    A generator class for creating personas based on a given topic.

    LOCAL PATCH (2026-08-03): when run_storm.py has set an article brief (title/angle/spine/about/
    not-about), personas come from OUR researcher picker (PickResearchTeam) — exactly max_num_persona
    researchers, mixed team, sceptic included, no 'Basic fact writer' default. The original Wikipedia
    route (CreateWriterWithPersona + the default persona) is kept verbatim as the no-brief path AND as
    the fallback if the picker fails, so a bare `run_storm.py "topic"` behaves exactly as before.
    """

    def __init__(self, engine: Union[dspy.dsp.LM, dspy.dsp.HFModel]):
        self.create_writer_with_persona = CreateWriterWithPersona(engine=engine)
        self.pick_research_team = PickResearchTeam(engine=engine)

    def generate_persona(self, topic: str, max_num_persona: int = 3) -> List[str]:
        """
        Generates a list of personas based on the provided topic, up to a maximum number specified.

        With a brief set: exactly `max_num_persona` researchers from our picker (no default persona).
        Without one (or if the picker fails): the original behavior — the default 'Basic fact writer'
        persona plus up to `max_num_persona` Wikipedia-derived personas.
        """
        if brief.has_brief():
            try:
                team = self.pick_research_team.pick(max_num_persona)
                logging.info(f"research team (brief-based): {team}")
                return team
            except Exception as e:
                logging.error(f"researcher picker failed ({e}) — falling back to the Wikipedia route")
        personas = self.create_writer_with_persona(topic=topic)
        default_persona = "Basic fact writer: Basic fact writer focusing on broadly covering the basic facts about the topic."
        considered_personas = [default_persona] + personas.personas[:max_num_persona]
        return considered_personas
