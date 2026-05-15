#!/usr/bin/env python3
"""Add [Core] / [Related·X] tags to README paper bullets."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

BULLET_RE = re.compile(r"^(- )(\(\*[^)]+\*\) \*\*.+?\*\*)")
TAG_PREFIX_RE = re.compile(r"^- \[(?:Core|Related[^\]]+)\] ")

# Force Core (medical multimodal / imaging agents misclassified by title-only rules)
FORCE_CORE = [
    "radagent:",
    "evidence-based actor-verifier reasoning for echocardiographic",
    "care: privacy-compliant agentic reasoning",
    "med-evo:",
    "ibisagent",
    "camyla",
    "lungcure:",
    "esc-rl",
    "mmedagent-rl",
    "bioMedAgent".lower(),
]

# Force Related·A (general, non-healthcare)
FORCE_A = [
    "graphflow:",
    "maspo:",
    "skillos:",
    "memtier:",
    "coral:",
    "evoskills:",
    "searl:",
    "cognitive friction",
    "ui-voyager",
    "creativebench",
    "tool-genesis",
    "agentfactory",
    "meta-harness",
    "aira_2",
    "agentic evolution is the path",
    "selfevolve",
    "evoagentx",
    "evoagent:",
    "cot-evo",
    "evotest",
    "skillevo",
    "s1-nexusagent",
    "ael:",
    "genericagent",
    "mage: multi-agent self-evolution",
    "evolving-rl",
    "nanoresearch",
    "autogenesis:",
    "co-evolving llm decision",
    "holistic evaluation and failure diagnosis",
    "transient turn injection",
    "symptomwise:",
    "autoskill:",
    "reflect to inform:",
    "when models judge themselves",
    "memma:",
    "agentic reproducibility assessment",
    "beyond individual intelligence",
    "from experience to skill: multi-agent generative",
    "mage: multi-agent",
    "when models judge",
]

# Force Related·B (medical agent, non-vision-primary)
FORCE_B = [
    "physicianbench",
    "healthcare ai gym",
    "gsem:",
    "evoclinician",
    "evomdt",
    "mdteamgpt",
    "sem-agents",
    "symphony for medical coding",
    "clinicalretrial",
    "camp)",
    "medihive",
    "doctorina medbench",
    "can large language models self-correct",
    "from exposure to internalization",
    "mat-cell",
    "healthflow",
    "rareagent",
    "origene",
    "agentomics",
    "pantheonos",
    "evoScientist".lower(),
    "emulating clinician cognition",
    "self-evolving ai agents for protein",
    "agentifying patient dynamics",
    "agentic ai for clinical urgency",
    "artificial epidemiology",
    "when chatbots become agents",
    "map: evaluation",
    "integrating dynamical systems learning",
    "dream paradigm",
    "self-evolving llm ecosystems",
    "everos",
    "quarkmedsearch",
    "caris",
    "emsdialog",
    "cacm",
    "counterfactual multi-agent diagnosis",
    "hiss",
    "sea-eval",
    "seqcomm",
    "ceem",
    "medagentgym",
    "counselbench",
    "joint optimization of reasoning and dual-memory",
    "modeling clinical concern trajectories",
    "endoGov".lower(),
    "medskillaudit",
    "from fuzzy to formal",
    "psychagent",
    "healthalign-agents",
    "perfecting human",
    "depression diagnosis dialogue",
    "curaview",  # graphrag text
    "an empirical study of agent skills for healthcare",
    "virtual speech therapist",
    "versatile ai agent for rare disease",
    "silence is not consensus",
    "doctoragent-rl",
    "med-edu",
    "symptomwise",
]

# Force Related·C (medical vision/mm, not agent)
FORCE_C = [
    "iterative multimodal retrieval-augmented generation for medical question",
    "medsynapse-v:",
    "verillmed",
    "case-specific rubrics for clinical ai evaluation",
    "seeing through experts",
    "enhancing reinforcement learning for radiology report generation",
    "rethinking patient education as multi-turn multi-modal",
    "how well do multimodal models reason on ecg",
    "llm as clinical graph structure refiner",
]

# Force Related·D in main list (perspectives / limits without agent focus)
FORCE_D = [
    "the doctor will (still) see you",
    "agentic ai, medical morality",
    "vibe medicine:",
    "can \"ai\" be a doctor",
    "can llms score medical diagnoses",
    "grounding clinical ai competency",  # framework paper
    "dissecting clinical reasoning failures",
    "enhancing llm-based medical decision-making by test-time knowledge",
    "automation bias in large language model",
    "haarf:",
]

MED_RE = re.compile(
    r"medical|clinical|health|healthcare|hospital|patient|physician|diagnos|therapy|"
    r"counsel|psychiat|mental |ehr|emr|oncolog|biomed|genomic|protein|cell |trial|"
    r"coding|outpatient|emergency|cardiac|lung|tumor|disease|drug|sepsis|myeloma|"
    r"dermatolog|skin |radiolog|imaging|neuroimag|patholog|histopath|pet |mri|cmr|"
    r"x-?ray|ultrasound|endoscop|seizure|ecg|anatomy|labos|nursing|dental|speech|"
    r"theranost|anesthes|surgical|operative|chest|tomography|echocardiograph|computed tomography",
    re.I,
)
AGENT_RE = re.compile(
    r"\bagent|\bmulti-agent\b|agentic|openhospital|agent hospital|mdt|workflow|"
    r"orchestr|subagent|self-evolv|skill.?evolv|memma|harness",
    re.I,
)
VISION_RE = re.compile(
    r"multimodal|multi-modal|vision|visual|imaging|radiolog|x-?ray|xray|mri|cmr|"
    r"ct |pet |patholog|histopath|dermatolog|skin|segmentation|3d medical|neuroimag|"
    r"ultrasound|endoscop|fundus|retina|slide|wsi|medagent|pathfinder|amie|"
    r"agentclinic|echocardio|cardiac agent|macro|tissuelab|eviagent|med-evo|ibis|"
    r"camyla|lungcure|xrayclaw|medagentsim|neuroagent|neuroclaw|labos|skingpt|"
    r"theranost|esc-rl|report generation|mmedagent|histolog|pathology|chest|"
    r"fundus|video|gui |screen|pose correction|physiotherapy",
    re.I,
)
SURVEY_RE = re.compile(r"survey|scoping review|systematic review|meta analysis|taxonomy", re.I)


def classify(title: str, section: str) -> str:
    t = title.lower()
    sec = section.lower()

    if "classic agent" in sec or "agent-based healthcare" in sec:
        return "Related·E"

    if "survey papers" in sec:
        return "Related·D"

    if any(x in t for x in FORCE_CORE):
        return "Core"

    if any(x in t for x in FORCE_A):
        return "Related·A"

    if any(x in t for x in FORCE_C):
        return "Related·C"

    if any(x in t for x in FORCE_D):
        return "Related·D"

    med = bool(MED_RE.search(title))
    agent = bool(AGENT_RE.search(title))
    vision = bool(VISION_RE.search(title))

    if not med:
        return "Related·A"

    if any(x in t for x in FORCE_B):
        return "Related·B"

    # Broader Core: medical + agent, or medical + vision + agent, or medical self-evolving harness
    if agent or (vision and med):
        if SURVEY_RE.search(title) and "agent" not in t:
            return "Related·D"
        return "Core"

    if vision and not agent:
        return "Related·C"

    if med and not agent:
        return "Related·D" if SURVEY_RE.search(title) else "Related·B"

    return "Core" if med else "Related·A"


def tag_line(line: str, label: str) -> str:
    if label == "Core":
        prefix = "[Core] "
    else:
        prefix = f"[{label}] "

    stripped = TAG_PREFIX_RE.sub("- ", line)

    m = BULLET_RE.match(stripped)
    if not m:
        return line
    return f"{m.group(1)}{prefix}{m.group(2)}"


def main() -> None:
    text = README.read_text(encoding="utf-8")
    lines = text.splitlines()
    section = ""
    out = []
    stats: dict[str, int] = {}

    for line in lines:
        if line.startswith("## "):
            section = line
        elif line.startswith("### "):
            section = f"{section} > {line}"

        stripped = TAG_PREFIX_RE.sub("- ", line)
        m = BULLET_RE.match(stripped)
        if m:
            title_m = re.search(r"\*\*(.+?)\*\*", line)
            title = title_m.group(1) if title_m else ""
            label = classify(title, section)
            stats[label] = stats.get(label, 0) + 1
            out.append(tag_line(line, label))
        else:
            out.append(line)

    README.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("Tagged bullets:", sum(stats.values()))
    for k in sorted(stats.keys()):
        print(f"  {k}: {stats[k]}")


if __name__ == "__main__":
    main()
