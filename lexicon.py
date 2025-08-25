LEXICON = {
    "scop3ptm": ["ptm", "post-translational", "ubiquitin", "acetyl", "methyl",
                 "glyco", "sumoyl", "neddyl", "palmitoyl"],
    "phospho_both": ["phosphosite", "p-site", "phosphorylation site"],
    "projects": ["pxd", "proteomexchange", "pride", "tissue", "instrument",
                 "experiment", "publication", "disease", "pathology", "relevance", "affect"],
    "mutations": ["mutation", "variant", "humsavar", "disease-associated"]
}

def classify_query(query: str):
    if not query:
        return {"mode": "llm", "db": None, "needs_projects": False, "needs_mutations": False}
        
    q = query.lower()
    needs_projects = any(t in q for t in LEXICON["projects"])
    needs_mutations = any(t in q for t in LEXICON["mutations"])

    if any(t in q for t in LEXICON["phospho_both"]):
        return {"mode": "sql", "db": "both", "needs_projects": needs_projects, "needs_mutations": needs_mutations}
    if any(t in q for t in LEXICON["scop3ptm"]):
        return {"mode": "sql", "db": "scop3ptm", "needs_projects": needs_projects, "needs_mutations": needs_mutations}

    return {"mode": "llm", "db": None, "needs_projects": needs_projects, "needs_mutations": needs_mutations}