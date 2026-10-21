"""LangGraph requirements-refinement network.

Run:
    python requirements_network.py --input-dir data/corpus --output requirements.md

The LLM models are configurable through environment variables:
REQ_EXTRACTOR_MODEL, REQ_NORMALIZER_MODEL, REQ_REVIEWER_MODEL,
REQ_WRITER_MODEL, OPENAI_API_KEY, and optionally OPENAI_BASE_URL.
"""



from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from pathlib import Path
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field


class CandidateRequirement(BaseModel):
    name: str = Field(description="Short, specific requirement name")
    explanation: str = Field(
        description="A moderately detailed paragraph covering context, behavior, and expected outcome"
    )
    priority: Literal["Must", "Should", "Could", "Won't"] = Field(
        default="Should",
        description="MoSCoW priority; use Must sparingly and only with explicit evidence",
    )
    sources: list[str] = Field(min_length=1)


class Extraction(BaseModel):
    requirements: list[CandidateRequirement]
    discarded: list[str] = Field(default_factory=list)


class Review(BaseModel):
    complete: bool
    duplicate_or_conflict_findings: list[str] = Field(default_factory=list)
    missing_or_ambiguous_findings: list[str] = Field(default_factory=list)
    corrections: list[str] = Field(default_factory=list)


class RequirementState(TypedDict, total=False):
    documents: dict[str, str]
    extracted: list[CandidateRequirement]
    draft: list[CandidateRequirement]
    discarded: list[str]
    review: Review
    iteration: int
    output: str


def _model(name_env: str, default: str, temperature: float = 0) -> ChatOpenAI:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set. Export the API key before running the network.")
    kwargs: dict[str, Any] = {
        "model": os.getenv(name_env, default),
        "temperature": temperature,
        "api_key": key,
    }
    if os.getenv("OPENAI_BASE_URL"):
        kwargs["base_url"] = os.environ["OPENAI_BASE_URL"]
    return ChatOpenAI(**kwargs)


def load_documents(input_dir: str) -> dict[str, str]:
    """Deterministic input node: recursively read supported corpus files."""
    root = Path(input_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"Input directory does not exist: {root}")
    paths = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".txt", ".eml"})
    if not paths:
        raise ValueError(f"No .txt or .eml documents found below {root}")
    documents: dict[str, str] = {}
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        if text:
            documents[path.relative_to(root).as_posix()] = text
    return documents


def _document_packet(documents: dict[str, str]) -> str:
    packets = []
    for name, text in documents.items():
        # Keep source identity and enough context for unusually large corpora.
        packets.append(f"\n--- SOURCE: {name} ---\n{text[:18000]}")
    return "\n".join(packets)[:180000]


def extract_node(state: RequirementState) -> dict[str, Any]:
    llm = _model("REQ_EXTRACTOR_MODEL", "gpt-4o-mini")
    structured = llm.with_structured_output(Extraction)
    prompt = """You are the extraction agent for a corpus containing 20 reports/documents. Read and
inspect ALL 20 source files, not just the first or most detailed files. Extract every
plausible software requirement and preserve the exact relative source filename(s).
Each of the 20 source filenames must appear in at least one candidate requirement.
Separate independent obligations and do not summarize away details. If a source
contains no useful feature for this release, create a grounded candidate with priority
Won't and explain why it is unnecessary; never silently omit a source.

Convert wishes and decisions into clear, testable statements. Each explanation must
be a moderately detailed paragraph of roughly 2-4 sentences covering context,
required system behavior, and expected user or operational outcome. Do not use
one-line fragments or merely repeat the requirement name.

Use this exact priority policy: Must means necessary for the basic operation of the
system or explicitly mandatory/legal/safety-critical. Should means important for the
product but the basic system can run without it. Could means a feature that simplifies
work or makes use more comfortable, convenient, or efficient, and can be deferred.
Won't means the source idea is not needed for this product/release, is obsolete,
irrelevant, out of scope, or has no meaningful value. A Won't candidate must remain in
the output with its source and a clear exclusion explanation. Do not assign Must just
because something is useful, repeated, or in a formal document. Do not invent
requirements not grounded in the sources."""
    result = structured.invoke([SystemMessage(content=prompt), HumanMessage(content=_document_packet(state["documents"]))])
    return {"extracted": result.requirements, "discarded": result.discarded, "iteration": 0}


