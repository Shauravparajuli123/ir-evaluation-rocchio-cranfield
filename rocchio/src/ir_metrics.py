"""IR evaluation metrics shared by Part B and Part C. A ranked list is a list of doc IDs."""
import math

def precision(ranked, rel):
    return sum(d in rel for d in ranked) / len(ranked) if ranked else 0.0

def recall(ranked, rel):
    return sum(d in rel for d in ranked) / len(rel) if rel else 0.0

def f1(ranked, rel):
    p, r = precision(ranked, rel), recall(ranked, rel)
    return 2 * p * r / (p + r) if p + r else 0.0

def precision_at_k(ranked, rel, k):
    """The denominator stays k even if fewer than k documents were returned."""
    return sum(d in rel for d in ranked[:k]) / k

def reciprocal_rank(ranked, rel):
    for i, d in enumerate(ranked, 1):
        if d in rel:
            return 1 / i
    return 0.0

def average_precision(ranked, rel):
    """Relevant documents that were not retrieved contribute 0 (division by |rel|)."""
    hits, total = 0, 0.0
    for i, d in enumerate(ranked, 1):
        if d in rel:
            hits += 1
            total += hits / i
    return total / len(rel) if rel else 0.0

def dcg(gains):
    return sum(g / math.log2(i + 1) for i, g in enumerate(gains, 1))

def ndcg_at_k(ranked, grades, k):
    """grades: doc -> gain; unjudged documents have gain 0."""
    actual = dcg([grades.get(d, 0) for d in ranked[:k]])
    ideal = dcg(sorted(grades.values(), reverse=True)[:k])
    return actual / ideal if ideal else 0.0

def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0
