"""
plagiarism_core.py
==================
Core engine of the Plagiarism Detector.

Pipeline
--------
1. normalize()        clean text (lowercase, drop punctuation/spaces) and remember
                      where every kept character sat in the original text
2. kgram_hashes()     Rabin-Karp rolling hash of every k-character window
3. find_matches_rk()  look up A's k-gram hashes in an index of B's hashes,
                      then VERIFY character by character (spurious hits are counted)
   find_matches_naive()  same job without hashing (used for the benchmark)
4. merge_blocks()     join consecutive k-gram matches into copied passages
5. analyze()          coverage %, verdict, passages, highlight spans
"""
import argparse
import html
import random
import time
from collections import defaultdict

BASE = 257                    # d : base of the polynomial hash
MOD = (1 << 61) - 1           # q : large prime (2^61 - 1) -> almost no spurious hits


# ------------------------------------------------------------------
# 1. PREPROCESSING
# ------------------------------------------------------------------
def normalize(text):
    """Keep only letters/digits, lowercase them.
    Returns (clean_string, positions) where positions[i] is the index in the
    ORIGINAL text of clean_string[i]. This lets us highlight the original text."""
    chars, positions = [], []
    for idx, ch in enumerate(text):
        if ch.isalnum():
            for c in ch.lower():
                chars.append(c)
                positions.append(idx)
    return "".join(chars), positions


# ------------------------------------------------------------------
# 2. ROLLING HASH OF ALL k-GRAMS
# ------------------------------------------------------------------
def kgram_hashes(s, k, d=BASE, q=MOD):
    """hash of s[i:i+k] for every i, computed in O(n) with a rolling hash."""
    n = len(s)
    if k <= 0 or n < k:
        return []
    h = pow(d, k - 1, q)                       # d^(k-1) mod q
    t = 0
    for c in s[:k]:
        t = (d * t + ord(c)) % q
    out = [t]
    for i in range(n - k):                     # slide the window by one char
        t = (d * (t - ord(s[i]) * h) + ord(s[i + k])) % q
        out.append(t)
    return out


def _verify(a, i, b, j, k):
    """Compare a[i:i+k] with b[j:j+k] char by char. Returns (equal, comparisons)."""
    c = 0
    while c < k:
        if a[i + c] != b[j + c]:
            return False, c + 1
        c += 1
    return True, k


# ------------------------------------------------------------------
# 3. FINDING MATCHING k-GRAMS
# ------------------------------------------------------------------
def find_matches_rk(a, b, k, d=BASE, q=MOD):
    """Rabin-Karp approach. Returns (pairs, stats); pairs = [(i, j)] with a[i:i+k]==b[j:j+k]."""
    start = time.perf_counter()
    pairs = []
    stats = {"kgrams_hashed": 0, "hash_lookups": 0, "hash_hits": 0,
             "char_comparisons": 0, "spurious_hits": 0}

    hb = kgram_hashes(b, k, d, q)
    ha = kgram_hashes(a, k, d, q)
    stats["kgrams_hashed"] = len(ha) + len(hb)

    index = defaultdict(list)                  # hash -> positions in B
    for j, hv in enumerate(hb):
        index[hv].append(j)

    for i, hv in enumerate(ha):
        stats["hash_lookups"] += 1
        for j in index.get(hv, ()):
            stats["hash_hits"] += 1
            ok, comps = _verify(a, i, b, j, k)
            stats["char_comparisons"] += comps
            if ok:
                pairs.append((i, j))
            else:
                stats["spurious_hits"] += 1    # same hash, different text
    stats["time_ms"] = (time.perf_counter() - start) * 1000
    return pairs, stats


def find_matches_naive(a, b, k, d=BASE, q=MOD):
    """Baseline: compare every k-gram of A with every k-gram of B directly."""
    start = time.perf_counter()
    pairs = []
    stats = {"kgrams_hashed": 0, "hash_lookups": 0, "hash_hits": 0,
             "char_comparisons": 0, "spurious_hits": 0}
    for i in range(len(a) - k + 1):
        for j in range(len(b) - k + 1):
            ok, comps = _verify(a, i, b, j, k)
            stats["char_comparisons"] += comps
            if ok:
                pairs.append((i, j))
    stats["time_ms"] = (time.perf_counter() - start) * 1000
    return pairs, stats


