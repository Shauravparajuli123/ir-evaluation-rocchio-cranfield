"""Before-and-after chart for the report. Usage: make_chart.py <results_json> <output_pdf>"""
import json, sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
R = json.load(open(sys.argv[1]))["residual"]
names = [("AP", "MAP"), ("RR", "MRR"), ("P10", "P@10"), ("nDCG10", "nDCG@10")]
BEFORE, AFTER, INK, MUTED = "#D97706", "#0D9488", "#1E293B", "#64748B"
plt.rcParams["font.family"] = ["Liberation Sans", "DejaVu Sans"]
fig, ax = plt.subplots(figsize=(6.6, 2.3))
w, gap = 0.36, 0.02
for i, (k, _) in enumerate(names):
    b, a = R["before"][k], R["after"][k]
    ax.bar(i - w / 2 - gap, b, w, color=BEFORE, label="Before feedback" if i == 0 else None)
    ax.bar(i + w / 2 + gap, a, w, color=AFTER, label="After feedback" if i == 0 else None)
    ax.text(i - w / 2 - gap, b + .008, f"{b:.3f}", ha="center", va="bottom", fontsize=8, color=INK)
    ax.text(i + w / 2 + gap, a + .008, f"{a:.3f}", ha="center", va="bottom", fontsize=8, color=INK)
ax.set_xticks(range(len(names)), [n for _, n in names], fontsize=9, color=INK)
ax.tick_params(axis="x", length=0); ax.tick_params(axis="y", labelsize=8, colors=MUTED, length=0)
ax.set_ylim(0, 0.54); ax.yaxis.grid(True, color="#E2E8F0", lw=.6); ax.set_axisbelow(True)
for s in ["top", "right", "left"]: ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#CBD5E1")
ax.legend(frameon=False, fontsize=8.5, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, labelcolor=INK)
fig.tight_layout(pad=.3); fig.savefig(sys.argv[2])
