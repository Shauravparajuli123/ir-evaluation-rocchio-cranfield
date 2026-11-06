"""Score the original and updated rankings with the Part B metric functions (unchanged).
Usage: rocchio_eval.py <data_dir> <results_dir> <grid_dir>"""
import json, os, re, sys, collections
import numpy as np
from ir_metrics import *

def load_rel(path):
    rel = collections.defaultdict(set)
    for l in open(path):
        q, _, d, r = l.split()
        if int(r) > 0: rel[q].add(d)
    return rel
def load_run(path):
    run = collections.defaultdict(list)
    for l in open(path):
        p = l.split(); run[p[0]].append(p[2])
    return run
def score(r, rel):
    gains = {d: 1 for d in rel}
    return dict(P=precision(r, rel), R=recall(r, rel), F1=f1(r, rel), P3=precision_at_k(r, rel, 3), P10=precision_at_k(r, rel, 10),
                R10=recall(r[:10], rel), F1_10=f1(r[:10], rel), AP=average_precision(r, rel), RR=reciprocal_rank(r, rel),
                nDCG5=ndcg_at_k(r, gains, 5), nDCG10=ndcg_at_k(r, gains, 10))
def evaluate(run, base, REL, k, residual):
    """residual=True removes the top k original results (the ones the user saw) from both the list and the answer key."""
    out = {}
    for q in REL:
        seen = set(base[q][:k]) if residual else set()
        rel = REL[q] - seen
        if not rel: continue
        out[q] = score([d for d in run[q] if d not in seen][:1000], rel)
    return out
def agg(per): return {m: mean(per[q][m] for q in per) for m in next(iter(per.values()))}
def flip(x, y, rng, n=100000):
    d = np.array(x) - np.array(y); s = rng.choice([-1, 1], size=(n, len(d)))
    return float((np.abs((s * d).mean(axis=1)) >= abs(d.mean()) - 1e-12).mean())

data, res, grid = sys.argv[1:4]
REL = load_rel(f"{data}/qrels.txt")
base = load_run(f"{res}/rocchio_original.run"); upd = load_run(f"{res}/rocchio_updated.run")
out = {}

# Does the no-feedback baseline reproduce Part C's TF-IDF run?
if len(sys.argv) > 4 and os.path.exists(sys.argv[4]):
    pc = load_run(sys.argv[4]); same = 0; total = 0
    for q in REL:
        same += base[q][:1000] == pc[q][:1000]; total += 1
    out["baseline_vs_partc"] = dict(identical_queries=same, total=total, map_baseline=mean(average_precision(base[q][:1000], REL[q]) for q in REL), map_partc=mean(average_precision(pc[q], REL[q]) for q in REL))

F0, F1_ = evaluate(base, base, REL, 10, False), evaluate(upd, base, REL, 10, False)
R0, R1_ = evaluate(base, base, REL, 10, True), evaluate(upd, base, REL, 10, True)
out["full"] = dict(before=agg(F0), after=agg(F1_), n=len(F0))
out["residual"] = dict(before=agg(R0), after=agg(R1_), n=len(R0))

rng = np.random.default_rng(618); tests = []
for name, A, B in [("full", F0, F1_), ("residual", R0, R1_)]:
    for m in ["AP", "P10", "P3", "nDCG10", "RR", "R10"]:
        qs = sorted(A, key=int); x = [B[q][m] for q in qs]; y = [A[q][m] for q in qs]; d = np.array(x) - np.array(y)
        tests.append(dict(view=name, metric=m, diff=float(d.mean()), up=int((d > 1e-12).sum()), down=int((d < -1e-12).sum()), same=int((abs(d) <= 1e-12).sum()), p=flip(x, y, rng)))
out["tests"] = tests

# Query changes and per-query outcome on unseen documents
ch = {l.split("\t")[0]: l.rstrip("\n").split("\t") for l in list(open(f"{res}/query_changes.tsv"))[1:]}
rows = []
for q in sorted(R0, key=int):
    c = ch[q]
    rows.append(dict(q=q, rel_top10=int(c[1]), orig_terms=int(c[3]), new_terms=int(c[4]), added=int(c[5]), removed=int(c[6]), top_added=c[7], nrel=len(REL[q]), ap0=R0[q]["AP"], ap1=R1_[q]["AP"], p10_0=R0[q]["P10"], p10_1=R1_[q]["P10"], dAP=R1_[q]["AP"] - R0[q]["AP"]))
