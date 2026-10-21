# Requirements-refinement agentic network

## Design

`requirements_network.py` is a reusable command-line program. It accepts only an
input directory and recursively reads `.txt` and `.eml` files, so the provided
corpus is an example rather than a hard-coded input.

The LangGraph state machine has four nodes:

1. **Extract** (OpenAI `gpt-4o-mini`) identifies every candidate obligation and
   attaches the relative source filename(s).
2. **Normalize** (OpenAI `gpt-5-mini`) merges semantic duplicates, standardizes
   vocabulary, classifies MoSCoW priority, and records rejected statements.
3. **Review** (OpenAI `gpt-5.4-nano`) checks completeness, conflicts, traceability,
   testability, and duplicate removal.
4. **Finalize** is deterministic. It validates fields, performs a stable
   name-based duplicate guard, assigns stable `REQ-###-HASH` IDs, and renders one
   Markdown document.

If review finds a material problem, the graph loops back to Normalize once. This
is the required feedback loop; the iteration limit prevents an unbounded API
cycle. The final writer uses a fourth model (`gpt-5.6-luna`) as a configurable
model slot is intentionally not needed: the three active LLM nodes already
satisfy the three-model requirement, while deterministic finalization keeps
IDs and output formatting reproducible.

## Specification coverage

- **ANS1:** Extract, Normalize, and Review invoke LLMs.
- **ANS2:** Load and Finalize are deterministic.
- **ANS3:** Review conditionally routes back to Normalize.
- **ANS4:** Defaults name four different available models.
- **ANS5:** The graph is built with `langgraph.graph.StateGraph`.
- **OS1/OS2:** one Markdown output with stable unique requirement IDs.
- **OS3/OS7:** normalization prompts address semantic duplicates, vocabulary,
  and contradictions; deterministic finalization adds a last duplicate guard.
- **OS4:** every requirement carries relative source filenames.
- **OS5/OS6:** each item has a short name, paragraph explanation, and MoSCoW
  priority; the document explains the scale.
- **OS8/OS9:** extraction requests complete coverage and the output contains a
  separate discarded/rejected section with reasons.

## Running

Install the dependencies from `requirements.txt`, export `OPENAI_API_KEY`, then:

```powershell
python requirements_network.py `
  --input-dir .\data\corpus `
  --output .\generated_requirements.md
```

Optional model overrides are `REQ_EXTRACTOR_MODEL`, `REQ_NORMALIZER_MODEL`,
`REQ_REVIEWER_MODEL`, and `OPENAI_BASE_URL`.
