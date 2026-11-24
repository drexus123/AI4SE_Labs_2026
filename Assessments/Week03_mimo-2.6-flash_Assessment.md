# Assessment by mimo-2.6-flash

# Week 03 Prompting
- Awarded: 2.5b out of 5b
- Commentary: Task 1 is the strongest deliverable: three properly selected frameworks with concrete prompts aimed at Task 2, plus sourcing. The experimental side is much thinner — predictions for all three prompts exist and an evaluation harness was written, but Task 2 has no report/visualisation/inference-time records, Task 3's "metric" is a hardcoded efficiency ratio defended only by two code comments, and Task 4's analysis is a few informal lines with no statistical significance test. Note: the image Task_4/Table_Graph.png could not be viewed by this model, so the graph/table were judged from the accompanying text only.

## Task 1
- Awarded: 1b   (max 1b)
- Commentary: Three frameworks (ICIO, RTF, PACT) chosen from https://frompting.com/frameworks, correctly avoiding ROSES and zero-shot, each with a fully formulated prompt actually usable for the Task 2 SQL-generation problem (roles/instructions, schema and file references, strict CSV output contract, constraint about not touching the results directory). The report gives a rationale and expected behaviour per framework (PACT's Constraints section for protected paths, RTF's minimalism for straight execution, and an honest note that ICIO was hard to apply), and states the source. Minor weaknesses: the "what do you expect from it" part is implied rather than stated explicitly for each prompt, the ICIO entry describes personal difficulty instead of an expectation, and the writing is casual with typos ("RFT"), but all required outputs are present.

## Task 2
- Awarded: 0.5b   (max 1b)
- Commentary: The core data deliverable exists — three prediction files (RTF, PACT, ICIO) with question,predicted_sql pairs for 161 questions, and a solid evaluate_retrieval_predictions.py harness that builds the SQLite DB from schema/data and scores results as multisets. However, the required brief report comparing the prompting techniques is missing entirely, there is no visualisation in this task, inference times are not recorded anywhere in Task 2, and the files carry prompt identification only via filenames with no model identification metadata. Roughly half of the requested output is delivered.

## Task 3
- Awarded: 0.5b   (max 1b)
- Commentary: A new metric is proposed — success rate over time (accuracy % divided by wall-clock seconds, plus a steps count) — and implemented in metrics.py, producing comparable values (PACT ≈762, RTF ≈658, ICIO ≈588 per hour). It plausibly complements the original accuracy metric (the comment correctly notes ICIO/PACT tie on raw accuracy while differing on time). Deductions: accuracy values and timings are hardcoded dictionaries rather than computed from the Task 2 predictions, the argument defending why the metric is good/applicable and whether it complements or replaces the original is only two comment lines with no real defence of validity (the metric rewards speed and ignores query quality differences), and the "report comparing the metric values for different prompts" is those same comments rather than a report document.

## Task 4
- Awarded: 0.5b   (max 2b)
- Commentary: The `result` file briefly compares the three prompts on execution time (PACT 131s vs RTF 138s vs ICIO 170s), steps (RTF fewest, 25), success rate (ICIO/PACT 27.74% vs RTF 25.16%) and success-rate-over-time (PACT best), and mentions the model/agent factor (gpt-5.6-luna) and the idea of repeated runs for more reliable estimates. A Table_Graph.png artifact exists but could not be inspected by this model, so its content is unverified. Substantial requirements are missing: no statistical significance test is performed (explicitly skipped for lack of credits), no reasoning about *why* the prompt designs cause the observed differences (prompt-as-factor is never analysed), and the whole "report" is eight informal lines rather than a detailed analysis. Image not viewable: judged from text.