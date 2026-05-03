import streamlit as st

from agent import process_ticket
from classifier import infer_company_key
from config import DATA_DIR
from corpus_loader import load_corpus
from retriever import CorpusRetriever


st.set_page_config(
    page_title="Support Triage Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════════
#  GLOBAL CSS
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Outfit:wght@400;500;600;700;800&display=swap');

/* ── Tokens ── */
:root {
  --bg:          #07080b;
  --bg2:         #0d0f14;
  --surface:     #111520;
  --surface2:    #161b28;
  --border:      #1c2235;
  --border-hi:   #252d42;
  --cyan:        #00e5c3;
  --cyan-dim:    #00b89a;
  --cyan-glow:   rgba(0,229,195,.15);
  --amber:       #f0a500;
  --amber-dim:   rgba(240,165,0,.12);
  --red:         #ff4d6d;
  --green:       #00c896;
  --green-dim:   rgba(0,200,150,.1);
  --text:        #dde3f0;
  --text-dim:    #8892aa;
  --mono:        'DM Mono', monospace;
  --sans:        'Outfit', sans-serif;
  --radius:      12px;
  --radius-sm:   8px;
}

/* ── Base reset ── */
html, body, [class*="css"] {
  font-family: var(--sans) !important;
  background: var(--bg) !important;
  color: var(--text);
}
.stApp { background: var(--bg) !important; }
.block-container {
  padding: 2rem 2.5rem 3rem !important;
  max-width: 1380px !important;
}
#MainMenu, footer, header { visibility: hidden; }
* { box-sizing: border-box; }

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg2); }
::-webkit-scrollbar-thumb { background: var(--border-hi); border-radius: 4px; }

/* ══ INPUTS ══ */
.stTextInput > div > div > input,
.stTextArea  > div > div > textarea {
  background:    var(--surface) !important;
  border:        1px solid var(--border-hi) !important;
  border-radius: var(--radius-sm) !important;
  color:         var(--text) !important;
  font-family:   var(--mono) !important;
  font-size:     0.83rem !important;
  padding:       0.65rem 0.9rem !important;
  transition:    border-color .2s, box-shadow .2s;
  caret-color:   var(--cyan);
}
.stTextInput > div > div > input:focus,
.stTextArea  > div > div > textarea:focus {
  border-color: var(--cyan) !important;
  box-shadow:   0 0 0 3px rgba(0,229,195,.1) !important;
  outline:      none !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea  > div > div > textarea::placeholder {
  color:     var(--text-dim) !important;
  font-size: 0.8rem !important;
}
.stTextInput > label,
.stTextArea  > label,
.stSelectbox > label {
  font-family:    var(--mono) !important;
  font-size:      0.68rem !important;
  font-weight:    500 !important;
  text-transform: uppercase;
  letter-spacing: .1em;
  color:          var(--text-dim) !important;
  margin-bottom:  .3rem;
}

/* ══ SELECTBOX ══ */
.stSelectbox > div > div {
  background:    var(--surface) !important;
  border:        1px solid var(--border-hi) !important;
  border-radius: var(--radius-sm) !important;
  color:         var(--text) !important;
  font-family:   var(--mono) !important;
  font-size:     0.83rem !important;
}
.stSelectbox > div > div:focus-within {
  border-color: var(--cyan) !important;
  box-shadow:   0 0 0 3px rgba(0,229,195,.1) !important;
}

/* ══ BUTTONS ══ */
.stButton > button {
  font-family:    var(--mono) !important;
  font-size:      0.76rem !important;
  font-weight:    500 !important;
  letter-spacing: .08em !important;
  text-transform: uppercase;
  border-radius:  var(--radius-sm) !important;
  border:         1px solid var(--border-hi) !important;
  background:     var(--surface) !important;
  color:          var(--text-dim) !important;
  padding:        0.58rem 1.1rem !important;
  transition:     all .2s;
  width:          100%;
}
.stButton > button:hover {
  border-color: var(--cyan) !important;
  color:        var(--cyan) !important;
  background:   rgba(0,229,195,.06) !important;
}
.stButton > button[kind="primary"] {
  background:   var(--cyan) !important;
  color:        #000 !important;
  border-color: var(--cyan) !important;
  font-weight:  700 !important;
}
.stButton > button[kind="primary"]:hover {
  background:   var(--cyan-dim) !important;
  border-color: var(--cyan-dim) !important;
}

/* ══ TABS ══ */
.stTabs [data-baseweb="tab-list"] {
  background:    transparent !important;
  border-bottom: 1px solid var(--border) !important;
  gap:     0 !important;
  padding: 0 !important;
}
.stTabs [data-baseweb="tab"] {
  font-family:    var(--mono) !important;
  font-size:      0.75rem !important;
  text-transform: uppercase;
  letter-spacing: .1em;
  color:          var(--text-dim) !important;
  background:     transparent !important;
  border:         none !important;
  border-bottom:  2px solid transparent !important;
  padding:        .7rem 1.4rem !important;
  transition:     all .2s;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--text) !important; }