# ------------------------------------------------------------------
# 4. MERGING MATCHES INTO PASSAGES
# ------------------------------------------------------------------
def merge_blocks(pairs, k):
    """Join k-gram matches on the same diagonal (j - i constant) that overlap or
    touch into blocks (i, j, length). 40 consecutive hits become ONE passage."""
    blocks = []
    for i, j in sorted(pairs, key=lambda p: (p[1] - p[0], p[0])):
        if blocks:
            bi, bj, bl = blocks[-1]
            if bj - bi == j - i and i <= bi + bl:
                blocks[-1] = (bi, bj, max(bl, i + k - bi))
                continue
        blocks.append((i, j, k))
    return sorted(blocks)


def drop_redundant(blocks):
    """Keep a block only if it covers NEW text in A or in B (longest blocks first).
    Removes noise when a phrase is repeated inside one document."""
    kept, cov_a, cov_b = [], [], []
    for ai, bj, length in sorted(blocks, key=lambda b: -b[2]):
        new_a = covered_length(cov_a + [(ai, ai + length)]) > covered_length(cov_a)
        new_b = covered_length(cov_b + [(bj, bj + length)]) > covered_length(cov_b)
        if new_a or new_b:
            kept.append((ai, bj, length))
            cov_a.append((ai, ai + length))
            cov_b.append((bj, bj + length))
    return sorted(kept)


def merge_intervals(intervals):
    """Union of [start, end) intervals."""
    out = []
    for s, e in sorted(intervals):
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def covered_length(intervals):
    return sum(e - s for s, e in merge_intervals(intervals))


# ------------------------------------------------------------------
# 5. FULL ANALYSIS
# ------------------------------------------------------------------
def verdict(score):
    if score >= 60:
        return "High similarity - likely plagiarised"
    if score >= 30:
        return "Moderate similarity - review the highlighted passages"
    if score >= 10:
        return "Low similarity - small overlaps"
    return "Very low similarity - appears original"


def analyze(text_a, text_b, k=20, d=BASE, q=MOD, method="rabin-karp"):
    na, pa = normalize(text_a)
    nb, pb = normalize(text_b)
    result = {"k": k, "method": method, "len_a": len(na), "len_b": len(nb),
              "blocks": [], "spans_a": [], "spans_b": [], "pairs": [],
              "coverage_a": 0.0, "coverage_b": 0.0, "score": 0.0,
              "verdict": "", "stats": {}, "too_short": False}
    if len(na) < k or len(nb) < k:
        result["too_short"] = True
        result["verdict"] = f"Documents must each contain at least {k} letters/digits."
        return result

    finder = find_matches_rk if method == "rabin-karp" else find_matches_naive
    pairs, stats = finder(na, nb, k, d, q)
    blocks = drop_redundant(merge_blocks(pairs, k))

    passages, spans_a, spans_b = [], [], []
    for ai, bj, length in blocks:
        sa = (pa[ai], pa[ai + length - 1] + 1)          # back to ORIGINAL text positions
        sb = (pb[bj], pb[bj + length - 1] + 1)
        spans_a.append(sa)
        spans_b.append(sb)
        passages.append({"chars": length, "span_a": sa, "span_b": sb,
                         "text_a": text_a[sa[0]:sa[1]], "text_b": text_b[sb[0]:sb[1]]})
    passages.sort(key=lambda p: -p["chars"])

    cov_a = 100 * covered_length([(ai, ai + L) for ai, _, L in blocks]) / len(na)
    cov_b = 100 * covered_length([(bj, bj + L) for _, bj, L in blocks]) / len(nb)
    result.update(blocks=passages, spans_a=merge_intervals(spans_a),
                  spans_b=merge_intervals(spans_b), pairs=pairs,
                  coverage_a=cov_a, coverage_b=cov_b,
                  score=max(cov_a, cov_b), stats=stats)
    result["verdict"] = verdict(result["score"])
    return result


