"""Independent check: recompute Part C metrics with the ranx library. Usage: verify.py <data_dir> <results_dir>"""
import json, sys
from ranx import Qrels, Run, evaluate as rx
from part_c_eval import load_qrels
data, res = sys.argv[1], sys.argv[2]
R, _ = load_qrels(f"{data}/qrels.txt")
Q = Qrels({q: {d: 1 for d in R[q]} for q in R})
own = json.load(open(f"{res}/partc_results.json"))["agg"]; out = {}
names = {"map": "AP", "mrr": "RR", "precision@3": "P3", "precision@10": "P10", "recall@10": "R10", "ndcg@5": "nDCG5", "ndcg@10": "nDCG10", "recall@1000": "R"}
for m in ["TF-IDF", "BM25", "LM-Dirichlet"]:
    run = {}
    for l in open(f"{res}/partc_{m}.run"):
        q, _, d, rk, _s, _t = l.split(); run.setdefault(q, {})[d] = 1000.0 - int(rk)
    r = rx(Q, Run(run), list(names))
    out[m] = {k: (round(own[m][v], 6), round(float(r[k]), 6)) for k, v in names.items()}
    print(m, "all match:", all(abs(a - b) < 2e-6 for a, b in out[m].values()), out[m])
json.dump(out, open(f"{res}/verify_ranx.json", "w"), indent=1)
