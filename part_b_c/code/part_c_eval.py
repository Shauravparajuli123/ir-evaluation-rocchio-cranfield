"""Part C: evaluate saved runs with the Part B metric functions (unchanged) and test differences.
Usage: part_c_eval.py <data_dir> <results_dir>"""
import json, sys, collections
import numpy as np
from scipy.stats import wilcoxon
from ir_metrics import *

def load_qrels(path):
    R, G = collections.defaultdict(set), collections.defaultdict(dict)
    for l in open(path):
        q, _, d, r = l.split()
        if int(r) > 0:
            R[q].add(d); G[q][d] = 1     # this copy of the qrels is binary, so gain = 1
    return R, G

def load_run(path):
    run = collections.defaultdict(list)
    for l in open(path):
        p = l.split(); run[p[0]].append(p[2])
    return run

def evaluate(run, R, G):
    o = {}
    for q in R:
        r = run.get(q, [])
        o[q] = dict(P=precision(r, R[q]), R=recall(r, R[q]), F1=f1(r, R[q]),
                    P3=precision_at_k(r, R[q], 3), P10=precision_at_k(r, R[q], 10),
                    R10=recall(r[:10], R[q]), F1_10=f1(r[:10], R[q]),
                    AP=average_precision(r, R[q]), RR=reciprocal_rank(r, R[q]),
                    nDCG5=ndcg_at_k(r, G[q], 5), nDCG10=ndcg_at_k(r, G[q], 10))
    return o

if __name__ == "__main__":
    data, res = sys.argv[1], sys.argv[2]
    R, G = load_qrels(f"{data}/qrels.txt")
    models = ["TF-IDF", "BM25", "LM-Dirichlet"]
    variants = ["LMD-mu50", "LMD-mu100", "LMD-mu200", "LMD-mu500", "LMD-mu1000", "LMJM-l0.1", "LMJM-l0.3", "LMJM-l0.7", "BM25-b0.25", "BM25-b0.5", "BM25-b1.0"]
    per = {m: evaluate(load_run(f"{res}/partc_{m}.run"), R, G) for m in models + variants}
    agg = {m: {k: mean(x[k] for x in v.values()) for k in next(iter(v.values()))} for m, v in per.items()}
    qs = sorted(R, key=int)

    # What happens if query IDs are NOT renumbered to match the qrels
    rawmap = {l.split("\t")[0]: l.split("\t")[1] for l in open(f"{data}/queries.tsv")}
    raw = {rawmap[q]: r for q, r in load_run(f"{res}/partc_BM25.run").items()}
    wrong = evaluate(raw, R, G)
    wrong_ids = {k: mean(x[k] for x in wrong.values()) for k in ["AP", "P10", "RR"]}

    # Paired two-sided randomization test and Wilcoxon signed-rank test over queries
    rng = np.random.default_rng(618); tests = []
    for a, b in [("BM25", "TF-IDF"), ("BM25", "LM-Dirichlet"), ("TF-IDF", "LM-Dirichlet")]:
        for k in ["AP", "nDCG10", "RR", "P10"]:
            x = np.array([per[a][q][k] for q in qs]); y = np.array([per[b][q][k] for q in qs]); d = x - y
            signs = rng.choice([-1, 1], size=(100000, len(d)))
            pp = (np.abs((signs * d).mean(axis=1)) >= abs(d.mean()) - 1e-12).mean()
            tests.append(dict(a=a, b=b, metric=k, diff=float(d.mean()), wins=int((d > 0).sum()), losses=int((d < 0).sum()),
                              ties=int((d == 0).sum()), p_perm=float(pp), p_wilcoxon=float(wilcoxon(x, y).pvalue)))

    # Query-level behaviour
    best = collections.Counter()
    for q in qs:
        v = {m: per[m][q]["AP"] for m in models}; top = max(v.values())
        ws = [m for m in models if abs(v[m] - top) < 1e-12]; best["tie" if len(ws) > 1 else ws[0]] += 1
    zero = {m: sum(per[m][q]["P10"] == 0 for q in qs) for m in models}
    spread = sorted(qs, key=lambda q: -(max(per[m][q]["AP"] for m in models) - min(per[m][q]["AP"] for m in models)))[:5]
    text = {l.split("\t")[0]: l.split("\t")[2].strip() for l in open(f"{data}/queries.tsv")}
    examples = [dict(q=q, text=text[q], nrel=len(R[q]), **{m: per[m][q]["AP"] for m in models}) for q in spread]
    runs = {m: load_run(f"{res}/partc_{m}.run") for m in models}
    overlap = {f"{a}|{b}": mean(len(set(runs[a][q][:10]) & set(runs[b][q][:10])) / 10 for q in qs)
               for a, b in [("BM25", "TF-IDF"), ("BM25", "LM-Dirichlet"), ("TF-IDF", "LM-Dirichlet")]}
    ret = {m: mean(len(runs[m][q]) for q in qs) for m in models}

    json.dump(dict(agg=agg, wrong_ids=wrong_ids, tests=tests, best_AP=dict(best), zero_P10=zero, examples=examples, overlap10=overlap, retrieved_mean=ret),
              open(f"{res}/partc_results.json", "w"), indent=1)
    with open(f"{res}/partc_per_query.csv", "w") as f:
        keys = list(next(iter(per["BM25"].values())))
        f.write("model,query," + ",".join(keys) + "\n")
        for m in models:
            for q in qs: f.write(f"{m},{q}," + ",".join(f"{per[m][q][k]:.6f}" for k in keys) + "\n")
    for m in models + variants: print(f"{m:14}", {k: round(v, 4) for k, v in agg[m].items()})
    for k, v in [("wrong_ids", wrong_ids), ("best_AP", dict(best)), ("zero_P10", zero), ("overlap10", overlap), ("retrieved", ret)]: print(k, v)
    for t in tests: print(t)
    for e in examples: print(e)
