"""Shared spelling aliases used by parsing and matching."""
ALIASES = {
    "Scikit-Learn": ["scikit learn", "sklearn"],
    "PyTorch": ["torch"],
    "NLP": ["natural language processing"],
    "LLM": ["large language model", "large language models", "llms"],
    "RAG": ["retrieval augmented generation", "retrieval-augmented generation"],
    "Vector Databases": ["vector database", "vector db", "vector dbs", "faiss", "chroma", "pinecone"],
    "REST API": ["rest apis", "restful api", "restful apis"],
    "AWS": ["amazon web services"],
    "CI/CD": ["continuous integration", "continuous delivery"],
}


def normalize_skill(skill: str) -> str:
    value = skill.strip().casefold()
    for canonical, aliases in ALIASES.items():
        if value in [canonical.casefold(), *aliases]:
            return canonical.casefold()
    return value
