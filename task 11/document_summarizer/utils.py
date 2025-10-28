# utils.py
# Placeholder for advanced analysis: e.g., using embeddings to classify sentences as technical vs story.
# Current app uses the model to return percentages directly, but you can implement local heuristics here.

def simple_sentence_based_ratio(text):
    """
    Very naive heuristic: sentences containing technical keywords count as 'technical'.
    Returns (technical_pct, story_pct)
    """
    import re
    technical_keywords = [
        "algorithm", "data", "API", "protocol", "function", "variable", "CPU", "memory",
        "latency", "throughput", "compile", "deploy", "server", "client", "database"
    ]
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    tech_count = 0
    for s in sentences:
        s_lower = s.lower()
        for k in technical_keywords:
            if k.lower() in s_lower:
                tech_count += 1
                break
    total = len(sentences) if sentences else 1
    tech_pct = int(round(100 * tech_count / total))
    story_pct = 100 - tech_pct
    return tech_pct, story_pct
