"""Part B: controlled comparison of System A and System B. Usage: part_b.py <output_dir>"""
import csv, json, sys
from ir_metrics import *

DOCS = {"D1": "Neural networks and deep learning methods for image classification",
        "D2": "BM25 ranking functions for information retrieval",
        "D3": "Convolutional neural networks for image recognition",
        "D4": "Language models and probabilistic document retrieval",
        "D5": "Image classification using machine learning",
        "D6": "BM25, query likelihood, and document ranking",
        "D7": "Unigram language models for text search",
        "D8": "Web crawling and link analysis"}
QUERIES = {"Q1": "Neural networks for image classification",
           "Q2": "BM25 information retrieval",
           "Q3": "Language models and document retrieval"}
REL = {"Q1": {"D1", "D3", "D5"}, "Q2": {"D2", "D4", "D6"}, "Q3": {"D4", "D6", "D7"}}
GRADES_Q1 = {"D1": 3, "D3": 2, "D5": 1}
RUNS = {"A": {"Q1": ["D1", "D2", "D3", "D5", "D4"], "Q2": ["D2", "D1", "D4", "D6", "D3"], "Q3": ["D4", "D2", "D6", "D7", "D1"]},
        "B": {"Q1": ["D2", "D1", "D4", "D3", "D6"], "Q2": ["D1", "D4", "D2", "D5", "D6"], "Q3": ["D1", "D4", "D3", "D7", "D6"]}}

rows = []
for s, run in RUNS.items():
    for q, r in run.items():
        rows.append(dict(System=s, Query=q, Precision=precision(r, REL[q]), Recall=recall(r, REL[q]), F1=f1(r, REL[q]),
                         P3=precision_at_k(r, REL[q], 3), AP=average_precision(r, REL[q]), RR=reciprocal_rank(r, REL[q])))
agg = {}
for s, run in RUNS.items():
    sel = [x for x in rows if x["System"] == s]
    gains = [GRADES_Q1.get(d, 0) for d in run["Q1"][:5]]
    agg[s] = dict(MAP=mean(x["AP"] for x in sel), MRR=mean(x["RR"] for x in sel),
                  mean_P=mean(x["Precision"] for x in sel), mean_R=mean(x["Recall"] for x in sel),
                  mean_F1=mean(x["F1"] for x in sel), mean_P3=mean(x["P3"] for x in sel),
                  gains_Q1=gains, DCG5_Q1=dcg(gains), IDCG5_Q1=dcg(sorted(GRADES_Q1.values(), reverse=True)),
                  nDCG5_Q1=ndcg_at_k(run["Q1"], GRADES_Q1, 5),
                  nDCG5_Q1_binary=ndcg_at_k(run["Q1"], {d: 1 for d in REL["Q1"]}, 5))

print(f"{'System':6} {'Query':5} {'Prec':>6} {'Recall':>6} {'F1':>6} {'P@3':>6} {'AP':>6} {'RR':>6}")
for x in rows:
    print(f"{x['System']:6} {x['Query']:5} " + " ".join(f"{x[k]:6.4f}" for k in ["Precision", "Recall", "F1", "P3", "AP", "RR"]))
for s in agg:
    print(s, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in agg[s].items()})

out = sys.argv[1] if len(sys.argv) > 1 else "."
with open(f"{out}/partb_table.csv", "w", newline="") as f:
    w = csv.DictWriter(f, rows[0].keys()); w.writeheader(); w.writerows(rows)
json.dump(dict(rows=rows, agg=agg), open(f"{out}/partb_results.json", "w"), indent=1)
