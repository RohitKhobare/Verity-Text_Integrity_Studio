"""
app.py - Plagiarism Detector using the Rabin-Karp rolling hash.
Run with: streamlit run app.py
"""
import os

import pandas as pd
import streamlit as st

import plagiarism_core as pc

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
MODULI = {
    "Large prime 2^61-1 (recommended)": pc.MOD,
    "1,000,003": 1_000_003,
    "10,007": 10_007,
    "101 (demonstration)": 101,
}

st.set_page_config(
    page_title="Verity | Text Integrity Studio",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False

THEMES = {
    "light": {
        "bg": "#f4f7fb",
        "surface": "#ffffff",
        "surface_alt": "#edf3f8",
        "ink": "#142b3b",
        "muted": "#627789",
        "line": "#dce6ee",
        "accent": "#087e8b",
        "accent_hover": "#066570",
        "accent_soft": "#e4f4f3",
        "hero_start": "#ffffff",
        "hero_end": "#e7f4f4",
        "shadow": "0 16px 42px rgba(22, 53, 74, .07)",
        "mark_bg": "#fff0b8",
        "mark_ink": "#634711",
    },
    "dark": {
        "bg": "#101923",
        "surface": "#182430",
        "surface_alt": "#202f3d",
        "ink": "#e8f0f5",
        "muted": "#a3b4c1",
        "line": "#314453",
        "accent": "#55c8c0",
        "accent_hover": "#7cddd5",
        "accent_soft": "#203b40",
        "hero_start": "#1a2934",
        "hero_end": "#1d3a40",
        "shadow": "0 18px 48px rgba(0, 0, 0, .22)",
        "mark_bg": "#65501f",
        "mark_ink": "#fff1bd",
    },
}
theme = THEMES["dark" if st.session_state["dark_mode"] else "light"]

st.markdown(
    f"""
    <style>
    :root {{
        color-scheme: {"dark" if st.session_state["dark_mode"] else "light"};
        --app-bg: {theme["bg"]};
        --surface: {theme["surface"]};
        --surface-alt: {theme["surface_alt"]};
        --ink: {theme["ink"]};
        --muted: {theme["muted"]};
        --line: {theme["line"]};
        --accent: {theme["accent"]};
        --accent-hover: {theme["accent_hover"]};
        --accent-soft: {theme["accent_soft"]};
        --hero-start: {theme["hero_start"]};
        --hero-end: {theme["hero_end"]};
        --shadow: {theme["shadow"]};
        --mark-bg: {theme["mark_bg"]};
        --mark-ink: {theme["mark_ink"]};
    }}
    .stApp, [data-testid="stAppViewContainer"] {{ background: var(--app-bg); color: var(--ink); }}
    [data-testid="stHeader"] {{ background: var(--app-bg); }}
    .block-container {{ max-width: 1500px; padding: 1.5rem 2.8rem 3.5rem; font-family: Inter, "Segoe UI", ui-sans-serif, system-ui, sans-serif; }}
    [data-testid="stSidebar"] {{ background: var(--surface); border-right: 1px solid var(--line); }}
    [data-testid="stSidebar"] > div:first-child {{ padding: 1.25rem 1rem 2rem; }}
    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {{ color: var(--ink); }}
    [data-testid="stCaptionContainer"], .stCaption {{ color: var(--muted); }}
    .brand-row {{ display:flex; align-items:center; gap:.7rem; margin:.2rem 0 1.3rem; }}
    .brand-symbol {{
        width:2.55rem; height:2.55rem; display:grid; place-items:center;
        border-radius:12px; color:#fff; font-size:1.55rem; font-weight:800;
        background:linear-gradient(145deg, var(--accent), #5269bd);
        box-shadow:0 7px 18px color-mix(in srgb, var(--accent) 25%, transparent);
    }}
    .brand-name {{ color:var(--ink); font-size:1.02rem; font-weight:800; letter-spacing:-.03em; }}
    .brand-sub {{ color:var(--muted); font-size:.68rem; letter-spacing:.12em; text-transform:uppercase; }}
    .hero {{
        position:relative; overflow:hidden; display:flex; justify-content:space-between; gap:2rem;
        margin:.35rem 0 1.3rem; padding:2rem 2.15rem; border:1px solid var(--line);
        border-radius:22px; background:linear-gradient(115deg,var(--hero-start),var(--hero-end));
        box-shadow:var(--shadow);
    }}
    .hero:after {{
        content:""; position:absolute; width:270px; height:270px; right:6%; top:-65%;
        border:1px solid color-mix(in srgb,var(--accent) 28%,transparent);
        border-radius:50%; box-shadow:0 0 0 28px color-mix(in srgb,var(--accent) 5%,transparent),
        0 0 0 58px color-mix(in srgb,var(--accent) 4%,transparent); pointer-events:none;
    }}
    .hero-copy {{ position:relative; z-index:1; max-width:790px; }}
    .eyebrow {{ color:var(--accent); font-size:.72rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; }}
    .hero h1 {{ margin:.45rem 0 .65rem; color:var(--ink); font-size:clamp(2rem,4vw,3.2rem); line-height:1.05; letter-spacing:-.055em; }}
    .hero p {{ max-width:760px; margin:0; color:var(--muted); font-size:1rem; line-height:1.7; }}
    .hero-aside {{
        z-index:1; align-self:center; min-width:185px; padding:1.05rem 1.15rem;
        border:1px solid var(--line); border-radius:15px; background:var(--surface);
    }}
    .hero-aside b {{ display:block; margin-bottom:.3rem; color:var(--ink); font-size:.83rem; }}
    .hero-aside span {{ color:var(--muted); font-size:.77rem; line-height:1.5; }}
    .section-label {{ margin:0 0 .25rem; color:var(--accent); font-size:.7rem; font-weight:800; letter-spacing:.13em; text-transform:uppercase; }}
    .compare-intro {{ display:flex; align-items:flex-start; justify-content:space-between; gap:1.5rem; margin:.6rem 0 1.1rem; }}
    .compare-intro h2 {{ margin:.2rem 0 .35rem; color:var(--ink); font-size:1.8rem; letter-spacing:-.04em; }}
    .compare-intro p {{ margin:0; color:var(--muted); line-height:1.6; }}
    .workflow-steps {{ display:flex; align-items:center; gap:.45rem; flex-wrap:wrap; }}
    .workflow-step {{ padding:.46rem .72rem; border:1px solid var(--line); border-radius:999px; background:var(--surface); color:var(--muted); font-size:.73rem; font-weight:700; }}
    .workflow-step.active {{ border-color:color-mix(in srgb,var(--accent) 32%,var(--line)); background:var(--accent-soft); color:var(--accent); }}
    [data-testid="stVerticalBlockBorderWrapper"] {{
        border:1px solid var(--line); border-radius:19px;
        background:var(--surface); box-shadow:var(--shadow);
        transition:border-color .18s ease, transform .18s ease, box-shadow .18s ease;
    }}
    [data-testid="stVerticalBlockBorderWrapper"]:hover {{
        border-color:color-mix(in srgb,var(--accent) 48%,var(--line));
        box-shadow:0 18px 42px color-mix(in srgb,var(--accent) 9%,transparent);
    }}
    .document-heading {{ display:flex; align-items:center; gap:.75rem; margin-bottom:.8rem; }}
    .document-icon {{ display:grid; place-items:center; width:2.55rem; height:2.55rem; border-radius:13px; background:var(--accent-soft); color:var(--accent); font-size:1.18rem; }}
    .document-heading strong {{ display:block; color:var(--ink); font-size:1rem; }}
    .document-heading span {{ display:block; margin-top:.16rem; color:var(--muted); font-size:.75rem; }}
    .document-state {{ display:flex; align-items:center; gap:.45rem; margin-top:.65rem; padding:.56rem .7rem; border-radius:9px; background:var(--surface-alt); color:var(--muted); font-size:.75rem; }}
    .document-state.ready {{ background:var(--accent-soft); color:var(--accent); }}
    .source-hint {{ margin:.1rem 0 .45rem; color:var(--muted); font-size:.76rem; }}
    .versus-badge {{ display:grid; place-items:center; width:2.65rem; height:2.65rem; margin:1.2rem auto 0; border:1px solid var(--line); border-radius:50%; background:var(--surface); color:var(--accent); font-size:.7rem; font-weight:850; box-shadow:var(--shadow); }}
    .compare-action {{ margin-top:1rem; padding:1rem 1.1rem; border:1px solid var(--line); border-radius:15px; background:var(--surface-alt); }}
    .input-card {{
        min-height:100px; margin:.35rem 0 .85rem; padding:1rem 1.1rem;
        border:1px solid var(--line); border-radius:15px; background:var(--surface); box-shadow:var(--shadow);
    }}
    .input-card strong {{ display:block; margin-bottom:.35rem; color:var(--ink); font-size:1rem; }}
    .input-card span {{ color:var(--muted); font-size:.88rem; line-height:1.5; }}
    .stTabs [data-baseweb="tab-list"] {{
        gap:.5rem; padding:.45rem; border:1px solid var(--line);
        border-radius:14px; background:var(--surface); box-shadow:var(--shadow);
    }}
    .stTabs [data-baseweb="tab"] {{
        height:2.85rem; padding:0 1.1rem; border-radius:10px;
        color:var(--muted); font-weight:700; transition:all .18s ease;
    }}
    .stTabs [data-baseweb="tab"]:hover {{ color:var(--accent); background:var(--accent-soft); }}
    .stTabs [aria-selected="true"] {{ color:#fff !important; background:var(--accent) !important; }}
    [data-testid="stMetric"] {{
        padding:1rem 1.05rem; border:1px solid var(--line);
        border-radius:15px; background:var(--surface); box-shadow:var(--shadow);
    }}
    [data-testid="stMetricLabel"] {{ color:var(--muted); }}
    [data-testid="stMetricValue"] {{ color:var(--ink); }}
    .stButton > button {{
        min-height:2.65rem; padding:0 1.05rem; border:1px solid var(--line);
        border-radius:11px; background:var(--surface); color:var(--ink); font-weight:700;
        transition:transform .16s ease, box-shadow .16s ease, border-color .16s ease;
    }}
    .stButton > button:hover {{
        transform:translateY(-1px); border-color:var(--accent);
        color:var(--accent); box-shadow:0 7px 18px color-mix(in srgb,var(--accent) 14%,transparent);
    }}
    .stButton > button[kind="primary"] {{
        min-height:3rem; padding:0 1.4rem; border:0; border-radius:11px;
        background:linear-gradient(120deg,var(--accent),#5269bd); color:#fff;
        font-weight:800; box-shadow:0 7px 18px color-mix(in srgb,var(--accent) 22%,transparent);
    }}
    .stButton > button[kind="primary"]:hover {{ color:#fff; filter:brightness(1.08); }}
    [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input, [data-testid="stSelectbox"] [data-baseweb="select"] > div {{
        background:var(--surface); color:var(--ink); border-color:var(--line); border-radius:10px;
    }}
    [data-testid="stFileUploader"] section {{ border-color:var(--line); border-radius:13px; background:var(--surface); }}
    [data-testid="stDataFrame"], [data-testid="stTable"] {{ border:1px solid var(--line); border-radius:12px; overflow:hidden; }}
    div[data-testid="stExpander"] {{ border-color:var(--line); border-radius:12px; background:var(--surface); }}
    .footnote {{ color:var(--muted); font-size:.84rem; line-height:1.6; }}
    mark {{ padding:.08rem .16rem; border-radius:4px; background:{theme["mark_bg"]}; color:{theme["mark_ink"]}; }}
    .soft-rule {{ height:1px; margin:1.25rem 0; background:var(--line); }}
    @media (max-width:850px) {{
        .hero {{ padding:1.4rem; }} .hero-aside {{ display:none; }}
        .block-container {{ padding:1rem 1rem 2.2rem; }}
        .stTabs [data-baseweb="tab"] {{ padding:0 .65rem; font-size:.78rem; }}
        .compare-intro {{ display:block; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def sample_files():
    if not os.path.isdir(SAMPLES_DIR):
        return []
    return sorted(name for name in os.listdir(SAMPLES_DIR) if name.lower().endswith(".txt"))


def read_sample(name):
    with open(os.path.join(SAMPLES_DIR, name), encoding="utf-8") as file:
        return file.read()


def read_upload(uploaded_file):
    if uploaded_file.name.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader
        except ImportError:
            st.error("PDF support is unavailable. Install the project dependencies with `pip install -r requirements.txt`.")
            return ""
        return "\n".join(page.extract_text() or "" for page in PdfReader(uploaded_file).pages)
    return uploaded_file.getvalue().decode("utf-8", errors="replace")


def document_input(label, key, default_index):
    samples = sample_files()
    document_number = "01" if key == "a" else "02"
    icon = "▤" if key == "a" else "▧"
    with st.container(border=True):
        st.markdown(
            f'<div class="document-heading"><div class="document-icon">{icon}</div>'
            f'<div><strong>{label}</strong>'
            f'<span>DOCUMENT {document_number} · SOURCE TEXT</span></div></div>',
            unsafe_allow_html=True,
        )
        mode = st.selectbox(
            f"Choose a source for {label}",
            ["Sample library", "Paste text", "Upload file"],
            key=f"{key}_mode",
            format_func=lambda value: {
                "Sample library": "▤  Sample library",
                "Paste text": "✎  Paste or write text",
                "Upload file": "↑  Upload a document",
            }[value],
            label_visibility="collapsed",
        )
        if mode == "Sample library":
            if not samples:
                st.info("No sample text files are available in the samples folder.")
                return label, ""
            name = st.selectbox(
                f"{label} sample",
                samples,
                key=f"{key}_sample",
                index=min(default_index, len(samples) - 1),
            )
            text = read_sample(name)
        elif mode == "Upload file":
            uploaded_file = st.file_uploader(
                f"Choose a .txt or .pdf file for {label}",
                type=["txt", "pdf"],
                key=f"{key}_file",
                help="PDF files are analyzed using selectable text; scanned image-only PDFs may have no extractable text.",
            )
            if uploaded_file is None:
                st.caption("Drop a file here or browse · .txt and text-based .pdf")
                st.markdown(
                    '<div class="document-state"><span>↑</span><span>Ready for a local file</span></div>',
                    unsafe_allow_html=True,
                )
                return label, ""
            name, text = uploaded_file.name, read_upload(uploaded_file)
        else:
            name = label
            text = st.text_area(
                f"{label} content",
                height=245,
                key=f"{key}_text",
                placeholder="Paste or type your document here...\n\nYour text stays in this local comparison session.",
                help="The analyzer ignores capitalization, spacing, and punctuation when finding matches.",
            )

        normalized, _ = pc.normalize(text)
        word_count = len(text.split())
        state_class = "ready" if normalized else ""
        state_icon = "●" if normalized else "○"
        state_label = (
            f"{word_count:,} words · {len(normalized):,} matchable characters"
            if normalized else "Waiting for document text"
        )
        st.markdown(
            f'<div class="document-state {state_class}"><span>{state_icon}</span>'
            f'<span>{state_label}</span></div>',
            unsafe_allow_html=True,
        )
        st.caption(name)
    return name, text


def show_verdict(score, verdict):
    if score >= 60:
        st.error(verdict)
    elif score >= 30:
        st.warning(verdict)
    else:
        st.success(verdict)


def current_comparison(name_a, name_b, text_a, text_b, k, d, q):
    if "comparison_result" not in st.session_state:
        return None
    saved = st.session_state["comparison_result"]
    signature = (name_a, name_b, text_a, text_b, k, int(d), q)
    if saved["signature"] != signature:
        st.info("The documents or matching settings have changed. Run the comparison again to refresh these results.")
        return None
    return saved["analysis"]


with st.sidebar:
    st.markdown(
        '<div class="brand-row"><div class="brand-symbol">V</div><div>'
        '<div class="brand-name">VERITY</div><div class="brand-sub">Text integrity studio</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )
    st.toggle("Dark appearance", key="dark_mode", help="Switch the complete workspace between light and dark palettes.")
    st.markdown('<div class="soft-rule"></div>', unsafe_allow_html=True)
    st.markdown('<p class="section-label">Matching controls</p>', unsafe_allow_html=True)
    st.subheader("Analysis settings")
    st.caption("Tune what counts as a matching passage.")
    k = st.slider(
        "Minimum match length",
        min_value=8,
        max_value=80,
        value=20,
        help="A smaller value catches shorter overlaps but may include common phrases. A larger value is more selective.",
    )
    st.caption(f"At least **{k} normalized characters** must match consecutively.")
    with st.expander("Advanced hash settings"):
        d = st.number_input("Hash base (d)", min_value=2, value=pc.BASE, step=1)
        q_label = st.selectbox("Hash modulus (q)", list(MODULI))
        q = MODULI[q_label]
        st.caption("Hash matches are always verified against the actual text.")
    st.divider()
    st.markdown("**What the score means**")
    st.markdown(
        '<p class="footnote">Similarity is the larger of the two directional coverage scores. '
        'It is a text-overlap measure, not a probability or a final finding of misconduct.</p>',
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <section class="hero">
      <div class="hero-copy">
      <div class="eyebrow">◈ &nbsp; TEXT INTEGRITY · DOCUMENT REVIEW</div>
      <h1>See what matches.<br>Understand what it means.</h1>
      <p>Compare documents, inspect verified passages, and understand how each score was calculated.
      The detector checks normalized exact text matches in the documents you provide; it does not check
      paraphrasing or online sources.</p>
      </div>
      <div class="hero-aside"><b>Designed for careful review</b>
      <span>Exact-match screening<br>Directional coverage scores<br>Context-first highlights</span></div>
    </section>
    """,
    unsafe_allow_html=True,
)

compare_tab, batch_tab, benchmark_tab, guide_tab = st.tabs(
    ["◉  Compare", "▦  Batch review", "⌁  Benchmark", "ⓘ  Method guide"]
)

with compare_tab:
    st.markdown(
        '<div class="compare-intro"><div><p class="section-label">Side-by-side workspace</p>'
        '<h2>Build your comparison</h2>'
        '<p>Choose a source for each side. The review checks exact text overlap and keeps the original context visible.</p>'
        '</div><div class="workflow-steps">'
        '<span class="workflow-step active">01&nbsp; Add documents</span>'
        '<span class="workflow-step">02&nbsp; Tune match length</span>'
        '<span class="workflow-step">03&nbsp; Review matches</span>'
        '</div></div>',
        unsafe_allow_html=True,
    )
    left, right = st.columns(2, gap="large")
    with left:
        name_a, text_a = document_input("Document A", "a", 1)
    with right:
        name_b, text_b = document_input("Document B", "b", 0)

    normalized_a, _ = pc.normalize(text_a)
    normalized_b, _ = pc.normalize(text_b)
    ready_count = int(bool(normalized_a)) + int(bool(normalized_b))
    st.markdown(
        f'<div class="document-state {"ready" if ready_count == 2 else ""}>'
        f'<span>{"●" if ready_count == 2 else "◌"}</span>'
        f'<span>{ready_count} of 2 documents ready · minimum passage length: {k} characters</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="compare-action"><p class="source-hint">'
        'The analyzer normalizes case, spaces, and punctuation. Every hash match is verified against the actual text.'
        '</p></div>',
        unsafe_allow_html=True,
    )
    if st.button("✦  Analyze text overlap", type="primary", key="analyze_two"):
        if not text_a.strip() or not text_b.strip():
            st.warning("Choose or add readable content for both document cards to start the review.")
            st.session_state.pop("comparison_result", None)
        else:
            with st.spinner("Finding and verifying matching passages..."):
                analysis = pc.analyze(text_a, text_b, k, int(d), q)
                st.session_state["comparison_result"] = {
                    "signature": (name_a, name_b, text_a, text_b, k, int(d), q),
                    "analysis": analysis,
                }

    analysis = current_comparison(name_a, name_b, text_a, text_b, k, d, q)
    if analysis is not None:
        st.divider()
        if analysis["too_short"]:
            st.warning(analysis["verdict"])
            st.caption("Increase the document length or reduce the minimum match length in the settings.")
        else:
            st.subheader("Similarity review")
            show_verdict(analysis["score"], analysis["verdict"])
            st.caption(
                "This is a screening result based on exact normalized text overlap. "
                "Review the highlighted context before drawing conclusions."
            )
            metric_a, metric_b, metric_score, metric_passages = st.columns(4)
            metric_a.metric("A covered by B", f"{analysis['coverage_a']:.1f}%")
            metric_b.metric("B covered by A", f"{analysis['coverage_b']:.1f}%")
            metric_score.metric("Overall similarity", f"{analysis['score']:.1f}%")
            metric_passages.metric("Matched passages", len(analysis["blocks"]))

            with st.expander("How to read these scores", expanded=True):
                st.markdown(
                    f"- **A covered by B ({analysis['coverage_a']:.1f}%)**: the share of Document A's "
                    "normalized text found in Document B.\n"
                    f"- **B covered by A ({analysis['coverage_b']:.1f}%)**: the reverse direction.\n"
                    f"- **Overall similarity ({analysis['score']:.1f}%)**: the higher directional coverage, "
                    "so a shorter document copied into a longer one remains visible."
                )
                st.caption("These percentages are not probabilities, authorship claims, or proof of plagiarism.")

            st.markdown("#### Highlighted documents")
            st.caption("Highlighted text belongs to a verified exact match after normalization.")
            highlighted_a, highlighted_b = st.columns(2, gap="large")
            with highlighted_a:
                st.markdown("**Document A**")
                st.caption(name_a)
                st.markdown(pc.highlight(text_a, analysis["spans_a"]), unsafe_allow_html=True)
            with highlighted_b:
                st.markdown("**Document B**")
                st.caption(name_b)
                st.markdown(pc.highlight(text_b, analysis["spans_b"]), unsafe_allow_html=True)

            if analysis["blocks"]:
                st.markdown("#### Matched passages")
                passage_rows = [
                    {
                        "Match length": f"{passage['chars']:,} chars",
                        f"{name_a} · position": f"{passage['span_a'][0]}–{passage['span_a'][1]}",
                        f"{name_b} · position": f"{passage['span_b'][0]}–{passage['span_b'][1]}",
                        "Verified text": passage["text_a"][:300]
                        + ("…" if len(passage["text_a"]) > 300 else ""),
                    }
                    for passage in analysis["blocks"]
                ]
                st.dataframe(pd.DataFrame(passage_rows), hide_index=True, width="stretch")
                st.caption("Positions are zero-based character offsets; the end offset is exclusive.")
                st.download_button(
                    "Download matched passages (CSV)",
                    data=pd.DataFrame(passage_rows).to_csv(index=False),
                    file_name="matched_passages.csv",
                    mime="text/csv",
                    key="download_passages",
                )
            else:
                st.info(f"No passages of {k} or more normalized characters were found.")

            with st.expander("Technical details"):
                stats = analysis["stats"]
                stat_a, stat_b, stat_c = st.columns(3)
                stat_a.metric("K-grams hashed", f"{stats['kgrams_hashed']:,}")
                stat_b.metric("Hash lookups", f"{stats['hash_lookups']:,}")
                stat_c.metric("Verified hash hits", f"{stats['hash_hits']:,}")
                st.caption(
                    f"Character comparisons: {stats['char_comparisons']:,} · "
                    f"Spurious hash hits rejected: {stats['spurious_hits']:,} · "
                    f"Analysis time: {stats['time_ms']:.2f} ms"
                )
                if stats["spurious_hits"]:
                    st.info("Some matching hashes were not matching text. Character-by-character verification rejected them.")

with batch_tab:
    st.subheader("Compare a collection")
    st.caption("Run every unique document pair, then review the ranked results and similarity matrix.")
    use_samples = st.checkbox("Include all sample documents", value=True, key="batch_samples")
    uploaded_files = st.file_uploader(
        "Add .txt or .pdf documents",
        type=["txt", "pdf"],
        accept_multiple_files=True,
        key="batch_uploads",
        help="Text-based PDFs are supported. Scanned image-only PDFs may not contain extractable text.",
    )
    documents = {}
    if use_samples:
        documents.update({name: read_sample(name) for name in sample_files()})
    for uploaded_file in uploaded_files or []:
        base_name = uploaded_file.name
        name = base_name
        suffix = 2
        while name in documents:
            stem, extension = os.path.splitext(base_name)
            name = f"{stem} ({suffix}){extension}"
            suffix += 1
        documents[name] = read_upload(uploaded_file)
    valid_count = sum(bool(text.strip()) for text in documents.values())
    st.caption(f"{len(documents)} document(s) added · {valid_count} with readable text")

    if st.button("Compare all pairs", type="primary", key="analyze_many"):
        readable_documents = {name: text for name, text in documents.items() if text.strip()}
        if len(readable_documents) < 2:
            st.warning("Add at least two documents with readable text.")
            st.session_state.pop("batch_result", None)
        else:
            rows = pc.compare_many(readable_documents, k, int(d), q)
            dataframe = pd.DataFrame(rows).sort_values("Similarity %", ascending=False)
            names = list(readable_documents)
            matrix = pd.DataFrame(100.0, index=names, columns=names)
            for row in rows:
                matrix.loc[row["Document 1"], row["Document 2"]] = row["Similarity %"]
                matrix.loc[row["Document 2"], row["Document 1"]] = row["Similarity %"]
            st.session_state["batch_result"] = {
                "signature": (readable_documents, k, int(d), q),
                "dataframe": dataframe,
                "matrix": matrix,
            }

    if "batch_result" in st.session_state:
        batch_result = st.session_state["batch_result"]
        readable_documents = {name: text for name, text in documents.items() if text.strip()}
        if batch_result["signature"] != (readable_documents, k, int(d), q):
            st.info("The collection or matching settings have changed. Compare all pairs again to refresh these results.")
        else:
            st.markdown("#### Pairwise results · highest similarity first")
            st.dataframe(batch_result["dataframe"], hide_index=True, width="stretch")
            st.download_button(
                "Download pairwise report (CSV)",
                data=batch_result["dataframe"].to_csv(index=False),
                file_name="plagiarism_report.csv",
                mime="text/csv",
                key="download_batch",
            )
            st.markdown("#### Similarity matrix")
            st.caption("Diagonal cells represent a document compared with itself.")
            st.dataframe(batch_result["matrix"].round(1), width="stretch")

with benchmark_tab:
    st.subheader("Benchmark the matching methods")
    st.caption("Compare the Rabin–Karp rolling-hash method with a straightforward character-by-character baseline.")
    st.markdown(
        '<div class="input-card"><strong>Controlled experiment</strong>'
        '<span>Both methods analyze generated text with a copied section planted in the second document. '
        'This measures algorithm performance; it does not evaluate real-world document authorship.</span></div>',
        unsafe_allow_html=True,
    )
    size_text = st.text_input(
        "Document lengths in characters (comma-separated)",
        "500, 1000, 2000, 3000",
        help="Keep each length at or below 8,000 characters; the naive method can take longer on large inputs.",
    )
    copy_ratio = st.slider("Approximate share copied into the second document", 0.05, 0.9, 0.3)
    if st.button("Run benchmark", type="primary", key="run_benchmark"):
        try:
            sizes = [int(value.strip()) for value in size_text.split(",") if value.strip()]
        except ValueError:
            st.error("Enter document lengths as comma-separated whole numbers.")
            sizes = []
        if sizes and (min(sizes) < k or max(sizes) > 8000):
            st.error(f"Every length must be at least the current match length ({k}) and no more than 8,000.")
            sizes = []
        if not sizes:
            st.warning("Enter one or more valid document lengths before running the benchmark.")
            st.session_state.pop("benchmark_result", None)
        else:
            with st.spinner("Running the benchmark…"):
                benchmark = pd.DataFrame(pc.run_benchmark(sizes, k, copy_ratio, int(d), q))
            st.session_state["benchmark_result"] = {
                "signature": (sizes, copy_ratio, k, int(d), q),
                "dataframe": benchmark,
            }

    if "benchmark_result" in st.session_state:
        benchmark_result = st.session_state["benchmark_result"]
        try:
            current_sizes = [int(value.strip()) for value in size_text.split(",") if value.strip()]
        except ValueError:
            current_sizes = []
        if benchmark_result["signature"] != (current_sizes, copy_ratio, k, int(d), q):
            st.info("Benchmark settings have changed. Run the benchmark again to refresh these results.")
        else:
            benchmark = benchmark_result["dataframe"]
            st.dataframe(benchmark, hide_index=True, width="stretch")
            agreement = all(
                group["Passages"].nunique() == 1 and group["Similarity %"].nunique() == 1
                for _, group in benchmark.groupby("Text length")
            )
            if agreement:
                st.success("Both methods found the same passages and similarity scores for every document size.")
            else:
                st.error("The methods returned different results. Review the parameters and benchmark output.")
            chart_time, chart_comparisons = st.columns(2)
            with chart_time:
                st.markdown("#### Runtime")
                st.line_chart(benchmark.pivot(index="Text length", columns="Method", values="Time (ms)"))
            with chart_comparisons:
                st.markdown("#### Character comparisons")
                st.line_chart(
                    benchmark.pivot(index="Text length", columns="Method", values="Char comparisons")
                )

with guide_tab:
    st.subheader("How the screening works")
    steps = [
        ("01", "Normalize", "Convert letters and digits to lowercase, ignoring spaces and punctuation while retaining original positions."),
        ("02", "Hash windows", "Compute rolling hashes for every overlapping k-character window in each document."),
        ("03", "Find candidates", "Index one document's hashes and look up matching windows from the other."),
        ("04", "Verify text", "Compare each candidate's actual characters. Hash collisions are rejected, not reported as matches."),
        ("05", "Group passages", "Merge consecutive verified windows and map their spans back to the original documents."),
        ("06", "Calculate coverage", "Measure matched normalized text in each direction and report the larger percentage as overall similarity."),
    ]
    for number, heading, detail in steps:
        with st.container():
            step_col, text_col = st.columns([1, 12])
            with step_col:
                st.markdown(f"**{number}**")
            with text_col:
                st.markdown(f"**{heading}**  \n{detail}")
    st.divider()
    st.markdown("#### Interpreting results responsibly")
    st.markdown(
        "- Similarity is a screening signal, not a probability, authorship determination, or automatic misconduct decision.\n"
        "- The detector finds exact passages after case, spacing, and punctuation are normalized. It does not detect paraphrasing, synonyms, or translations.\n"
        "- Common phrases can match by coincidence. Increase the minimum match length and review the surrounding context.\n"
        "- PDF analysis depends on extractable text; image-only scans need OCR, which this app does not provide.\n"
        "- No internet-source search is performed. Results compare only the documents provided to this app."
    )