def compare_many(docs, k=20, d=BASE, q=MOD):
    """docs = {name: text}. Returns a list of pairwise results."""
    names = list(docs)
    rows = []
    for x in range(len(names)):
        for y in range(x + 1, len(names)):
            r = analyze(docs[names[x]], docs[names[y]], k, d, q)
            rows.append({"Document 1": names[x], "Document 2": names[y],
                         "% of Doc 1 found in Doc 2": round(r["coverage_a"], 1),
                         "% of Doc 2 found in Doc 1": round(r["coverage_b"], 1),
                         "Similarity %": round(r["score"], 1),
                         "Passages": len(r["blocks"]), "Verdict": r["verdict"]})
    return rows


def highlight(text, spans):
    """HTML of the original text with the copied spans wrapped in <mark>."""
    out, last = [], 0
    for s, e in merge_intervals(spans):
        out.append(html.escape(text[last:s]))
        out.append("<mark>" + html.escape(text[s:e]) + "</mark>")
        last = e
    out.append(html.escape(text[last:]))
    return ("<div style='white-space:pre-wrap;line-height:1.6;max-height:420px;"
            "overflow-y:auto;padding:6px'>" + "".join(out) + "</div>")


# ------------------------------------------------------------------
# 6. BENCHMARK HELPERS (Naive vs Rabin-Karp)
# ------------------------------------------------------------------
def generate_pair(n_chars, copy_ratio=0.3, seed=7):
    """Two synthetic documents of ~n_chars; B contains a copied chunk of A."""
    rnd = random.Random(seed)
    letters = "abcdefghijklmnopqrstuvwxyz"
    vocab = ["".join(rnd.choice(letters) for _ in range(rnd.randint(3, 9)))
             for _ in range(1000)]

    def gen():
        words, total = [], 0
        while total < n_chars:
            w = rnd.choice(vocab)
            words.append(w)
            total += len(w) + 1
        return words

    a_words, b_words = gen(), gen()
    copy_len = int(len(a_words) * copy_ratio)
    start = rnd.randrange(0, max(1, len(a_words) - copy_len))
    b_words[rnd.randint(0, len(b_words)):0] = a_words[start:start + copy_len]
    return " ".join(a_words), " ".join(b_words)


def run_benchmark(sizes, k=20, copy_ratio=0.3, d=BASE, q=MOD):
    rows = []
    for n in sizes:
        a, b = generate_pair(n, copy_ratio)
        for method, label in (("naive", "Naive"), ("rabin-karp", "Rabin-Karp")):
            r = analyze(a, b, k, d, q, method)
            rows.append({"Text length": n, "Method": label,
                         "Time (ms)": round(r["stats"]["time_ms"], 2),
                         "Char comparisons": r["stats"]["char_comparisons"],
                         "Hash lookups": r["stats"]["hash_lookups"],
                         "Spurious hits": r["stats"]["spurious_hits"],
                         "Passages": len(r["blocks"]),
                         "Similarity %": round(r["score"], 1)})
    return rows


# ------------------------------------------------------------------
# Command-line use:  python plagiarism_core.py fileA.txt fileB.txt [-k 20]
# ------------------------------------------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Compare two text files for copied passages.")
    ap.add_argument("file_a")
    ap.add_argument("file_b")
    ap.add_argument("-k", type=int, default=20, help="minimum match length in characters")
    args = ap.parse_args()
    ta = open(args.file_a, encoding="utf-8", errors="ignore").read()
    tb = open(args.file_b, encoding="utf-8", errors="ignore").read()
    res = analyze(ta, tb, args.k)
    print(f"{res['verdict']}")
    print(f"{args.file_a}: {res['coverage_a']:.1f}% found in {args.file_b}")
    print(f"{args.file_b}: {res['coverage_b']:.1f}% found in {args.file_a}")
    print(f"Stats: {res['stats']}")
    for p in res["blocks"][:10]:
        print(f"\n[{p['chars']} chars] {p['text_a'][:150]!r}")
