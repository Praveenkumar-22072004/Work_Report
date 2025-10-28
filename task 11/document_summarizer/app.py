import os
import streamlit as st
from io import StringIO, BytesIO
import PyPDF2
import matplotlib.pyplot as plt
from graph import run_workflow
import html

# Must be the first Streamlit call
st.set_page_config(page_title="Document Summarizer", layout="wide")

# Lightweight .env loader (no external dependency)
def _load_env_file(path: str = ".env"):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and not os.environ.get(k):
                            os.environ[k] = v
    except Exception:
        # Fail silently; sidebar input can still set the key
        pass

_load_env_file()

# Use Groq API key from environment (after loading .env)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.warning("Set GROQ_API_KEY as an environment variable for summarization to work. The app will still let you run local preprocessing without calling an LLM.")

# ---------- Styles ----------
st.markdown(
    """
    <style>
    :root {
        /* Plants & Flowers palette */
        --accent: #2e7d32; /* Leaf green */
        --accent-2: #ff69b4; /* Floral pink */
        --bg-card: rgba(255,255,255,0.03);
        --border-subtle: rgba(255,255,255,0.08);
    }
    /* Page background */
    html, body {
        background: radial-gradient(1200px 600px at 10% 10%, rgba(46,125,50,0.18), transparent 60%),
                    radial-gradient(1000px 500px at 90% 20%, rgba(255,105,180,0.15), transparent 60%),
                    radial-gradient(900px 500px at 20% 90%, rgba(46,125,50,0.12), transparent 60%),
                    #0b0f0c;
    }
    /* Sidebar background */
    [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(180deg, rgba(46,125,50,0.20), rgba(255,105,180,0.12));
        border-right: 1px solid var(--border-subtle);
        backdrop-filter: blur(6px);
    }
    /* Main background card feel */
    .block-container {
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0));
        border-radius: 12px;
    }
    .hero {
        padding: 1.25rem 1.5rem; border-radius: 14px; position: relative;
        background: linear-gradient(120deg, color-mix(in srgb, var(--accent) 18%, transparent), color-mix(in srgb, var(--accent-2) 18%, transparent));
        border: 1px solid var(--border-subtle);
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        overflow: hidden;
    }
    /* subtle leaf vein pattern */
    .hero::after {
        content: ""; position: absolute; inset: -20%;
        background: radial-gradient(circle at 20% 20%, rgba(255,255,255,0.08) 0 8px, transparent 8px 100%),
                    radial-gradient(circle at 80% 40%, rgba(255,255,255,0.06) 0 10px, transparent 10px 100%),
                    radial-gradient(circle at 40% 80%, rgba(255,255,255,0.05) 0 12px, transparent 12px 100%);
        pointer-events: none; mix-blend-mode: screen; opacity: 0.6;
    }
    /* Gradient title text */
    .hero h1 {
        background: linear-gradient(90deg, var(--accent), var(--accent-2));
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    .subtle { color: rgba(255,255,255,0.75); }
    .footer { margin-top: 2rem; opacity: 0.8; font-size: 0.9rem; }
    .metric-card {
        padding: 0.8rem 1rem; border-radius: 12px;
        background: linear-gradient(180deg, var(--bg-card), transparent);
        border: 1px solid var(--border-subtle); text-align: center;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
        position: relative; overflow: hidden;
        border-image: linear-gradient(135deg, var(--accent), var(--accent-2)) 1;
    }
    .metric-card:hover { transform: translateY(-2px); transition: 160ms ease; }
    /* colorful variants for cards */
    .metric-style { background: linear-gradient(135deg, rgba(46,125,50,0.28), rgba(255,255,255,0.02)); }
    .metric-creativity { background: linear-gradient(135deg, rgba(129,199,132,0.28), rgba(255,255,255,0.02)); }
    .metric-pages { background: linear-gradient(135deg, rgba(102,187,106,0.28), rgba(255,255,255,0.02)); }
    .metric-engine { background: linear-gradient(135deg, rgba(255,105,180,0.28), rgba(255,255,255,0.02)); }
    .metric-card::after {
        content: ""; position: absolute; inset: 0; pointer-events: none;
        background: linear-gradient(90deg, rgba(46,125,50,0.12), rgba(255,105,180,0.12));
        opacity: 0.6;
    }
    /* Gradient button for downloads */
    .stDownloadButton > button {
        background: linear-gradient(90deg, var(--accent), var(--accent-2)) !important;
        color: white !important; border: none !important;
        box-shadow: 0 6px 18px rgba(0,0,0,0.2);
    }
    .stDownloadButton > button:hover { filter: brightness(1.05); }
    .badge { display: inline-block; padding: 4px 10px; border-radius: 999px; border: 1px solid var(--border-subtle); background: var(--bg-card); font-size: .85rem; }
    .card { background: linear-gradient(180deg, var(--bg-card), transparent); border: 1px solid var(--border-subtle); border-radius: 14px; padding: 1rem 1.25rem; box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
    /* Center main container and tune readable width */
    .block-container { max-width: 1800px; }
    /* Summary alignment */
    .summary-section { max-width: none; width: 100%; margin: 0 auto; padding: 0 32px; }
    .summary-section .summary-text { text-align: justify; line-height: 1.8; font-size: 1.05rem; hyphens: auto; word-break: normal; overflow-wrap: anywhere; }
    .summary-section h4 { text-align: center; margin-bottom: 0.75rem; }
    /* Print-friendly overrides (enabled dynamically) */
    .print-friendly .summary-section .summary-text { font-size: 1.18rem; line-height: 1.95; }
    .print-friendly .metric-card { background: transparent; box-shadow: none; }
    .print-friendly .hero { box-shadow: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Hide Streamlit default chrome (header/menu/footer)
st.markdown(
    """
    <style>
    header[data-testid="stHeader"] { display: none; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Header ----------
st.markdown(
    """
    <div class="summary-section">
      <div class="hero">
        <h1 style="margin-bottom:0.25rem;"> Document Summarizer</h1>
        <p class="subtle" style="margin:0;">Plants & Flowers theme • Choose <b>Technical</b> or <b>Story</b> and see the balance of styles.</p>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Sidebar Controls ----------
with st.sidebar:
    st.header("Controls")
    uploaded = st.file_uploader("Upload a document", type=["txt", "pdf"])
    style_choice = st.radio("Style", ("Technical", "Story", "Balanced", "Custom"), horizontal=True)
    if style_choice == "Custom":
        target_technical_pct = st.slider("Technical Content (%)", 0, 100, 50, help="Target percentage of technical vs. story content.")
    else:
        target_technical_pct = {"Technical": 100, "Story": 0, "Balanced": 50}[style_choice]
    # Use a fixed default model per request: llama-3.1-70b-versatile
    model = "llama-3.1-70b-versatile"
    pages = st.slider("Summary length (pages)", 1, 20, 1, help="Approximate length to target.")
    chart_style = st.selectbox("Chart style", ("Bars", "Stacked 100%"), index=0)
    print_view = st.toggle("Print-friendly view", value=False, help="Larger fonts and clean layout for printing/export.")

    st.markdown("---")
    st.caption("Tips")
    st.markdown("- Try a research PDF for Technical\n- Try a short story for Story")

    st.markdown("---")
    st.caption("Session")
    st.write("Using: **" + ("Groq" if GROQ_API_KEY else "Local") + "**")

def read_text_from_file(uploaded_file):
    if uploaded_file.type == "text/plain":
        return StringIO(uploaded_file.getvalue().decode("utf-8")).read()
    elif uploaded_file.type == "application/pdf":
        # read pdf
        reader = PyPDF2.PdfReader(uploaded_file)
        text_pages = []
        for p in reader.pages:
            try:
                text_pages.append(p.extract_text() or "")
            except Exception:
                pass
        return "\n".join(text_pages)
    else:
        return ""

# ---------- Paging Helpers ----------
def _split_summary_into_pages(text: str, pages: int) -> list[str]:
    """Split summary text into roughly equal page chunks by sentences.
    Fallbacks to character-based splitting if needed.
    """
    import re
    text = (text or "").strip()
    if not text:
        return [""]
    pages = max(1, int(pages))
    # Sentence split
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if len(sentences) < pages:
        # Fallback: character-based slicing
        n = len(text)
        step = max(1, n // pages)
        chunks = [text[i:i+step] for i in range(0, n, step)]
        # Ensure exact number of pages by merging tail
        if len(chunks) > pages:
            merged = chunks[:pages-1]
            merged.append("".join(chunks[pages-1:]))
            return merged
        return chunks
    # Distribute sentences into pages as evenly as possible
    per_page = max(1, len(sentences) // pages)
    chunks: list[str] = []
    i = 0
    for p in range(pages-1):
        chunk = " ".join(sentences[i:i+per_page]).strip()
        chunks.append(chunk)
        i += per_page
    chunks.append(" ".join(sentences[i:]).strip())
    return chunks

tabs = st.tabs(["Workspace", "About"])  # main layout

with tabs[0]:
    st.markdown("### Workspace")
    if uploaded:
        raw_text = read_text_from_file(uploaded)
        if not raw_text.strip():
            st.error("Could not extract text from the uploaded file.")
        else:
            # Center the working area to the same width and run immediately
            st.markdown("<div class='summary-section'>", unsafe_allow_html=True)
            with st.spinner("Generating summary (summarize → classify)..."):
                # Derive token budget purely from pages (~700 tokens per page)
                derived_tokens = int(pages) * 700
                # Use a fixed creativity/temperature of 1.0 (100%) internally
                result = run_workflow(raw_text, target_technical_pct, 1.0, derived_tokens, pages, model)

            if result.get("error"):
                st.error(result["error"])
                st.stop()
            summary = result.get("summary", "")
            technical_pct = result.get("technical_pct")
            story_pct = result.get("story_pct")

            st.markdown("---")
            # Center the metrics row within the same width as summary (no Creativity/Max Tokens metrics)
            with st.container():
                st.markdown("<div class='card'><h4>Metrics</h4></div>", unsafe_allow_html=True)
                top_cols = st.columns(3)
                with top_cols[0]:
                    st.markdown("**Style**")
                    st.markdown(f"<div class='metric-card metric-style'>{style_choice if style_choice != 'Custom' else f'{target_technical_pct}% Tech'}</div>", unsafe_allow_html=True)
                with top_cols[1]:
                    st.markdown("**Pages**")
                    st.markdown(f"<div class='metric-card metric-pages'>{pages}</div>", unsafe_allow_html=True)
                with top_cols[2]:
                    st.markdown("**Model**")
                    st.markdown(f"<div class='metric-card metric-engine'>{model}</div>", unsafe_allow_html=True)

            if summary:
                # Split into pages and allow viewing page-wise
                chunks = _split_summary_into_pages(summary, pages)
                total_pages = len(chunks)
                # Initialize page index in session state
                if "page_idx" not in st.session_state:
                    st.session_state.page_idx = 1
                # Navigation buttons
                nav_l, nav_r, dl_col = st.columns([1, 1, 2])
                with nav_l:
                    back = st.button("← Back", use_container_width=True, disabled=st.session_state.page_idx <= 1)
                with nav_r:
                    nxt = st.button("Next →", use_container_width=True, disabled=st.session_state.page_idx >= total_pages)
                with dl_col:
                    from io import BytesIO
                    full_buf = BytesIO((summary or "").encode('utf-8'))
                    st.download_button("Download full (.txt)", data=full_buf, file_name="summary_full.txt", mime="text/plain")

                # Update current page based on clicks
                if back and st.session_state.page_idx > 1:
                    st.session_state.page_idx -= 1
                if nxt and st.session_state.page_idx < total_pages:
                    st.session_state.page_idx += 1
                page_idx = st.session_state.page_idx

                # Render the selected page
                current_text = chunks[page_idx - 1]
                st.markdown("<div class='summary-section'><div class='card'>", unsafe_allow_html=True)
                st.markdown(f"<h4>Summary • Page {page_idx} of {total_pages}</h4>", unsafe_allow_html=True)
                st.markdown(
                    f"<div class='summary-text'>{html.escape(current_text).replace('\\n','<br/>')}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown("</div></div>", unsafe_allow_html=True)

            if summary:
                st.markdown("<div class='summary-section'><div class='card'><h4>Technical vs Story (%)</h4>", unsafe_allow_html=True)
                # Use user's target mix: Story is complement of Technical
                t_val = int(target_technical_pct)
                s_val = max(0, 100 - t_val)
                colors = ['#2e7d32', '#ff69b4']  # Leaf green, Floral pink

                chart_cols = st.columns([1, 2, 1])
                with chart_cols[1]:
                    if chart_style == "Bars":
                        # Horizontal bar chart
                        fig, ax = plt.subplots(figsize=(7, 3))
                        categories = ["Technical", "Story"]
                        values = [t_val, s_val]
                        ax.barh(categories, values, color=colors)
                        ax.set_xlim(0, 100)
                        for i, v in enumerate(values):
                            ax.text(v + 1 if v < 95 else v - 5, i, f"{v}%", va='center', ha='left' if v < 95 else 'right', color='#ffffff' if v > 85 else None, weight='bold' if v > 85 else None)
                        ax.invert_yaxis()
                        ax.set_xlabel("Percentage")
                        ax.set_ylabel("")
                        ax.grid(axis='x', linestyle='--', alpha=0.3)
                        st.pyplot(fig)
                    else:
                        # Pie / donut chart
                        sizes = [t_val, s_val]
                        labels = [f'Technical ({t_val}%)', f'Story ({s_val}%)']
                        fig, ax = plt.subplots(figsize=(6, 6))
                        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors, wedgeprops=dict(width=0.4, edgecolor='w'))
                        ax.axis('equal')
                        st.pyplot(fig)

                st.info("Chart reflects your selected target mix. Measured results may differ slightly.")
                st.markdown("</div></div>", unsafe_allow_html=True)

            # Close centered working area
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Upload a TXT/PDF from the left sidebar to get started.")

with tabs[1]:
    st.markdown("### About")
    st.write(
        "This app uses a LangGraph pipeline to summarize your document in a chosen style, then estimates how much of the output reads like technical writing vs a story."
    )
    st.caption("Built with Streamlit, LangGraph, and LangChain")

# ---------- Footer ----------
st.markdown(
    """
    <div class="footer">
      <hr/>
      <span>💡 Tip: For best results with Groq, set <code>GROQ_API_KEY</code> before launching.</span>
    </div>
    """,
    unsafe_allow_html=True,
)