.stTabs [aria-selected="true"] {
  color:         var(--cyan) !important;
  border-bottom: 2px solid var(--cyan) !important;
}
.stTabs [data-baseweb="tab-panel"] { padding: 1.6rem 0 0 !important; }

/* ══ METRICS ══ */
[data-testid="stMetric"] {
  background:    var(--surface);
  border:        1px solid var(--border);
  border-radius: var(--radius);
  padding:       1rem 1.2rem;
}
[data-testid="stMetricLabel"] {
  font-family:    var(--mono) !important;
  font-size:      0.66rem !important;
  text-transform: uppercase;
  letter-spacing: .12em;
  color:          var(--text-dim) !important;
}
[data-testid="stMetricValue"] {
  font-family: var(--sans) !important;
  font-size:   1.2rem !important;
  font-weight: 700 !important;
  color:       var(--text) !important;
}

/* ══ DIVIDER ══ */
hr {
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 1.5rem 0 !important;
}

/* ══ ALERTS ══ */
[data-testid="stAlert"] {
  border-radius: var(--radius-sm) !important;
  font-family:   var(--mono) !important;
  font-size:     0.8rem !important;
}
.stSpinner > div { color: var(--cyan) !important; }

/* ══ BORDERED CONTAINERS ══ */
[data-testid="stVerticalBlockBorderWrapper"] > div {
  background:    var(--surface) !important;
  border:        1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  padding:       1.2rem 1.4rem !important;
}

/* ═══════════════════════════════════
   CUSTOM HTML COMPONENTS
═══════════════════════════════════ */
.brand-bar {
  display:     flex;
  align-items: center;
  gap:         1rem;
  padding:     .5rem 0 1.2rem;
}
.brand-icon {
  width:48px; height:48px;
  background:    var(--cyan);
  border-radius: 12px;
  display:flex; align-items:center; justify-content:center;
  font-size:1.4rem; flex-shrink:0;
  box-shadow: 0 0 24px rgba(0,229,195,.28);
}
.brand-name {
  font-family:    var(--sans);
  font-size:      1.75rem;
  font-weight:    800;
  color:          var(--text);
  letter-spacing: -.03em;
  line-height:    1;
}
.brand-name em { color:var(--cyan); font-style:normal; }
.brand-sub {
  font-family:    var(--mono);
  font-size:      0.68rem;
  color:          var(--text-dim);
  letter-spacing: .12em;
  text-transform: uppercase;
  margin-top:     .3rem;
}

.slabel {
  font-family:    var(--mono);
  font-size:      0.66rem;
  font-weight:    500;
  letter-spacing: .14em;
  text-transform: uppercase;
  color:          var(--text-dim);
  margin-bottom:  .8rem;
}

/* Big pipeline */
.big-pipeline {
  display:       flex;
  align-items:   stretch;
  background:    var(--surface);
  border:        1px solid var(--border);
  border-radius: var(--radius);
  overflow:      hidden;
}
.bp-step {
  flex:       1;
  padding:    .9rem .8rem;
  text-align: center;
  border-right: 1px solid var(--border);
}
.bp-step:last-child { border-right: none; }
.bp-icon  { font-size:1.2rem; margin-bottom:.3rem; }
.bp-name  { font-family:var(--mono); font-size:.68rem; text-transform:uppercase; letter-spacing:.08em; color:var(--text); font-weight:500; }
.bp-desc  { font-family:var(--mono); font-size:.6rem; color:var(--text-dim); margin-top:.15rem; }

