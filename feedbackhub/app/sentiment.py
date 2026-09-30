"""Small lexicon-based sentiment scorer with simple negation handling.

Returns a score in [-1, 1] and a label (positive / neutral / negative).
It is intentionally lightweight and dependency-free; swap in an ML model later
behind the same `analyze` interface.
"""
import re

POSITIVE = {
    "good", "great", "excellent", "amazing", "love", "loved", "easy", "fast",
    "helpful", "smooth", "friendly", "awesome", "fantastic", "reliable",
    "intuitive", "happy", "perfect", "best", "nice", "satisfied", "quick",
}
NEGATIVE = {
    "bad", "poor", "terrible", "awful", "hate", "hated", "slow", "difficult",
    "confusing", "buggy", "broken", "crash", "crashes", "crashed", "worst",
    "annoying", "frustrating", "disappointed", "useless", "unreliable", "error",
}
NEGATIONS = {"not", "no", "never", "hardly", "isnt", "wasnt", "dont", "doesnt", "didnt", "cant", "cannot"}

_TOKEN_RE = re.compile(r"[a-z']+")


def analyze(text):
    tokens = [t.replace("'", "") for t in _TOKEN_RE.findall(text.lower())]
    pos = neg = 0
    for i, tok in enumerate(tokens):
        negated = i > 0 and tokens[i - 1] in NEGATIONS
        if tok in POSITIVE:
            if negated:
                neg += 1
            else:
                pos += 1
        elif tok in NEGATIVE:
            if negated:
                pos += 1
            else:
                neg += 1

    total = pos + neg
    score = round((pos - neg) / total, 3) if total else 0.0
    if score > 0.2:
        label = "positive"
    elif score < -0.2:
        label = "negative"
    else:
        label = "neutral"
    return score, label
