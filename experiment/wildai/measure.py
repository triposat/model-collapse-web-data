import json, gzip, re, random, statistics
from collections import Counter
d = json.load(open("sample.json"))
W = re.compile(r"[a-z][a-z'\-]*")
L = 300
def prep(rows):
    out = []
    for r in rows:
        ws = W.findall(r["text"].lower())
        if len(ws) >= L: out.append((ws[:L], r))
    return out
H, A = prep(d["human"]), prep(d["ai"])
n = min(len(H), len(A)); rnd = random.Random(0); H = rnd.sample(H, n); A = rnd.sample(A, n)
def per_doc(ws):
    t = " ".join(ws).encode()
    bi = list(zip(ws, ws[1:])); fg = list(zip(ws, ws[1:], ws[2:], ws[3:]))
    return {"gzip": len(t)/len(gzip.compress(t)), "distinct2": len(set(bi))/len(bi), "rep4": len(fg) != len(set(fg)), "distinct1": len(set(ws))/len(ws)}
def summarize(S, name):
    m = [per_doc(ws) for ws, _ in S]
    allw = [w for ws, _ in S for w in ws]
    res = {k: round(statistics.mean(x[k] for x in m), 3) for k in m[0]}
    res["corpus_vocab"] = len(set(allw))
    def boot(k):
        vals = [x[k] for x in m]; bs = sorted(statistics.mean(rnd.choices(vals, k=len(vals))) for _ in range(1000))
        return round(bs[25], 3), round(bs[975], 3)
    res["gzip_ci"] = boot("gzip"); res["distinct2_ci"] = boot("distinct2"); res["rep4_ci"] = boot("rep4")
    print(name, len(S), res)
summarize(H, "human"); summarize(A, "ai")
print("formats human", Counter(r["format"] for _, r in H).most_common(5))
print("formats ai", Counter(r["format"] for _, r in A).most_common(5))
print("dumps human", Counter(r["dump"][:12] for _, r in H).most_common(4)); print("dumps ai", Counter(r["dump"][:12] for _, r in A).most_common(4))
# matched by format: compare within the top shared formats
fm = Counter(r["format"] for _, r in H) & Counter(r["format"] for _, r in A)
for f, _ in fm.most_common(4):
    h = [x for x in H if x[1]["format"] == f]; a = [x for x in A if x[1]["format"] == f]
    k = min(len(h), len(a))
    if k < 40: continue
    gh = statistics.mean(per_doc(ws)["gzip"] for ws, _ in h[:k]); ga = statistics.mean(per_doc(ws)["gzip"] for ws, _ in a[:k])
    dh = statistics.mean(per_doc(ws)["distinct2"] for ws, _ in h[:k]); da = statistics.mean(per_doc(ws)["distinct2"] for ws, _ in a[:k])
    rh = statistics.mean(per_doc(ws)["rep4"] for ws, _ in h[:k]); ra = statistics.mean(per_doc(ws)["rep4"] for ws, _ in a[:k])
    print(f"format={f} n={k} gzip h={gh:.3f} a={ga:.3f} | distinct2 h={dh:.3f} a={da:.3f} | rep4 h={rh:.2f} a={ra:.2f}")
# Stratified by format: same number of docs per format in both groups
fm2 = Counter(r["format"] for _, r in H) & Counter(r["format"] for _, r in A)
Hs, As = [], []
for f, k in fm2.items():
    Hs += [x for x in H if x[1]["format"] == f][:k]; As += [x for x in A if x[1]["format"] == f][:k]
for name, S in (("human_matched", Hs), ("ai_matched", As)):
    allw = [w for ws, _ in S for w in ws]
    m = [per_doc(ws) for ws, _ in S]
    print(name, len(S), "vocab", len(set(allw)), "gzip", round(statistics.mean(x["gzip"] for x in m), 3), "rep4", round(statistics.mean(x["rep4"] for x in m), 3), "distinct2", round(statistics.mean(x["distinct2"] for x in m), 3))