/* Result card */
.result-card {
  background:    var(--surface2);
  border:        1px solid var(--border-hi);
  border-radius: var(--radius);
  padding:       1.4rem 1.6rem;
  margin-top:    1.2rem;
}
.status-pill {
  display:        inline-flex;
  align-items:    center;
  gap:            .4rem;
  font-family:    var(--mono);
  font-size:      .72rem;
  font-weight:    700;
  text-transform: uppercase;
  letter-spacing: .1em;
  padding:        .3rem .75rem;
  border-radius:  20px;
  margin-bottom:  .9rem;
}
.pill-replied   { background:rgba(0,200,150,.12); color:var(--green); border:1px solid rgba(0,200,150,.3); }
.pill-escalated { background:rgba(240,165,0,.1);  color:var(--amber); border:1px solid rgba(240,165,0,.3); }

.meta-chips { display:flex; gap:.6rem; flex-wrap:wrap; margin-bottom:1.1rem; }
.meta-chip  {
  background:    var(--bg);
  border:        1px solid var(--border);
  border-radius: 6px;
  padding:       .28rem .65rem;
  font-family:   var(--mono);
  font-size:     .72rem;
  color:         var(--text-dim);
}
.meta-chip b { color:var(--text); font-weight:600; }

.response-box {
  background:    var(--bg);
  border:        1px solid var(--border-hi);
  border-left:   3px solid var(--cyan);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  padding:       1rem 1.2rem;
  font-family:   var(--sans);
  font-size:     .91rem;
  line-height:   1.75;
  color:         var(--text);
  margin-bottom: 1rem;
}
.justif-box {
  background:    var(--amber-dim);
  border:        1px solid rgba(240,165,0,.2);
  border-radius: var(--radius-sm);
  padding:       .9rem 1.1rem;
}
.justif-label {
  font-family:    var(--mono);
  font-size:      .63rem;
  letter-spacing: .14em;
  text-transform: uppercase;
  color:          var(--amber);
  font-weight:    700;
  margin-bottom:  .45rem;
}
.justif-text {
  font-family: var(--mono);
  font-size:   .78rem;
  line-height: 1.65;
  color:       var(--text-dim);
}

/* Evidence */
.ev-card {
  background:    var(--surface);
  border:        1px solid var(--border);
  border-radius: var(--radius);
  padding:       1.1rem 1.3rem 1rem;
  margin-bottom: .7rem;
  position:      relative;
}
.ev-num {
  position:      absolute;
  top:.9rem; right:1rem;
  font-family:   var(--mono);
  font-size:     .65rem;
  color:         var(--text-dim);
  background:    var(--bg2);
  border:        1px solid var(--border);
  border-radius: 5px;
  padding:       .12rem .45rem;
}
.ev-title {
  font-family:   var(--sans);
  font-size:     .95rem;
  font-weight:   700;
  color:         var(--text);
  margin-bottom: .45rem;
  padding-right: 2.5rem;
}
.ev-meta { display:flex; gap:.5rem; flex-wrap:wrap; margin-bottom:.55rem; }
.ev-tag  {
  font-family:   var(--mono);
  font-size:     .67rem;
  color:         var(--text-dim);
  background:    var(--bg2);
  border:        1px solid var(--border);
  border-radius: 5px;
  padding:       .13rem .5rem;
}
.ev-score {
  font-family:   var(--mono);
  font-size:     .67rem;
  color:         var(--cyan);
  background:    rgba(0,229,195,.08);
  border:        1px solid rgba(0,229,195,.2);
  border-radius: 5px;
  padding:       .13rem .5rem;
}
.ev-url { font-family:var(--mono); font-size:.72rem; color:var(--cyan-dim); text-decoration:none; word-break:break-all; }
.ev-url:hover { text-decoration:underline; }

/* About */
.about-block {
  background:    var(--surface);
  border:        1px solid var(--border);
  border-radius: var(--radius);
  padding:       1.2rem 1.4rem;
  margin-bottom: .7rem;
}
.about-title { font-family:var(--sans); font-size:.95rem; font-weight:700; color:var(--text); margin-bottom:.5rem; }
.about-body  { font-family:var(--sans); font-size:.87rem; line-height:1.7; color:var(--text-dim); }

