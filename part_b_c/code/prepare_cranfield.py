"""Convert the TREC-XML copy of Cranfield to flat files and validate it.
Query IDs are renumbered 1..225 by file position: the raw <num> values are
non-consecutive (1, 2, 4, 8, ...) while the qrels number queries consecutively.
Usage: prepare_cranfield.py <source_dir> <output_dir>"""
import re, json, sys, collections
root, out = sys.argv[1], sys.argv[2]
clean = lambda s: re.sub(r"\s+", " ", s).strip()
raw = open(f"{root}/cran.all.1400.xml", encoding="utf-8").read()
docs = []
for d in re.findall(r"<doc>(.*?)</doc>", raw, flags=re.S):
    g = lambda t: clean((re.search(fr"<{t}>(.*?)</{t}>", d, flags=re.S) or [None, ""])[1])
    docs.append((g("docno"), g("title"), g("text")))
raw = open(f"{root}/cran.qry.xml", encoding="utf-8").read()
qs = [(int(n), clean(t)) for n, t in re.findall(r"<num>\s*(\d+)\s*</num>\s*<title>(.*?)</title>", raw, flags=re.S)]
rows = [l.split() for l in open(f"{root}/cranqrel.trec.txt")]
with open(f"{out}/docs.tsv", "w") as f:
    for i, t, x in docs: f.write(f"{i}\t{t}\t{x}\n")
with open(f"{out}/queries.tsv", "w") as f:
    for s, (n, t) in enumerate(qs, 1): f.write(f"{s}\t{n}\t{t}\n")
with open(f"{out}/qrels.txt", "w") as f:
    for q, _, d, r in rows: f.write(f"{q} 0 {d} {r}\n")
pos = collections.Counter(q for q, _, d, r in rows if int(r) > 0)
ids = {d[0] for d in docs}
stats = dict(docs=len(docs), unique_doc_ids=len(ids), empty_text_docs=[d[0] for d in docs if not d[2]],
             queries=len(qs), raw_max_query_num=max(n for n, _ in qs), mean_query_words=sum(len(t.split()) for _, t in qs) / len(qs),
             qrel_rows=len(rows), qrel_query_ids=len({r[0] for r in rows}), qrel_max_query_id=max(int(r[0]) for r in rows),
             qrel_label_counts=dict(collections.Counter(r[3] for r in rows)), qrel_docs_missing=sum(r[2] not in ids for r in rows),
             queries_with_relevant=len(pos), positive_rows=sum(pos.values()), relevant_per_query_mean=sum(pos.values()) / max(1, len(pos)),
             relevant_per_query_min=min(pos.values()), relevant_per_query_max=max(pos.values()),
             first_raw_ids=[n for n, _ in qs[:6]])
json.dump(stats, open(f"{out}/dataset_stats.json", "w"), indent=1)
print(json.dumps(stats, indent=1))
