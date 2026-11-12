from pathlib import Path

import pandas as pd
import spacy
from spacy.matcher import PhraseMatcher

nlp = spacy.blank("en")

SOFT_SKILLS = {"communication", "teamwork", "leadership", "problem solving",
               "time management", "adaptability", "creativity", "critical thinking"}

# Other spellings -> the skill name used in skills_list.csv
ALIASES = {
    "ml": "machine learning", "scikit learn": "scikit-learn", "sklearn": "scikit-learn",
    "natural language processing": "nlp", "js": "javascript", "reactjs": "react",
    "node": "node.js", "nodejs": "node.js", "postgres": "postgresql", "mongo db": "mongodb",
    "k8s": "kubernetes", "cicd": "ci/cd", "amazon web services": "aws", "team work": "teamwork",
    "problem-solving": "problem solving", "powerbi": "power bi",
}

_csv_path = Path(__file__).parent / "skills_list.csv"
SKILLS = pd.read_csv(_csv_path)["skill"].str.lower().str.strip().tolist()

_phrase_to_skill = {s: s for s in SKILLS}
_phrase_to_skill.update(ALIASES)

_groups = {}
for phrase, canon in _phrase_to_skill.items():
    _groups.setdefault(canon, []).append(nlp.make_doc(phrase))

matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
for canon, patterns in _groups.items():
    matcher.add(canon, patterns)


def extract_skills(text):
    """Return a sorted list of skills found in the text."""
    doc = nlp(text)
    return sorted({nlp.vocab.strings[mid] for mid, _, _ in matcher(doc)})


def skill_type(skill):
    return "soft" if skill in SOFT_SKILLS else "technical"