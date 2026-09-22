import streamlit as st



def inject_premium_styles():
    st.markdown(
        """
        <style>
        :root {
          --bg:#111318; --bg-soft:#171a21; --surface:#1b1f28; --surface-2:#222733;
          --border:#303746; --text:#f4f1ea; --text-soft:#c4c8d1; --muted:#8e96a5;
          --accent:#d7a85f; --accent-strong:#e8bd79; --accent-ink:#17130d;
          --success:#77c8a3; --warning:#e8b36b; --danger:#f08c88; --shadow:rgba(0,0,0,.28);
        }
        html, body, [class*="css"], .stApp { color:var(--text) !important; }
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background:var(--bg) !important; }
        [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer { display:none !important; }
        .block-container { max-width:1260px; padding:2rem 2.5rem 4rem !important; }
        .nav-rule, .admin-rule { background:var(--border) !important; }
        .brand, .footer-brand, .login-brand { color:var(--text) !important; }
        .brand-mark { background:var(--accent) !important; }
        .brand-mark:after { background:var(--bg) !important; }
        h1,h2,h3,h4,p,li,label,span,b,strong { color:var(--text); }
        h1 { font-size:clamp(2rem,4vw,3.6rem) !important; letter-spacing:-.045em !important; }
        h2 { font-size:clamp(1.45rem,2.5vw,2rem) !important; }
        .page-intro { margin:2rem 0 1.35rem !important; }
        .page-intro h1 { color:var(--text) !important; margin:.5rem 0 .65rem !important; }
        .page-intro p, .hero p, .content-section p, .venue-line { color:var(--text-soft) !important; }
        .eyebrow, .section-kicker, .filter-label, .event-category { color:var(--accent-strong) !important; }
        .breadcrumb { color:var(--muted) !important; }
        .breadcrumb span { color:var(--accent) !important; }
        .stButton > button { color:var(--text) !important; background:var(--surface) !important; border:1px solid var(--border) !important; border-radius:10px !important; box-shadow:0 5px 16px var(--shadow); transition:transform .16s ease, border-color .16s ease, background .16s ease !important; }
        .stButton > button:hover { color:var(--accent-strong) !important; border-color:var(--accent) !important; background:var(--surface-2) !important; transform:translateY(-1px); }
        .stButton > button:active { transform:translateY(0); }
        .stButton > button[kind="primary"], button[data-testid^="stBaseButton-primary"] { color:#fffaf3 !important; background:#b8734b !important; border-color:#b8734b !important; }
        .stButton > button[kind="primary"]:hover, button[data-testid^="stBaseButton-primary"]:hover { color:#fffaf3 !important; background:#cf8b60 !important; }
        .stButton > button:disabled { color:#747b88 !important; background:#20242c !important; border-color:#2c313c !important; }
        .stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input, .stTimeInput input, .stSelectbox [data-baseweb="select"] > div, [data-testid="stFileUploaderDropzone"] { color:var(--text) !important; background:var(--surface) !important; border:1px solid var(--border) !important; border-radius:10px !important; }
        .stTextInput input::placeholder, .stTextArea textarea::placeholder { color:var(--muted) !important; }
        .stTextInput label, .stTextArea label, .stNumberInput label, .stDateInput label, .stTimeInput label, .stSelectbox label, .stFileUploader label, .stRadio label { color:var(--text-soft) !important; }
        [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] { background:var(--surface-2) !important; color:var(--text) !important; }
        [role="option"] { color:var(--text) !important; }
        [role="option"]:hover { background:var(--border) !important; }
        [data-testid="stForm"] { background:var(--surface) !important; border:1px solid var(--border) !important; border-radius:16px !important; box-shadow:0 18px 45px var(--shadow); padding:1.5rem !important; }
        .hero { max-width:820px; margin:4rem auto 2rem !important; }
        .hero h1 { color:var(--text) !important; font-size:clamp(2.8rem,7vw,5.5rem) !important; }
        .hero h1 em { color:var(--accent-strong) !important; }
        .event-card { background:var(--surface) !important; border:1px solid var(--border); border-radius:16px; padding:.65rem; box-shadow:0 12px 28px var(--shadow); transition:transform .18s ease, border-color .18s ease, box-shadow .18s ease; }
        .event-card:hover { transform:translateY(-4px); border-color:var(--accent); box-shadow:0 20px 38px var(--shadow); }
        .event-card-copy { padding:.8rem .35rem .55rem !important; }
        .event-title { color:var(--text) !important; font-size:17px !important; }
        .event-meta, .event-card-bottom, .section-head span { color:var(--text-soft) !important; }
        .event-card-bottom b, .summary-total strong { color:var(--accent-strong) !important; }
        [data-testid="stImage"] img { border-radius:12px !important; background:var(--surface-2); aspect-ratio:2/3; object-fit:cover; }
        .poster-fallback { min-height:210px; border-radius:12px; padding:1.2rem; display:flex; flex-direction:column; justify-content:flex-end; gap:.5rem; background:radial-gradient(circle at 80% 15%, rgba(215,168,95,.28), transparent 34%), linear-gradient(145deg,#252b38,#151820 72%); border:1px solid #3b4352; color:var(--text); overflow:hidden; }
        .poster-fallback span { color:var(--accent-strong); font:500 10px 'DM Mono',monospace; letter-spacing:.14em; }
        .poster-fallback strong { color:var(--text); font-size:20px; line-height:1.08; }
        .poster-fallback small { color:var(--muted); font:500 9px 'DM Mono',monospace; letter-spacing:.08em; }
        .event-card .poster-fallback { min-height:160px; }
        .detail-summary .poster-fallback { min-height:390px; }
        .editorial-note, .detail-rule, .ticket-divider { border-color:var(--border) !important; }
        .detail-summary, .content-section, .info-list { color:var(--text); }
        .detail-summary h1, .detail-summary h2, .content-section h2 { color:var(--text) !important; }
        .detail-key span, .info-list span, .ticket-detail span, .ticket-metric span, .confirmation-grid span, .profile-label { color:var(--muted) !important; }
        .detail-key b, .info-list b, .ticket-detail b, .ticket-metric b { color:var(--text) !important; }
        .seat-area, .summary-card, .ticket, .profile-card, .activity-card, .support-shell { background:var(--surface) !important; border:1px solid var(--border) !important; box-shadow:0 15px 34px var(--shadow); }
        .screen-label, .row-label, .seat-legend, .secure-note, .empty-state { color:var(--text-soft) !important; }
        .screen-line { background:var(--accent) !important; opacity:.7; }
        .seat-swatch.available { border-color:var(--text-soft) !important; }
        .seat-swatch.selected { background:var(--accent) !important; }
        .seat-swatch.reserved { background:var(--warning) !important; }
        .seat-swatch.sold { background:#7b4a4c !important; }
        .summary-line, .booking-meta { color:var(--text-soft) !important; }
        .summary-line b, .summary-card h3, .booking-event { color:var(--text) !important; }
        .status.confirmed { color:var(--success) !important; background:rgba(119,200,163,.14) !important; }
        .status.completed { color:var(--accent-strong) !important; background:rgba(215,168,95,.14) !important; }
        .status.cancelled { color:var(--danger) !important; background:rgba(240,140,136,.14) !important; }
        .confirmation-check { background:rgba(119,200,163,.15) !important; color:var(--success) !important; }
        .confirmation-id { color:var(--text-soft) !important; }
        .support-welcome p { color:var(--text-soft) !important; }
        .stChatMessage { background:var(--surface) !important; border:1px solid var(--border); border-radius:12px; margin:.5rem 0; }
        .stChatInput textarea { background:var(--surface) !important; color:var(--text) !important; border-color:var(--border) !important; }
        .profile-card p, .activity-grid span { color:var(--text-soft) !important; }
        [data-testid="stMetric"] { background:var(--surface) !important; border:1px solid var(--border) !important; border-radius:16px !important; box-shadow:0 15px 34px var(--shadow); }
        [data-testid="stMetricLabel"] p { color:var(--muted) !important; }
        [data-testid="stMetricValue"] { color:var(--accent-strong) !important; }
        [data-testid="stDataFrame"] { border:1px solid var(--border); border-radius:12px; overflow:hidden; }
        [data-testid="stDataFrame"] * { color:var(--text) !important; }
        [data-testid="stSidebar"] { background:#0c0e12 !important; border-right:1px solid var(--border); }
        [data-testid="stSidebar"] * { color:var(--text-soft) !important; }
        [data-testid="stSidebar"] .stButton > button { background:transparent !important; box-shadow:none; text-align:left; }
        [data-testid="stSidebar"] .stButton > button:hover { background:var(--surface) !important; color:var(--accent-strong) !important; }
        [data-testid="stSidebar"] .stButton > button[kind="primary"] { background:var(--accent) !important; color:var(--accent-ink) !important; }
        .admin-brand { color:var(--text) !important; }
        .admin-brand small { color:var(--accent-strong) !important; }
        .admin-rule { background:var(--border) !important; }
        .login-shell { background:rgba(27,31,40,.96) !important; border:1px solid var(--border) !important; box-shadow:0 24px 70px rgba(0,0,0,.4) !important; }
        .login-shell .login-title, .login-shell .login-copy, .login-shell .login-hint { color:var(--text) !important; }
        .login-shell .login-copy, .login-shell .login-hint { color:var(--text-soft) !important; }
        .stAlert { background:var(--surface) !important; border:1px solid var(--border) !important; color:var(--text) !important; }
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4,
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] span,
        [data-testid="stMarkdownContainer"] b,
        [data-testid="stMarkdownContainer"] strong { color:var(--text) !important; }
        [data-testid="stMarkdownContainer"] .eyebrow,
        [data-testid="stMarkdownContainer"] .section-kicker,
        [data-testid="stMarkdownContainer"] .filter-label,
        [data-testid="stMarkdownContainer"] .event-category { color:var(--accent-strong) !important; }
        [data-testid="stMarkdownContainer"] .event-meta,
        [data-testid="stMarkdownContainer"] .event-card-bottom,
        [data-testid="stMarkdownContainer"] .page-intro p,
        [data-testid="stMarkdownContainer"] .hero p,
        [data-testid="stMarkdownContainer"] .venue-line,
        [data-testid="stMarkdownContainer"] .confirmation-id,
        [data-testid="stMarkdownContainer"] .booking-meta { color:var(--text-soft) !important; }
        [data-testid="stMarkdownContainer"] .breadcrumb { color:var(--muted) !important; }
        [data-testid="stMarkdownContainer"] .breadcrumb span { color:var(--accent) !important; }
        [data-testid="stMarkdownContainer"] .detail-key span,
        [data-testid="stMarkdownContainer"] .info-list span,
        [data-testid="stMarkdownContainer"] .ticket-detail span,
        [data-testid="stMarkdownContainer"] .ticket-metric span,
        [data-testid="stMarkdownContainer"] .confirmation-grid span,
        [data-testid="stMarkdownContainer"] .profile-label { color:var(--muted) !important; }
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input,
        [data-testid="stTimeInput"] input { color:var(--text) !important; -webkit-text-fill-color:var(--text) !important; }
        [data-testid="stTextInput"] label,
        [data-testid="stTextArea"] label,
        [data-testid="stNumberInput"] label,
        [data-testid="stDateInput"] label,
        [data-testid="stTimeInput"] label,
        [data-testid="stSelectbox"] label,
        [data-testid="stFileUploader"] label { color:var(--text-soft) !important; }
        [data-baseweb="tab"] p, [data-baseweb="tab"] { color:var(--text-soft) !important; }
        [data-baseweb="tab"][aria-selected="true"] p, [data-baseweb="tab"][aria-selected="true"] { color:var(--accent-strong) !important; }
        @media (max-width:760px) { .block-container { padding:1rem 1rem 3rem !important; } .hero { margin:2.2rem auto 1.5rem !important; } .page-intro h1 { font-size:2.2rem !important; } }
        </style>
        """,
        unsafe_allow_html=True,
    )