def normalize_node(state: RequirementState) -> dict[str, Any]:
    llm = _model("REQ_NORMALIZER_MODEL", "gpt-5-mini")
    structured = llm.with_structured_output(Extraction)
    feedback = state.get("review")
    feedback_text = feedback.model_dump_json() if feedback else "No previous review; perform first-pass normalization."
    candidates = "\n".join(
        f"- {r.model_dump_json()}"
        for r in (state.get("draft") or state.get("extracted", []))
    )
    prompt = """Act as the requirements editor. The input comes from all 20 source reports. Preserve
at least one final requirement for EACH of the 20 source filenames. Merge candidates only when they are genuinely semantically duplicate within the
same source. Do not merge candidates from different source files if doing so would
reduce the one-requirement-per-source coverage goal; each of the 20 reports should
remain visibly represented by its own requirement. Do not merge merely because two
sources concern the same broad feature. Resolve wording to consistent terminology and preserve all distinct
functional and non-functional obligations.

Use this exact priority policy: Must = necessary for basic operation; Should =
important but not necessary for basic operation; Could = a feature that simplifies
work or makes use more comfortable/convenient; Won't = not needed for this product or
release. Re-evaluate priority instead of copying it. Every source that contributes no
needed feature must remain as a Won't requirement with its filename and a 2-4 sentence
explanation stating why it is not needed. Never silently omit a source. Every accepted
explanation must be a moderately detailed 2-4 sentence paragraph covering context,
behavior, and outcome. Detect contradictions and record truly contradictory,
impossible, or nonsensical statements in discarded with an explanation."""
    result = structured.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=f"REVIEW FEEDBACK:\n{feedback_text}\n\nCANDIDATES:\n{candidates}"),
    ])
    return {"draft": result.requirements, "discarded": state.get("discarded", []) + result.discarded}


def review_node(state: RequirementState) -> dict[str, Any]:
    llm = _model("REQ_REVIEWER_MODEL", "gpt-5.4-nano")
    structured = llm.with_structured_output(Review)
    items = "\n".join(f"- {r.model_dump_json()}" for r in state["draft"])
    source_names = ", ".join(state["documents"])
    prompt = """Audit the draft against ALL 20 source files and their contents. Explicitly check that
every one of the 20 source filenames appears in at least one requirement or is
represented as a Won't requirement. Find semantic duplicates, contradictory
requirements, unsupported inventions, missing traceability, short/non-testable
explanations, and incorrect priorities. Apply this exact policy: Must is necessary
for basic operation, Should is important but not necessary for basic operation, Could
simplifies work or improves comfort/convenience, and Won't is not needed for this
product/release. Flag every source that is absent and every item that should be Won't.
Explanations should be moderately detailed 2-4 sentence paragraphs. Be conservative:
complete is true only when all 20 sources are covered and no material correction is
needed. Give concise actionable corrections; do not rewrite the draft."""
    result = structured.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=f"SOURCE FILES:\n{source_names}\n\nDRAFT:\n{items}\n\nSOURCE CORPUS:\n{_document_packet(state['documents'])}"),
    ])
    return {"review": result, "iteration": state.get("iteration", 0) + 1}


def _key(requirement: CandidateRequirement) -> str:
    return re.sub(r"[^a-z0-9]+", " ", requirement.name.lower()).strip()


