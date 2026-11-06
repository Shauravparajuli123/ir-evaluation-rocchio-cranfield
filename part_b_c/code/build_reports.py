"""Fills the LaTeX templates from result files, so reported numbers come from actual runs."""
import json, re, subprocess, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from ir_metrics import *
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RES, REP = f"{ROOT}/results", f"{ROOT}/reports"
B = json.load(open(f"{RES}/partb_results.json")); C = json.load(open(f"{RES}/partc_results.json"))
D = json.load(open(f"{ROOT}/data/dataset_stats.json")); X = json.load(open(f"{RES}/verify_ranx.json"))
IDX = dict(p.split("=") for p in open(f"{RES}/index_stats.txt").read().split())
c = lambda m, k, n=4: f"{C['agg'][m][k]:.{n}f}"
ba = lambda s, k, n=4: f"{B['agg'][s][k]:.{n}f}"
test = lambda a, b, k: next(t for t in C['tests'] if t['a'] == a and t['b'] == b and t['metric'] == k)
def p(x): return r"$<10^{-5}$" if x < 1e-5 else (f"{x:.5f}" if x < 0.001 else f"{x:.4f}")
esc = lambda t: re.sub(r"([&%#_$])", r"\\\1", t)
EX = {e['q']: e for e in C['examples']}
def t_b():
    return "\n".join(f"{r['System']} & {r['Query']} & {r['Precision']:.4f} & {r['Recall']:.4f} & {r['F1']:.4f} & {r['P3']:.4f} & {r['AP']:.4f} & {r['RR']:.4f} \\\\" + ("\\midrule" if r['System'] == "A" and r['Query'] == "Q3" else "") for r in B['rows'])
MODELS = ["TF-IDF", "BM25", "LM-Dirichlet"]
def t_c():
    keys = [("AP", "MAP"), ("RR", "MRR"), ("P3", "P@3"), ("P10", "P@10"), ("R10", "Recall@10"), ("F1_10", "F1@10"), ("nDCG5", "nDCG@5"), ("nDCG10", "nDCG@10"), ("P", "Precision (full list)"), ("R", "Recall (full list)"), ("F1", "F1 (full list)")]
    out = []
    for k, n in keys:
        vals = [C['agg'][m][k] for m in MODELS]; mx = max(round(v, 4) for v in vals)
        out.append(n + " & " + " & ".join(("\\textbf{%.4f}" % v) if round(v, 4) == mx and len({round(x, 4) for x in vals}) > 1 else "%.4f" % v for v in vals) + " \\\\")
    return "\n".join(out)
def t_tests():
    n = {"AP": "AP", "nDCG10": "nDCG@10", "RR": "RR", "P10": "P@10"}
    return "\n".join(f"{t['a']} vs {t['b']} & {n[t['metric']]} & ${t['diff']:+.4f}$ & {t['wins']}/{t['losses']}/{t['ties']} & {p(t['p_perm'])} & {p(t['p_wilcoxon'])} \\\\" for t in C['tests'])
def t_sens():
    names = [("BM25-b0.25", "BM25, $b$=0.25"), ("BM25-b0.5", "BM25, $b$=0.5"), ("BM25", "BM25, $b$=0.75 (default)"), ("BM25-b1.0", "BM25, $b$=1.0"), ("LMD-mu50", "LM-Dirichlet, $\\mu$=50"), ("LMD-mu100", "LM-Dirichlet, $\\mu$=100"), ("LMD-mu200", "LM-Dirichlet, $\\mu$=200"), ("LMD-mu500", "LM-Dirichlet, $\\mu$=500"), ("LMD-mu1000", "LM-Dirichlet, $\\mu$=1000"), ("LM-Dirichlet", "LM-Dirichlet, $\\mu$=2000 (default)"), ("LMJM-l0.1", "LM-JM, $\\lambda$=0.1"), ("LMJM-l0.3", "LM-JM, $\\lambda$=0.3"), ("LMJM-l0.7", "LM-JM, $\\lambda$=0.7")]
    return "\n".join(f"{n} & {c(m,'AP')} & {c(m,'RR')} & {c(m,'nDCG10')} \\\\" for m, n in names)
def t_ex():
    return "\n".join(f"{e['q']} & {esc(e['text'])} & {e['nrel']} & {e['TF-IDF']:.3f} & {e['BM25']:.3f} & {e['LM-Dirichlet']:.3f} \\\\" for e in C['examples'])
def t_ranx():
    return "\n".join(f"{m} & {X[m]['map'][0]:.6f} & {X[m]['map'][1]:.6f} & {X[m]['mrr'][0]:.6f} & {X[m]['mrr'][1]:.6f} & {X[m]['ndcg@10'][0]:.6f} & {X[m]['ndcg@10'][1]:.6f} \\\\" for m in MODELS)
_r = set("abcdef"); _x = list("abcuvw"); _y = list("aubcvdef")
HYP = dict(x_p3=precision_at_k(_x, _r, 3), x_ap=average_precision(_x, _r), y_p3=precision_at_k(_y, _r, 3), y_ap=average_precision(_y, _r))
assert HYP['x_p3'] > HYP['y_p3'] and HYP['x_ap'] < HYP['y_ap']
ctx = dict(c=c, ba=ba, test=test, p=p, C=C, D=D, IDX=IDX, HYP=HYP, B=B, EX=EX, t_b=t_b, t_c=t_c, t_tests=t_tests, t_sens=t_sens, t_ex=t_ex, t_ranx=t_ranx)
for f in sorted(os.listdir(f"{REP}/templates")):
    if not f.endswith(".tex"): continue
    src = open(f"{REP}/templates/preamble.inc").read() + open(f"{REP}/templates/{f}").read()
    tex = re.sub(r"\[\[(.+?)\]\](?!\])", lambda m: str(eval(m.group(1), ctx)), src, flags=re.S)
    open(f"{REP}/{f}", "w").write(tex)
    for _ in range(2):
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", f], cwd=REP, capture_output=True, text=True)
    if r.returncode: print(f, "FAIL", r.stdout[-1500:]); continue
    print(f, "OK", subprocess.run(["pdfinfo", f"{REP}/{f[:-4]}.pdf"], capture_output=True, text=True).stdout.split("Pages:")[-1].split()[0], "overfull:", len(re.findall(r"Overfull \\hbox", r.stdout)))
