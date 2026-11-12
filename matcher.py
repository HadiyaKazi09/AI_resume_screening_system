from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def match_skills(required, candidate):
    required_set, candidate_set = set(required), set(candidate)
    matched = sorted(required_set & candidate_set)
    missing = sorted(required_set - candidate_set)
    pct = round(len(matched) / len(required_set) * 100, 1) if required_set else 0.0
    return matched, missing, pct


def weighted_match(required, matched, weight_of):
    """Weighted % = weight of matched skills / weight of required skills x 100."""
    total = sum(weight_of(s) for s in required)
    got = sum(weight_of(s) for s in matched)
    return round(got / total * 100, 1) if total else 0.0


def recommendation(weighted_pct):
    if weighted_pct >= 75:
        return "Strong fit"
    if weighted_pct >= 50:
        return "Moderate fit"
    return "Low fit"


def text_similarity(resume_text, job_text):
    try:
        vectors = TfidfVectorizer(stop_words="english").fit_transform([resume_text, job_text])
        return round(float(cosine_similarity(vectors[0], vectors[1])[0][0]) * 100, 1)
    except ValueError:
        return 0.0