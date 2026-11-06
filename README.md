# CSC 618: IR evaluation and Rocchio relevance feedback (Cranfield)

Utica University, Fall 2026. Everything here uses Apache Lucene 10.5.0 and the Cranfield collection, except Part B, which uses the assignment's sample data.

| Folder | Task | Main result |
|---|---|---|
| `part_a/` | Part A report: evaluation concepts, formulas, worked example | Worked example on MatchAll: AP 0.345, Recall 1.0 |
| `part_b_c/` | Part B controlled experiment and Part C on Cranfield (Submissions 2, 3, 4) | BM25 MAP 0.2952 and TF-IDF 0.2931 are tied; both beat the Language Model at 0.2341 |
| `rocchio/` | Rocchio relevance feedback, with report and class demo | MAP on unseen documents rose from 0.1209 to 0.2643 |
| `data/` | Cranfield: raw files in `data/raw/`, flat files in `data/` | 1,400 documents, 225 queries |
| `lib/` | Lucene classes, from `anserini-2.3.0-fatjar.jar` in the pyserini 2.4.0 source package | |

## Rocchio class demo
Needs Java 21 or newer.

    cd rocchio
    sh run_demo.sh

Pick a query ID, type the ranks of the relevant and non-relevant results, then set alpha, beta and gamma (press Enter for 1.0, 0.75 and 0.15). It prints the updated query, the new ranking and before-and-after metrics.

Try query 20 with relevant ranks `2 3 4 5 6` and non-relevant ranks `1 7 8 9 10`. For a case where feedback hurts, try query 168 with relevant rank `5` and non-relevant ranks `1 2 3 4 6 7 8 9 10`.

## Rerun the experiments

    cd rocchio && sh run_experiments.sh
    cd part_b_c && sh run_part_b_c.sh

Both need Python 3 and numpy. Part C also needs scipy, and the final checks need `pip install ranx`. `part_b_c/results/` holds the three main rankings, and the rerun also creates the parameter variants.

## Data source
Cranfield copy: https://github.com/oussbenk/cranfield-trec-dataset (commit 1208e6e). Original: http://ir.dcs.gla.ac.uk/resources/test_collections/cran/. Query numbers in the file (1, 2, 4, 8, ...) are renumbered 1 to 225 by position to match the judgments.
