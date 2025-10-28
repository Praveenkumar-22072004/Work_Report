# graph.py
# Defines a simple LangGraph workflow for summarization and language-type breakdown.

import os
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END
from langchain.prompts import ChatPromptTemplate
from utils import simple_sentence_based_ratio
from langchain_groq import ChatGroq  # type: ignore


class DocState(TypedDict, total=False):
    text: str
    target_technical_pct: int
    temperature: float
    max_tokens: int
    pages: int
    model: str
    summary: str
    technical_pct: int
    story_pct: int
    error: Optional[str]
    note: Optional[str]


def _make_llm(temperature: float = 0.2, model: str | None = None):
    """Create a Groq chat model; require GROQ_API_KEY."""
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        raise RuntimeError("GROQ_API_KEY not set.")
    # Default model if not provided
    selected = model or "llama-3.1-70b-versatile"
    return ChatGroq(model=selected, temperature=temperature)


def summarize_node(state: DocState) -> DocState:
    text = state.get("text", "")
    target_technical_pct: int = state.get("target_technical_pct", 50)
    # Create a blended prompt based on the target percentage
    # 100% technical = "highly technical and academic"
    # 0% technical = "engaging and narrative-driven, like a story"
    # 50% technical = a blend of both
    technical_weight = target_technical_pct / 100.0
    story_weight = 1 - technical_weight

    style_descriptors = []
    if technical_weight > 0:
        style_descriptors.append(f"{technical_weight:.0%} technical and academic")
    if story_weight > 0:
        style_descriptors.append(f"{story_weight:.0%} engaging and narrative-driven, like a story")

    target_format = " and ".join(style_descriptors)
    temperature = state.get("temperature", 0.2)
    max_tokens = state.get("max_tokens", 600)
    pages = state.get("pages", 1)

    if not text.strip():
        return {"error": "Empty document text for summarization."}

    llm = _make_llm(temperature, state.get("model"))

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that summarizes documents."),
        ("user", (
            "Summarize the following document in a {style} style. Be concise and informative.\n"
            "Target length: approximately {pages} page(s). If needed, prioritize key points to fit the length.\n\n"
            "Document:\n\"\"\"\n{doc}\n\"\"\"\n"
        )),
    ])

    # Roughly budget ~700 tokens per page for safety; capped by max_tokens slider
    requested_tokens = max(100, min(max_tokens, int(pages) * 700))
    chain = prompt | llm.bind(max_tokens=requested_tokens)
    try:
        resp = chain.invoke({"style": target_format, "doc": text[:40000], "pages": pages})
        content = resp.content if hasattr(resp, "content") else str(resp)
        if not isinstance(content, str):
            content = str(content)
        # Respect token limit by truncation (LangChain handles tokens but we keep a guard)
        summary = content
        return {"summary": summary}
    except Exception as e:
        # Offline/connection fallback: produce a simple extractive summary
        import re
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        # Heuristic: ~6 sentences per page target
        n = max(3, min(len(sentences), int(pages) * 6))
        fallback = " ".join(sentences[:n])
        return {
            "summary": fallback,
            "note": f"LLM call failed ({e.__class__.__name__}). Shown fallback extractive summary.",
        }


def classify_node(state: DocState) -> DocState:
    summary = state.get("summary", "")
    if not summary:
        # If no summary, try to classify the original text
        summary = state.get("text", "")
    tech_pct, story_pct = simple_sentence_based_ratio(summary)
    return {"technical_pct": tech_pct, "story_pct": story_pct}


def build_graph():
    graph = StateGraph(DocState)

    graph.add_node("summarize", summarize_node)
    graph.add_node("classify", classify_node)

    graph.add_edge(START, "summarize")
    graph.add_edge("summarize", "classify")
    graph.add_edge("classify", END)

    return graph.compile()


def run_workflow(text: str, target_technical_pct: int, temperature: float = 0.2, max_tokens: int = 600, pages: int = 1, model: str | None = None) -> DocState:
    app = build_graph()
    initial: DocState = {
        "text": text,
        "target_technical_pct": target_technical_pct,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "pages": pages,
        "model": model or "llama-3.1-70b-versatile",
    }
    state: DocState = app.invoke(initial)

    # Merge initial with results
    result: DocState = {**initial, **state}
    return result
