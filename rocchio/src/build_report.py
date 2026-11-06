"""Fills the report template from result files, so reported numbers come from actual runs."""
import json, re, subprocess, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")); RES, REP = f"{ROOT}/results", f"{ROOT}/reports"
R = json.load(open(f"{RES}/rocchio_results.json")); D = json.load(open(f"{ROOT}/../data/dataset_stats.json"))
CISI = json.load(open(f"{RES}/cisi_rocchio_summary.json"))
r = lambda s, m: f"{R['residual'][s][m]:.4f}"
a = lambda s, m: f"{R['full'][s][m]:.4f}"
T = lambda m: next(t for t in R['tests'] if t['view'] == 'residual' and t['metric'] == m)
G = lambda A, b, g: R['grid'][f"a{float(A)}_b{float(b)}_g{float(g)}_k10"]
BASE = R['residual']['before']['AP']
K10 = [v for v in R['grid'].values() if v['k'] == 10]
BEST = max(K10, key=lambda v: v['residual']['AP'])
assert sum(v['residual']['AP'] < BASE for v in K10) == 12 and len(K10) == 115
assert all(v['beta'] == 0 for v in K10 if v['residual']['AP'] < BASE)
assert abs(G(.5,.75,.5)['residual']['AP'] - G(1,1.5,1)['residual']['AP']) < 1e-4
assert CISI['gamma05'] > CISI['gamma0'] and G(1,.75,.5)['residual']['AP'] < G(1,.75,0)['residual']['AP']
assert R['removed_gamma1']['queries'] == 0
def p(x): return "$<0.00001$" if x < 1e-5 else f"{x:.5f}"
def t_ba():
    names = [("P", "Precision (whole list)"), ("R", "Recall (whole list)"), ("F1", "F1 (whole list)"), ("P3", "P@3"), ("P10", "P@10"), ("R10", "Recall@10"), ("F1_10", "F1@10"), ("AP", "MAP"), ("RR", "MRR"), ("nDCG10", "nDCG@10")]
    F, S = R['full'], R['residual']
    return "\n".join(f"{n} & {F['before'][k]:.4f} & {F['after'][k]:.4f} & ${F['after'][k]-F['before'][k]:+.4f}$ & {S['before'][k]:.4f} & {S['after'][k]:.4f} & ${S['after'][k]-S['before'][k]:+.4f}$ \\\\" for k, n in names)
def t_tests():
    n = {"AP": "AP", "P10": "P@10", "P3": "P@3", "nDCG10": "nDCG@10", "RR": "RR", "R10": "Recall@10"}
    return "\n".join(f"{n[t['metric']]} & ${t['diff']:+.4f}$ & {t['up']} & {t['down']} & {t['same']} & {p(t['p'])} \\\\" for t in R['tests'] if t['view'] == 'residual')
def t_group():
    return "\n".join(f"{g} & {v['n']} & {v['ap0']:.4f} & {v['ap1']:.4f} & ${v['dAP']:+.4f}$ & {v['down']} \\\\" for g, v in R['by_rel'].items())
def t_grid():
    Bs, Gs = [0, .25, .5, .75, 1, 1.5], [0, .15, .25, .5, 1]
    vals = [G(1, b, g)['residual']['AP'] for b in Bs for g in Gs]; lo, hi = min(vals), max(vals)
    def cell(b, g):   # one-hue heat map: light to medium teal, so dark text stays readable
        v = G(1, b, g)['residual']['AP']; t = (v - lo) / (hi - lo)
        c = [x + (y - x) * t for x, y in zip((0.93, 0.97, 0.96), (0.36, 0.72, 0.67))]
        return f"\\cellcolor[rgb]{{{c[0]:.3f},{c[1]:.3f},{c[2]:.3f}}}{v:.4f} ({G(1,b,g)['down']})"
    return "\n".join(f"\\cellcolor{{white}}$\\beta$ = {b} & " + " & ".join(cell(b, g) for g in Gs) + " \\\\" for b in Bs)
def t_alpha():
    return "\n".join(f"{A} & {G(A,.75,.15)['residual']['AP']:.4f} & {G(A,.75,.15)['full']['AP']:.4f} & {G(A,.75,.15)['up']} & {G(A,.75,.15)['down']} \\\\" for A in [0, .5, 1, 2, ])
def t_k():
    rows = []
    for k in [3, 5, 10, 20]:
        v = R['grid'][f"a1.0_b0.75_g0.15_k{k}"]
        rows.append(f"{k} & {v['n']} & {v['base_residual']['AP']:.4f} & {v['residual']['AP']:.4f} & ${v['residual']['AP']-v['base_residual']['AP']:+.4f}$ \\\\")
    return "\n".join(rows)
def t_down():
    w = sorted([x for x in R['rows'] if x['dAP'] < 0], key=lambda x: x['dAP'])[:5]
    return "\n".join(f"{x['q']} & {x['rel_top10']} & {x['ap0']:.4f} & {x['ap1']:.4f} & {' '.join(y.split(':')[0] for y in x['top_added'].split()[:5]) or '(no words added)'} \\\\" for x in w)
ctx = dict(CISI=CISI, R=R, D=D, r=r, a=a, T=T, G=G, BASE=BASE, BEST=BEST, t_ba=t_ba, t_tests=t_tests, t_group=t_group, t_grid=t_grid, t_alpha=t_alpha, t_k=t_k, t_down=t_down)
# demo transcript without the long ID list
lines = open(f"{RES}/demo_query20.txt").read().splitlines()
lines = [("Judged query IDs: 1 2 3 4 ... (all 225 listed)" if l.startswith("Judged query IDs") else l) for l in lines]
open(f"{REP}/demo_query20_trim.txt", "w").write("\n".join(lines) + "\n")
f = "Rocchio_Cranfield_Report.tex"
src = open(f"{REP}/templates/preamble.inc").read() + open(f"{REP}/templates/{f}").read()
open(f"{REP}/{f}", "w").write(re.sub(r"\[\[(.+?)\]\](?!\])", lambda m: str(eval(m.group(1), ctx)), src, flags=re.S))
for _ in range(2):
    o = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", f], cwd=REP, capture_output=True, text=True)
print("OK" if o.returncode == 0 else o.stdout[-1500:], subprocess.run(["pdfinfo", f"{REP}/{f[:-4]}.pdf"], capture_output=True, text=True).stdout.split("Pages:")[-1].split()[0], "overfull:", len(re.findall(r"Overfull \\hbox", o.stdout)))