.check-item {
  display:       flex;
  align-items:   flex-start;
  gap:           .55rem;
  font-family:   var(--mono);
  font-size:     .78rem;
  color:         var(--text-dim);
  padding:       .32rem 0;
  border-bottom: 1px solid var(--border);
}
.check-item:last-child { border-bottom:none; }
.check-dot {
  width:12px; height:12px; flex-shrink:0; margin-top:2px;
  border-radius:50%; background:var(--cyan);
  box-shadow:0 0 6px rgba(0,229,195,.4);
}

/* Pipeline mini */
.pipeline { display:flex; align-items:center; flex-wrap:wrap; }
.pipe-step {
  background:    var(--bg2);
  border:        1px solid var(--border-hi);
  border-radius: 6px;
  padding:       .25rem .6rem;
  font-family:   var(--mono);
  font-size:     .67rem;
  color:         var(--text);
}
.pipe-arrow { padding:0 .28rem; color:var(--border-hi); }

/* Empty state */
.empty-state {
  background:    var(--surface);
  border:        1px dashed var(--border-hi);
  border-radius: var(--radius);
  padding:       2.5rem;
  text-align:    center;
  margin-top:    .5rem;
}
.empty-icon { font-size:2rem; margin-bottom:.6rem; }
.empty-text { font-family:var(--mono); font-size:.78rem; color:var(--text-dim); line-height:1.6; }

/* Footer */
.footer-bar {
  text-align:    center;
  font-family:   var(--mono);
  font-size:     .66rem;
  color:         var(--text-dim);
  padding:       1rem 0 .5rem;
  letter-spacing:.08em;
}
.footer-bar span { color:var(--cyan); }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
#  DATA
# ═══════════════════════════════════════════════════════════════════
EXAMPLES = {
    "HackerRank score dispute": {
        "company": "HackerRank",
        "subject": "Assessment score issue",
        "issue": "My test score is wrong. Please review my answers and increase my score.",
    },
    "HackerRank subscription pause": {
        "company": "HackerRank",
        "subject": "Pause subscription",
        "issue": "Hi, please pause our subscription. We have stopped all hiring efforts for now.",
    },
    "Claude workspace access": {
        "company": "Claude",
        "subject": "Workspace access",
        "issue": "I lost access to my Claude team workspace after our admin removed my seat. Please restore my access.",
    },
    "Claude crawler blocking": {
        "company": "Claude",
        "subject": "Crawler blocking",
        "issue": "I want Claude to stop crawling my website. What should I do?",
    },
    "Visa lost card guidance": {
        "company": "Visa",
        "subject": "Lost card",
        "issue": "Where can I report a lost or stolen Visa card from India?",
    },
    "Visa refund request": {
        "company": "Visa",
        "subject": "Merchant refund",
        "issue": "I bought something online with my Visa card, but the merchant sent the wrong product. Please make Visa refund me today.",
    },
}


# ═══════════════════════════════════════════════════════════════════
#  CACHED RESOURCES & STATE
# ═══════════════════════════════════════════════════════════════════
@st.cache_resource(show_spinner=False)
def load_agent_resources():
    documents = load_corpus(DATA_DIR)
    retriever = CorpusRetriever(documents)
    return documents, retriever


def init_state():
    defaults = {"company": "Auto Detect", "subject": "", "issue": "", "result": None, "top_docs": [], "_pending_example": None}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def apply_example(name):
    """Queue an example to be applied on the next rerun, before widgets are instantiated."""
    st.session_state["_pending_example"] = name


def flush_pending_example():
    """Apply a queued example. Must be called BEFORE any widget with these keys is rendered."""
    name = st.session_state.get("_pending_example")
    if name and name in EXAMPLES:
        ex = EXAMPLES[name]
        st.session_state["company"] = ex["company"]
        st.session_state["subject"] = ex["subject"]
        st.session_state["issue"]   = ex["issue"]
        st.session_state["_pending_example"] = None


def readable(val):
    return str(val or "").replace("_", " ").title()


def get_top_documents(retriever, issue, subject, company):
    company_key = infer_company_key(issue, subject, company)
    return retriever.search(query=f"{subject} {issue}", company_key=company_key, top_k=3)


