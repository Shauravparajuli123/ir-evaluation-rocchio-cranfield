"""Check my before-and-after scores against the ranx library. Usage: verify_rocchio.py <data_dir> <results_dir>"""
import json, sys, collections
from ranx import Qrels, Run, evaluate as rx
data, res = sys.argv[1:3]
REL = collections.defaultdict(set)
for l in open(f"{data}/qrels.txt"):
    q, _, d, r = l.split()
    if int(r) > 0: REL[q].add(d)
def load(p):
    run = collections.defaultdict(list)
    for l in open(p):
        x = l.split(); run[x[0]].append(x[2])
    return run
base, upd = load(f"{res}/rocchio_original.run"), load(f"{res}/rocchio_updated.run")
own = json.load(open(f"{res}/rocchio_results.json"))
names = {"map": "AP", "mrr": "RR", "precision@3": "P3", "precision@10": "P10", "recall@10": "R10", "ndcg@10": "nDCG10"}
out = {}
for view, k in [("full", 0), ("residual", 10)]:
    for side, run in [("before", base), ("after", upd)]:
        qrels, rr = {}, {}
        for q in REL:
            seen = set(base[q][:k]); rel = REL[q] - seen
            if not rel: continue
            qrels[q] = {d: 1 for d in rel}
            rr[q] = {d: 1000.0 - i for i, d in enumerate([d for d in run[q] if d not in seen][:1000])}
        r = rx(Qrels(qrels), Run(rr), list(names))
        out[f"{view}_{side}"] = {m: (round(own[view][side][v], 6), round(float(r[m]), 6)) for m, v in names.items()}
        print(view, side, "all match:", all(abs(a - b) < 2e-6 for a, b in out[f"{view}_{side}"].values()), out[f"{view}_{side}"]["map"])
json.dump(out, open(f"{res}/verify_ranx.json", "w"), indent=1)
