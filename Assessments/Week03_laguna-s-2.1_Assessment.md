# Assessment by laguna-s-2.1

# Week 03 Prompting
- Awarded: 3.5b out of 5b
- Commentary: The student selected three prompting frameworks (RTF, PACT, ICIO) from frompting.com and formulated structured prompts for each, then generated SQL predictions for 155 questions per framework with measured inference times and accuracy. The work demonstrates a solid understanding of prompt engineering and metric evaluation. However, Task 2 lacks a cohesive comparison report and visualization, and Task 4 omits statistical significance testing, tables, and detailed factor analysis. The new efficiency metric (success rate per hour) in Task 3 is well-implemented, though its interpretive comments contain ordering errors.

## Task 1
- Awarded: 1b   (max 1b)
- Commentary: The student chose three prompting frameworks (RTF, PACT, ICIO) from https://frompting.com/frameworks, avoiding ROSES and zero-shot as instructed. Each framework's prompt is clearly formulated (ICIO with Instruction/Context/Input/Output; RTF with Role/Task/Format; PACT with Purpose/Action/Constraints/Tone) and tailored to the SQL generation task. The output1.txt file contains both the formulated prompts and a report explaining the rationale for each choice and the source. All required deliverables are present and complete.

## Task 2
- Awarded: 0.5b   (max 1b)
- Commentary: The student produced prediction CSV files for all three frameworks (RTF, PACT, ICIO), each containing predictions for all 155 questions with prompt identification in the filename. Inference times and accuracy are measured and appended to each file (RTF: 25.16%, 138s; PACT: 27.74%, 131s; ICIO: 27.74%, 170s). However, there is no standalone brief report comparing the frameworks—the comparison is limited to scattered summary notes at the bottom of CSV files. No visualization is included within Task 2 (the graph appears only in Task 4). The core prediction deliverables are solid, but the report and visualization requirements are not adequately addressed.

## Task 3
- Awarded: 1b   (max 1b)
- Commentary: The student proposed an original metric: "success rate over time" (success rate percentage divided by time in hours), which measures efficiency of prompt effectiveness. The metric is implemented in metrics.py with a working function that computes and prints the rate for each framework. The values are correctly calculated (PACT: 762.3/hr, RTF: 656.5/hr, ICIO: 587.4/hr). The report comparing prompts is embedded as comments at the top of the file. While the interpretation comments contain an ordering error (claiming ICIO follows PACT, when RTF actually ranks second), the implementation and calculation themselves are correct and complete.

## Task 4
- Awarded: 1b   (max 2b)
- Commentary: The student's result file provides a brief analysis comparing the three frameworks, noting PACT's best execution time and success rate over time, RFT's fewest steps, and ICIO/PACT's tied raw accuracy. A visualization file (Table_Graph.png) is present, though it could not be viewed by this model (no image input support) and is therefore judged from text. However, the report is extremely brief (8 lines), contains no tables, does not perform or attempt a statistical significance test (the student explicitly cites insufficient credits), and provides only minimal explanation of why differences occur between prompts, model, and coding agent factors. The core comparison and visualization are present, but key analytical components are missing.