out["query_terms"] = dict(orig=mean(int(c[3]) for c in ch.values()), new=mean(int(c[4]) for c in ch.values()), added=mean(int(c[5]) for c in ch.values()), removed=mean(int(c[6]) for c in ch.values()))
groups = {"0": (0, 0), "1 to 2": (1, 2), "3 to 5": (3, 5), "6 to 10": (6, 10)}
out["by_rel"] = {g: dict(n=sum(lo <= r["rel_top10"] <= hi for r in rows), dAP=mean(r["dAP"] for r in rows if lo <= r["rel_top10"] <= hi), ap0=mean(r["ap0"] for r in rows if lo <= r["rel_top10"] <= hi), ap1=mean(r["ap1"] for r in rows if lo <= r["rel_top10"] <= hi), down=sum(lo <= r["rel_top10"] <= hi and r["dAP"] < 0 for r in rows)) for g, (lo, hi) in groups.items()}
cg = [l.split("\t") for l in list(open(f"{res}/query_changes_gamma1.tsv"))[1:]]
out["removed_gamma1"] = dict(mean=mean(int(c[6]) for c in cg), queries=sum(int(c[6]) > 0 for c in cg), orig=mean(int(c[3]) for c in cg))
s = sorted(rows, key=lambda r: r["dAP"])
out["worst"], out["best"] = s[:5], s[-5:][::-1]
out["rows"] = rows

# Ranking change
out["rank_change"] = dict(top10_overlap=mean(len(set(base[q][:10]) & set(upd[q][:10])) / 10 for q in REL),
                          new_in_top10=mean(len(set(upd[q][:10]) - set(base[q][:10])) for q in REL))

# Parameter grid
g = {}
for f in sorted(os.listdir(grid)):
    if not f.endswith(".run"): continue
    a, b, gm, k = re.match(r"a([\d.]+)_b([\d.]+)_g([\d.]+)_k(\d+)\.run", f).groups()
    run = load_run(f"{grid}/{f}"); k = int(k)
    pr = evaluate(run, base, REL, k, True); pf = evaluate(run, base, REL, k, False)
    pb = evaluate(base, base, REL, k, True)
    g[f[:-4]] = dict(alpha=float(a), beta=float(b), gamma=float(gm), k=k, residual=agg(pr), full=agg(pf), n=len(pr), base_residual=agg(pb),
                     down=sum(pr[q]["AP"] < pb[q]["AP"] - 1e-12 for q in pr), up=sum(pr[q]["AP"] > pb[q]["AP"] + 1e-12 for q in pr))
out["grid"] = g
json.dump(out, open(f"{res}/rocchio_results.json", "w"), indent=1)
with open(f"{res}/rocchio_per_query.csv", "w") as f:
    f.write("query,rel_in_top10,AP_before_unseen,AP_after_unseen,change,top_added_words\n")
    for r in rows: f.write(f"{r['q']},{r['rel_top10']},{r['ap0']:.6f},{r['ap1']:.6f},{r['dAP']:+.6f},{r['top_added']}\n")

for k in ["baseline_vs_partc", "query_terms", "rank_change", "by_rel"]: print(k, out.get(k))
for v in ["full", "residual"]:
    print(v, out[v]["n"]); [print(f"  {m:7} {out[v]['before'][m]:.4f} {out[v]['after'][m]:.4f}") for m in out[v]["before"]]
for t in tests: print(t)
for r in out["worst"] + out["best"]: print(r["q"], r["rel_top10"], r["nrel"], round(r["ap0"], 4), round(r["ap1"], 4), r["top_added"][:70])
K = [v for v in g.values() if v["k"] == 10]
print("top residual"); [print(v["alpha"], v["beta"], v["gamma"], round(v["residual"]["AP"], 4), round(v["full"]["AP"], 4), v["up"], v["down"]) for v in sorted(K, key=lambda v: -v["residual"]["AP"])[:6]]
print("bottom"); [print(v["alpha"], v["beta"], v["gamma"], round(v["residual"]["AP"], 4), round(v["full"]["AP"], 4), v["up"], v["down"]) for v in sorted(K, key=lambda v: v["residual"]["AP"])[:5]]
for v in g.values():
    if v["k"] != 10: print("k", v["k"], v["n"], round(v["base_residual"]["AP"], 4), round(v["residual"]["AP"], 4), round(v["full"]["AP"], 4))