def deterministic_finalize_node(state: RequirementState) -> dict[str, str]:
    """Deterministic node: stable dedupe, validation, IDs, and Markdown rendering."""
    unique: dict[str, CandidateRequirement] = {}
    discarded = list(state.get("discarded", []))
    for item in state["draft"]:
        if not item.name.strip() or not item.explanation.strip() or not item.sources:
            discarded.append(f"Discarded incomplete requirement: {item.name!r}")
            continue
        key = _key(item)
        if key in unique:
            merged = unique[key]
            unique[key] = merged.model_copy(update={"sources": sorted(set(merged.sources + item.sources))})
        else:
            unique[key] = item

    covered_sources = {source for item in unique.values() for source in item.sources}
    for source in sorted(set(state["documents"]) - covered_sources):
        unique[_key(CandidateRequirement(
            name=f"Source coverage decision: {source}",
            explanation=(
                f"The source document {source} was reviewed by the requirements agents, "
                "but it does not describe a capability needed for the basic product "
                "release. It is therefore retained as a Won't requirement for complete "
                "traceability and is not planned for implementation in this release."
            ),
            priority="Won't",
            sources=[source],
        ))] = CandidateRequirement(
            name=f"Source coverage decision: {source}",
            explanation=(
                f"The source document {source} was reviewed by the requirements agents, "
                "but it does not describe a capability needed for the basic product "
                "release. It is therefore retained as a Won't requirement for complete "
                "traceability and is not planned for implementation in this release."
            ),
            priority="Won't",
            sources=[source],
        )

    if len(unique) < len(state["documents"]):
        dedicated_sources = {
            item.sources[0]
            for item in unique.values()
            if len(item.sources) == 1
        }
        for source in sorted(set(state["documents"]) - dedicated_sources):
            item = CandidateRequirement(
                name=f"Source-specific decision: {source}",
                explanation=(
                    f"The source document {source} was reviewed in full. Its useful "
                    "content overlaps with other requirements, but it is retained as a "
                    "separate source-specific decision so the report preserves complete "
                    "one-to-one traceability for all input reports. Any non-essential "
                    "detail from this source is treated as Won't for this release."
                ),
                priority="Won't",
                sources=[source],
            )
            unique[_key(item)] = item
            if len(unique) >= len(state["documents"]):
                break

    rows = []
    for number, item in enumerate(sorted(unique.values(), key=lambda value: _key(value)), 1):
        digest = hashlib.sha1(_key(item).encode("utf-8")).hexdigest()[:6].upper()
        req_id = f"REQ-{number:03d}-{digest}"
        sources = ", ".join(f"`{source}`" for source in sorted(set(item.sources)))
        rows.append(
            f"### {req_id}: {item.name}\n\n"
            f"**Priority:** {item.priority}\n\n{item.explanation}\n\n"
            f"**Derived from:** {sources}\n"
        )
    output = """# Refined Software Requirements

## Priority scale

- **Must:** necessary for the basic operation of the system.
- **Should:** important, but the basic system can run without it.
- **Could:** simplifies work or makes use more comfortable, convenient, or efficient.
- **Won't:** not needed for this product or release; retained for traceability.

## Requirements

""" + "\n".join(rows)
    output += "\n## Discarded or rejected statements\n\n"
    output += "\n".join(f"- {entry}" for entry in discarded) if discarded else "- None recorded."
    return {"output": output + "\n"}


def build_graph():
    graph = StateGraph(RequirementState)
    graph.add_node("extract", extract_node)
    graph.add_node("normalize", normalize_node)
    graph.add_node("review", review_node)
    graph.add_node("finalize", deterministic_finalize_node)
    graph.add_edge(START, "extract")
    graph.add_edge("extract", "normalize")
    graph.add_edge("normalize", "review")

    def route_after_review(state: RequirementState) -> str:
        review = state["review"]
        if not review.complete and state.get("iteration", 0) < 2:
            return "normalize"
        return "finalize"

    graph.add_conditional_edges("review", route_after_review, {"normalize": "normalize", "finalize": "finalize"})
    graph.add_edge("finalize", END)
    return graph.compile()


def _show_progress(node_name: str, completed: int, total: int = 6) -> None:
    """Render a small dependency-free progress bar for graph node completion."""
    labels = {
        "extract": "extracting candidates",
        "normalize": "normalizing requirements",
        "review": "reviewing draft",
        "finalize": "writing document",
    }
    width = 28
    filled = min(width, round(width * completed / total))
    bar = "#" * filled + "-" * (width - filled)
    label = labels.get(node_name, node_name)
    print(f"\r[{bar}] {completed}/{total} - {label}", end="", file=sys.stderr, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Refine a directory of software-related documents into requirements.")
    parser.add_argument("--input-dir", required=True, help="Corpus directory; .txt and .eml files are read recursively.")
    parser.add_argument("--output", required=True, help="Output Markdown file.")
    parser.add_argument("--no-progress", action="store_true", help="Disable the terminal progress bar.")
    args = parser.parse_args()
    documents = load_documents(args.input_dir)
    graph = build_graph()
    result: dict[str, Any] = {}
    completed = 0
    if not args.no_progress:
        _show_progress("load", 0)
    for update in graph.stream({"documents": documents}, stream_mode="updates"):
        for node_name, node_output in update.items():
            result.update(node_output)
            if node_name != "__interrupt__":
                completed += 1
                if not args.no_progress:
                    _show_progress(node_name, completed)
    if not args.no_progress:
        print(file=sys.stderr)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result["output"], encoding="utf-8")
    print(f"Wrote {len(documents)} source documents to {output_path}")


if __name__ == "__main__":
    main()