# ═══════════════════════════════════════════════════════════════════
#  RENDERERS
# ═══════════════════════════════════════════════════════════════════
def render_header(doc_count):
    st.markdown("""
    <div class="brand-bar">
      <div class="brand-icon">⚡</div>
      <div>
        <div class="brand-name">Support <em>Triage</em> Agent</div>
        <div class="brand-sub">Local RAG · Multi-Domain · HackerRank · Claude · Visa</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Support Articles", doc_count)
    c2.metric("Domains", "3")
    c3.metric("Retrieval", "TF-IDF")
    c4.metric("Mode", "Local Corpus")


def render_pipeline():
    st.markdown("""
    <div class="big-pipeline">
      <div class="bp-step"><div class="bp-icon">📝</div><div class="bp-name">Ticket Input</div><div class="bp-desc">Subject &amp; body</div></div>
      <div class="bp-step"><div class="bp-icon">🏢</div><div class="bp-name">Company Detect</div><div class="bp-desc">Auto or manual</div></div>
      <div class="bp-step"><div class="bp-icon">🔍</div><div class="bp-name">Corpus Retrieval</div><div class="bp-desc">TF-IDF top-k</div></div>
      <div class="bp-step"><div class="bp-icon">🛡</div><div class="bp-name">Safety Routing</div><div class="bp-desc">Risk assessment</div></div>
      <div class="bp-step"><div class="bp-icon">✅</div><div class="bp-name">Reply / Escalate</div><div class="bp-desc">Final decision</div></div>
    </div>
    """, unsafe_allow_html=True)


def render_result(result):
    replied   = result["status"] == "replied"
    pill_cls  = "pill-replied" if replied else "pill-escalated"
    pill_txt  = "✓ Replied"    if replied else "⚠ Escalated"

    st.markdown(f"""
    <div class="result-card">
      <div><span class="status-pill {pill_cls}">{pill_txt}</span></div>
      <div class="meta-chips">
        <div class="meta-chip">Request &nbsp;<b>{readable(result['request_type'])}</b></div>
        <div class="meta-chip">Product &nbsp;<b>{readable(result['product_area'])}</b></div>
        <div class="meta-chip">Status &nbsp;<b>{readable(result['status'])}</b></div>
      </div>
      <div class="slabel" style="margin-bottom:.45rem;">Agent Response</div>
      <div class="response-box">{result['response']}</div>
      <div class="justif-box">
        <div class="justif-label">⚙ Decision Justification</div>
        <div class="justif-text">{result['justification']}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_evidence(top_docs):
    if not top_docs:
        st.markdown("""
        <div class="empty-state">
          <div class="empty-icon">🔍</div>
          <div class="empty-text">No evidence retrieved yet.<br>Analyze a ticket first to see corpus matches here.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    for i, item in enumerate(top_docs, 1):
        doc = item.document
        url_html = (
            f'<a class="ev-url" href="{doc.source_url}" target="_blank">{doc.source_url}</a>'
            if doc.source_url else
            '<span style="font-family:var(--mono);font-size:.72rem;color:var(--text-dim);">No URL available</span>'
        )
        st.markdown(f"""
        <div class="ev-card">
          <div class="ev-num">#{i}</div>
          <div class="ev-title">{doc.title}</div>
          <div class="ev-meta">
            <span class="ev-tag">🏢 {doc.company_name}</span>
            <span class="ev-tag">📂 {doc.breadcrumbs or '—'}</span>
            <span class="ev-score">Score {item.score:.3f}</span>
          </div>
          {url_html}
        </div>
        """, unsafe_allow_html=True)


def render_about():
    st.markdown("""
    <div class="about-block">
      <div class="about-title">📦 Project Summary</div>
      <div class="about-body">
        This demo uses the same backend as the terminal solution. It loads the local Markdown support
        corpus, retrieves relevant articles using TF-IDF, classifies the ticket, checks safety rules,
        and decides whether to reply or escalate. No live web access is used.
      </div>
    </div>

    <div class="about-block">
      <div class="about-title">🛡 Safety Principle</div>
      <div class="about-body">
        The agent does not answer everything. It replies only when the corpus provides sufficient evidence.
        It escalates risky, account-specific, payment-related, unsupported, or weak-evidence cases.
      </div>
    </div>

    <div class="about-block">
      <div class="about-title">⚙ What the Agent Evaluates</div>
      <div style="margin-top:.6rem;">
        <div class="check-item"><div class="check-dot"></div>Corpus retrieval quality &amp; evidence score</div>
        <div class="check-item"><div class="check-dot"></div>Request type classification</div>
        <div class="check-item"><div class="check-dot"></div>Product area identification</div>
        <div class="check-item"><div class="check-dot"></div>Risk level assessment</div>
        <div class="check-item"><div class="check-dot"></div>Reply vs. escalation decision</div>
      </div>
    </div>

    <div class="about-block">
      <div class="about-title">🎬 Demo Tip</div>
      <div class="about-body">
        For a recording, type one ticket manually instead of only using the example loader.
        That makes it clear the system is fully dynamic and not hardcoded.
      </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════
def main():
    init_state()
    flush_pending_example()  # apply any queued example BEFORE widgets are rendered

    with st.spinner("Loading local support corpus…"):
        documents, retriever = load_agent_resources()

    render_header(len(documents))
    st.divider()
    render_pipeline()
    st.divider()

    tab1, tab2, tab3 = st.tabs(["⚡  Analyze Ticket", "🔍  Evidence", "ℹ  About"])

    # ─── TAB 1 ──────────────────────────────────────────────────────
    with tab1:
        left, _, right = st.columns([1.35, 0.05, 0.9])

        with left:
            st.markdown('<div class="slabel">Compose Ticket</div>', unsafe_allow_html=True)

            company = st.selectbox(
                "Company",
                ["Auto Detect", "HackerRank", "Claude", "Visa"],
                key="company",
            )
            subject = st.text_input(
                "Subject",
                key="subject",
                placeholder="e.g. Billing issue, lost card, Claude access",
            )
            issue = st.text_area(
                "Ticket Message",
                key="issue",
                height=215,
                placeholder="Paste or type the full support ticket here…",
            )
            analyze = st.button("⚡  Analyze Ticket", type="primary", use_container_width=True)

        with right:
            with st.container(border=True):
                st.markdown('<div class="slabel">Demo Scenarios</div>', unsafe_allow_html=True)
                st.markdown(
                    '<p style="font-family:var(--mono);font-size:.73rem;color:var(--text-dim);margin-bottom:.8rem;">'
                    "These load the form only — the actual answer comes from the live agent pipeline."
                    "</p>",
                    unsafe_allow_html=True,
                )
                example_name = st.selectbox("Scenario", list(EXAMPLES.keys()), label_visibility="collapsed")
                if st.button("Load Scenario", use_container_width=True):
                    apply_example(example_name)  # queues; actual apply happens on rerun
                    st.rerun()

            with st.container(border=True):
                st.markdown('<div class="slabel">Pipeline Flow</div>', unsafe_allow_html=True)
                st.markdown("""
                <div class="pipeline">
                  <span class="pipe-step">Ticket</span><span class="pipe-arrow">→</span>
                  <span class="pipe-step">Detect</span><span class="pipe-arrow">→</span>
                  <span class="pipe-step">Retrieve</span><span class="pipe-arrow">→</span>
                  <span class="pipe-step">Safety</span><span class="pipe-arrow">→</span>
                  <span class="pipe-step">Reply / Escalate</span>
                </div>
                """, unsafe_allow_html=True)

        # ── Run pipeline ──
        if analyze:
            if not st.session_state["issue"].strip():
                st.error("Please enter a ticket message before analyzing.")
                return

            sel_company = "" if st.session_state["company"] == "Auto Detect" else st.session_state["company"]

            with st.spinner("Retrieving evidence and checking safety rules…"):
                result = process_ticket(
                    retriever=retriever,
                    issue=st.session_state["issue"],
                    subject=st.session_state["subject"],
                    company=sel_company,
                )
                top_docs = get_top_documents(
                    retriever=retriever,
                    issue=st.session_state["issue"],
                    subject=st.session_state["subject"],
                    company=sel_company,
                )

            st.session_state["result"]   = result
            st.session_state["top_docs"] = top_docs
            st.success("Analysis complete — results below")

        if st.session_state["result"]:
            render_result(st.session_state["result"])

    # ─── TAB 2 ──────────────────────────────────────────────────────
    with tab2:
        st.markdown('<div class="slabel">Retrieved Corpus Evidence</div>', unsafe_allow_html=True)
        render_evidence(st.session_state["top_docs"])

    # ─── TAB 3 ──────────────────────────────────────────────────────
    with tab3:
        render_about()

    st.markdown("""
    <div class="footer-bar">
      Built for <span>HackerRank Orchestrate</span> · Local corpus only · No live web access
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
