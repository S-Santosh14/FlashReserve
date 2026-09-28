
import streamlit as st

LIGHT_CSS = r"""<style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
        :root { --ink:#13253f; --ink-soft:#314157; --blue:#1769e0; --blue-dark:#0c4ca9; --paper:#f8f8f6; --panel:#ffffff; --mist:#edf1f5; --line:#dce3ea; --muted:#6f7b8d; --green:#16825d; --amber:#a76a06; --red:#be4650; }
        html, body, [class*="css"] { font-family:'Manrope', Arial, sans-serif; color:var(--ink); }
        .stApp { background:var(--paper); }
        [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer { display:none !important; }
        .block-container { max-width:1180px; padding:1.05rem 2rem 2.8rem !important; }
        .nav-rule { height:1px; background:var(--line); margin:-1.05rem 0 1.05rem; }
        .nav-space { height:1.15rem; }
        .brand { font-size:14px; font-weight:800; color:var(--ink); letter-spacing:.07em; white-space:nowrap; padding-top:.65rem; }
        .brand-mark { display:inline-block; position:relative; width:13px; height:13px; margin:0 8px -2px 0; background:var(--blue); transform:rotate(45deg); border-radius:2px; }
        .brand-mark:after { content:''; position:absolute; width:5px; height:5px; border-radius:50%; background:var(--paper); top:4px; left:4px; }
        h1,h2,h3,p { margin-top:0; } h1 { letter-spacing:-.055em; line-height:1.04; } h2 { letter-spacing:-.035em; }
        .stButton > button { min-height:38px; border-radius:8px; font-family:'Manrope',sans-serif; font-size:12px; font-weight:700; letter-spacing:.005em; border:1px solid var(--line); color:var(--ink); background:transparent; transition:.18s ease; }
        .stButton > button:hover { border-color:#a8b7c9; color:var(--blue); background:#f4f7fb; }
        .stButton > button[kind="primary"], button[data-testid^="stBaseButton-primary"] { color:white; background:var(--blue); border-color:var(--blue); }
        .stButton > button[kind="primary"]:hover, button[data-testid^="stBaseButton-primary"]:hover { background:var(--blue-dark); border-color:var(--blue-dark); color:white; }
        .stButton > button:disabled { color:#9faab8; background:#eef1f4; border-color:#eef1f4; opacity:1; }
        .stTextInput input, .stSelectbox [data-baseweb="select"] > div { border:1px solid var(--line) !important; background:var(--panel) !important; border-radius:9px !important; min-height:45px !important; color:var(--ink) !important; box-shadow:none !important; }
        .stTextInput input:focus { border-color:var(--blue) !important; box-shadow:0 0 0 3px rgba(23,105,224,.10) !important; }
        .stTextInput input::placeholder { color:#8b96a5; }
        .stTextInput label, .stSelectbox label { color:var(--ink); font-size:12px; font-weight:700; }
        .hero { margin:2.4rem auto 1.4rem; max-width:710px; text-align:center; }
        .eyebrow, .section-kicker, .filter-label { color:var(--blue); font-family:'DM Mono',monospace; font-size:10px; font-weight:500; letter-spacing:.14em; }
        .hero h1 { font-size:clamp(42px,5.4vw,67px); margin:.65rem 0 .75rem; font-weight:800; color:var(--ink); }
        .hero h1 em { color:var(--blue); font-style:normal; }
        .hero p { max-width:510px; color:var(--muted); font-size:15px; line-height:1.75; margin:0 auto; }
        .location-pill { font-size:12px; font-weight:700; color:var(--ink-soft); padding-top:.7rem; }
        .location-pill::first-letter { color:var(--blue); }
        .section-spacer { height:2.7rem; }
        .section-head { display:flex; justify-content:space-between; align-items:baseline; margin:2.55rem 0 1rem; }
        .section-head h2 { margin:0; font-size:22px; font-weight:800; } .section-head span { color:var(--muted); font-size:12px; }
        .event-card { margin-bottom:1.2rem; } .event-card-copy { padding:.95rem .15rem .45rem; }
        .event-category { font-family:'DM Mono',monospace; color:var(--blue); letter-spacing:.095em; font-size:9px; font-weight:500; }
        .event-title { font-size:15px; font-weight:800; letter-spacing:-.025em; color:var(--ink); margin:.38rem 0 .25rem; }
        .event-meta { font-size:11px; color:var(--muted); line-height:1.5; } .event-card-bottom { font-size:11px; color:var(--muted); margin-top:.82rem; }
        .event-card-bottom b { color:var(--ink); }
        [data-testid="stImage"] img { border-radius:10px; aspect-ratio:1.52/1; object-fit:cover; }
        .editorial-note { margin:3.7rem 0 1rem; border-top:1px solid var(--line); border-bottom:1px solid var(--line); padding:1.05rem 0; display:flex; gap:1.2rem; align-items:baseline; }
        .editorial-note span { font-family:'DM Mono',monospace; font-size:10px; color:var(--blue); letter-spacing:.12em; }.editorial-note p { margin:0; font-size:15px; font-weight:800; letter-spacing:-.02em; }.editorial-note small { color:var(--muted); }
        .page-intro { margin:2.1rem 0 1.5rem; } .page-intro.compact { margin-top:1rem; }
        .page-intro h1 { margin:.5rem 0 .45rem; font-size:42px; font-weight:800; }.page-intro p { color:var(--muted); margin:0; font-size:14px; }
        .filter-label { margin:1.45rem 0 .52rem; }.result-count { font-size:12px; color:var(--muted); margin:1.8rem 0 .9rem; }
        .tiny-gap { height:.7rem; }.detail-summary { padding:.5rem .2rem 0; }.detail-summary h1 { font-size:47px; margin:.5rem 0 .45rem; font-weight:800; }.venue-line { color:var(--muted); line-height:1.65; margin:0; }
        .detail-rule { height:1px; background:var(--line); margin:1.45rem 0 1rem; }.detail-key { display:flex; justify-content:space-between; gap:1rem; padding:.5rem 0; font-size:12px; }.detail-key span,.info-list span,.ticket-detail span,.ticket-metric span,.confirmation-grid span,.profile-label { color:var(--muted); font-family:'DM Mono',monospace; font-size:9px; letter-spacing:.11em; }.detail-key b { text-align:right; line-height:1.55; }.content-section { padding-top:3.1rem; }.content-section h2 { font-size:25px; margin:.45rem 0 .65rem; }.content-section p { max-width:670px; color:var(--ink-soft); font-size:14px; line-height:1.9; }.info-list { padding-top:3rem; }.info-list > div:not(.section-kicker) { padding:.68rem 0; border-bottom:1px solid var(--line); display:flex; justify-content:space-between; font-size:12px; gap:1rem; }.info-list b { text-align:right; }
        .seat-area { padding:1.45rem 1.2rem .7rem; border:1px solid var(--line); border-radius:12px; background:var(--panel); }.screen-label { text-align:center; color:var(--muted); font-family:'DM Mono',monospace; letter-spacing:.16em; font-size:9px; }.screen-line { width:62%; height:3px; background:#b8c3cf; border-radius:50%; margin:.52rem auto 1.7rem; }.row-label { padding-top:.6rem; color:var(--muted); font-family:'DM Mono',monospace; font-size:11px; }
        .seat-area .stButton > button { min-height:35px; padding:.25rem; font-size:10px; }.seat-legend { display:flex; gap:1.1rem; flex-wrap:wrap; margin:.95rem .15rem .1rem; color:var(--muted); font-size:10px; }.seat-legend span { display:flex; align-items:center; gap:.34rem; }.seat-swatch { width:10px; height:10px; border-radius:3px; display:inline-block; }.seat-swatch.available { border:1px solid #9aa7b7; }.seat-swatch.selected { background:var(--blue); }.seat-swatch.sold { background:#e6eaee; }
        .summary-card { border:1px solid var(--line); border-radius:11px; background:var(--panel); padding:1.25rem; }.summary-card h3 { font-size:16px; margin:.58rem 0 1rem; letter-spacing:-.025em; }.summary-line { display:flex; justify-content:space-between; align-items:flex-start; gap:.8rem; padding:.58rem 0; color:var(--muted); font-size:12px; }.summary-line b { color:var(--ink); text-align:right; font-weight:700; }.summary-total { display:flex; justify-content:space-between; align-items:center; padding-top:1rem; margin-top:.55rem; border-top:1px solid var(--line); font-size:12px; }.summary-total strong { color:var(--blue); font-size:18px; }.summary-card + .stButton { margin-top:.65rem; }
        .checkout-event { border-top:1px solid var(--line); border-bottom:1px solid var(--line); padding:1.25rem 0; }.checkout-event h2 { font-size:27px; margin:.45rem 0; }.checkout-event p { color:var(--muted); font-size:13px; line-height:1.75; }.checkout-seats { display:flex; justify-content:space-between; font-size:13px; }.checkout-seats span { font-family:'DM Mono',monospace; font-size:10px; color:var(--muted); letter-spacing:.12em; }.total-card { margin-top:.1rem; }.secure-note { color:var(--muted); font-size:10px; line-height:1.55; margin:.75rem 0; }
        .payment-form { margin:1.35rem 0 1rem; }.stRadio > label { color:var(--ink); font-size:12px; font-weight:700; }.stRadio [role="radiogroup"] { gap:1.1rem; }.stRadio label { font-size:12px; }
        .confirmation { text-align:center; max-width:570px; margin:3.6rem auto 1.45rem; }.confirmation-check { width:48px; height:48px; display:flex; align-items:center; justify-content:center; margin:0 auto 1rem; background:#e8f5ef; border-radius:50%; color:var(--green); font-weight:800; font-size:25px; }.confirmation h1 { font-size:42px; margin:.55rem 0 .35rem; font-weight:800; }.confirmation-id { font-family:'DM Mono',monospace; font-size:11px; color:var(--muted); margin-bottom:2.15rem; }.confirmation h2 { font-size:21px; margin:0 0 .3rem; }.confirmation p { color:var(--muted); font-size:13px; line-height:1.65; }.confirmation-grid { border-top:1px solid var(--line); border-bottom:1px solid var(--line); display:grid; grid-template-columns:1fr 1fr; margin:1.8rem 0; padding:1rem 0; }.confirmation-grid div + div { border-left:1px solid var(--line); }.confirmation-grid span,.confirmation-grid b { display:block; }.confirmation-grid b { font-size:14px; margin-top:.4rem; }
        .booking-card { padding:1rem 0; border-top:1px solid var(--line); }.booking-card-copy { padding:.05rem 0; }.booking-event { font-size:18px; font-weight:800; letter-spacing:-.03em; margin:.48rem 0 .4rem; }.booking-meta { color:var(--muted); font-size:12px; line-height:1.75; }.status { display:inline-block; padding:.23rem .48rem; border-radius:999px; font-family:'DM Mono',monospace; font-size:9px; letter-spacing:.06em; }.status.confirmed { color:var(--green); background:#e9f6f0; }.status.completed { color:var(--blue); background:#edf4ff; }.status.cancelled { color:var(--red); background:#fff0f1; }.stTabs [data-baseweb="tab-list"] { gap:1.3rem; border-bottom:1px solid var(--line); }.stTabs [data-baseweb="tab"] { height:44px; padding:0; color:var(--muted); font-weight:700; font-size:12px; }.stTabs [aria-selected="true"] { color:var(--blue) !important; }.stTabs [data-baseweb="tab-highlight"] { background-color:var(--blue); }.empty-state { color:var(--muted); font-size:13px; padding:1.5rem 0; }
        .ticket { border:1px solid var(--line); background:var(--panel); border-radius:12px; padding:1.75rem; }.ticket h1 { font-size:38px; margin:.6rem 0 .7rem; }.ticket-detail { margin-top:1.25rem; }.ticket-detail span,.ticket-detail b { display:block; }.ticket-detail b { font-size:13px; line-height:1.65; margin-top:.35rem; }.ticket-divider { margin:1.6rem 0 1rem; border-top:1px dashed #c4ced9; }.ticket-metric span,.ticket-metric b { display:block; }.ticket-metric b { font-size:14px; margin-top:.42rem; }
        .support-shell { min-height:240px; border:1px solid var(--line); background:var(--panel); border-radius:12px; padding:1rem 1.1rem; margin-bottom:1rem; }.support-welcome { display:flex; align-items:center; gap:.75rem; margin:.35rem 0 1rem; }.support-welcome p { margin:.2rem 0 0; color:var(--muted); font-size:12px; }.support-avatar { display:flex; align-items:center; justify-content:center; width:31px; height:31px; border-radius:50%; color:white; background:var(--blue); font-family:'DM Mono',monospace; font-size:9px; }.stChatMessage { background:transparent !important; }.stChatInput textarea { border-radius:9px !important; border-color:var(--line) !important; }
        .profile-card,.activity-card { min-height:198px; border:1px solid var(--line); border-radius:12px; background:var(--panel); padding:1.5rem; }.avatar { height:43px; width:43px; display:flex; align-items:center; justify-content:center; border-radius:50%; background:#eaf2ff; color:var(--blue); font-weight:800; font-size:12px; }.profile-card h2 { font-size:22px; margin:.9rem 0 .2rem; }.profile-card p { color:var(--muted); font-size:12px; margin:0; }.profile-label { display:block; margin-bottom:.35rem; }.activity-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:.7rem; margin-top:2.2rem; }.activity-grid b,.activity-grid span { display:block; }.activity-grid b { font-size:27px; letter-spacing:-.04em; }.activity-grid span { font-size:10px; color:var(--muted); margin-top:.2rem; }
        .site-footer { margin-top:4rem; padding:1.35rem 0 0; border-top:1px solid var(--line); display:grid; grid-template-columns:1.35fr 1.5fr .8fr; align-items:end; color:var(--muted); }.footer-brand { color:var(--ink); letter-spacing:.08em; font-size:11px; font-weight:800; }.site-footer p { font-size:10px; margin:.34rem 0 0; }.footer-links { display:flex; gap:1rem; font-size:10px; justify-content:center; }.footer-copy { font-size:10px; text-align:right; }
        [data-testid="stForm"] { border:1px solid var(--line); border-radius:12px; background:var(--panel); padding:1.35rem; }.login-shell { margin-top:9vh; text-align:center; }.login-brand { font-size:13px; font-weight:800; letter-spacing:.09em; }.login-title { font-size:37px; margin:.85rem 0 .35rem; letter-spacing:-.055em; }.login-copy { color:var(--muted); font-size:13px; margin-bottom:1.4rem; }.login-hint { margin-top:1rem; color:var(--muted); font-size:10px; }.login-hint b { color:var(--ink-soft); }
        @media (max-width: 760px) { .block-container{padding:1rem 1rem 2rem !important;} .brand{font-size:11px;}.nav-space{height:.7rem}.hero{margin-top:1.55rem}.hero h1{font-size:40px}.page-intro h1{font-size:34px}.detail-summary h1{font-size:37px}.section-head{display:block}.section-head span{display:block;margin-top:.3rem}.editorial-note{display:block}.editorial-note p{margin:.45rem 0}.site-footer{grid-template-columns:1fr;gap:.8rem}.footer-links{justify-content:flex-start}.footer-copy{text-align:left}.seat-area{padding:.9rem .5rem}.summary-card{padding:1rem}.confirmation{margin-top:2.2rem}.ticket{padding:1.15rem}.ticket h1{font-size:31px;} }
        </style>"""
DARK_CSS = r"""<style>
/* FlashReserve dark theme overrides */
:root {
  --ink:#f4f1ea;
  --ink-soft:#c7cbd3;
  --blue:#d7a85f;
  --blue-dark:#b98a46;
  --paper:#111318;
  --panel:#1b1f28;
  --mist:#222733;
  --line:#303746;
  --muted:#8e96a5;
  --green:#77c8a3;
  --amber:#e8b36b;
  --red:#f08c88;
}
html, body, [class*="css"] { color:var(--ink) !important; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background:var(--paper) !important; }
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer { display:none !important; }
.brand, .footer-brand, .login-brand { color:var(--ink) !important; }
.brand-mark { background:var(--blue) !important; }
.brand-mark:after { background:var(--paper) !important; }
.stButton > button { color:var(--ink) !important; background:var(--panel) !important; border-color:var(--line) !important; }
.stButton > button:hover { color:#f1c98d !important; border-color:var(--blue) !important; background:#222733 !important; }
.stButton > button[kind="primary"], button[data-testid^="stBaseButton-primary"] { color:#17130d !important; background:var(--blue) !important; border-color:var(--blue) !important; }
.stButton > button[kind="primary"]:hover, button[data-testid^="stBaseButton-primary"]:hover { background:#e8bd79 !important; border-color:#e8bd79 !important; }
.stButton > button:disabled { color:#747b88 !important; background:#20242c !important; border-color:#2c313c !important; }
.stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input, .stTimeInput input,
.stSelectbox [data-baseweb="select"] > div, [data-testid="stFileUploaderDropzone"] {
  color:var(--ink) !important; background:var(--panel) !important; border-color:var(--line) !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color:var(--muted) !important; }
.stTextInput label, .stTextArea label, .stNumberInput label, .stDateInput label, .stTimeInput label,
.stSelectbox label, .stFileUploader label, .stRadio label { color:var(--ink-soft) !important; }
[data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] { background:#222733 !important; color:var(--ink) !important; }
[role="option"] { color:var(--ink) !important; }
[role="option"]:hover { background:var(--line) !important; }
[data-testid="stForm"] { background:var(--panel) !important; border-color:var(--line) !important; box-shadow:0 18px 45px rgba(0,0,0,.35) !important; }
.hero h1, .page-intro h1, .detail-summary h1, .detail-summary h2, .content-section h2,
.section-head h2, .event-title, .summary-card h3, .booking-event, .ticket h1, .profile-card h2 { color:var(--ink) !important; }
.hero p, .page-intro p, .event-meta, .event-card-bottom, .section-head span, .venue-line,
.content-section p, .booking-meta, .secure-note, .empty-state, .profile-card p, .activity-grid span,
.confirmation p, .confirmation-id, .support-welcome p { color:var(--muted) !important; }
.eyebrow, .section-kicker, .filter-label, .event-category { color:#e8bd79 !important; }
.event-card { background:var(--panel) !important; border-color:var(--line) !important; box-shadow:0 12px 28px rgba(0,0,0,.22) !important; }
.event-card:hover { border-color:var(--blue) !important; box-shadow:0 20px 38px rgba(0,0,0,.32) !important; }
[data-testid="stImage"] img { background:#222733 !important; }
.editorial-note, .detail-rule, .ticket-divider { border-color:var(--line) !important; }
.seat-area, .summary-card, .ticket, .profile-card, .activity-card, .support-shell {
  background:var(--panel) !important; border-color:var(--line) !important; box-shadow:0 15px 34px rgba(0,0,0,.25) !important;
}
.screen-label, .row-label, .seat-legend { color:var(--muted) !important; }
.screen-line { background:var(--blue) !important; opacity:.7; }
.seat-swatch.available { border-color:var(--ink-soft) !important; }
.seat-swatch.selected { background:var(--blue) !important; }
.seat-swatch.reserved { background:var(--amber) !important; }
.seat-swatch.sold { background:#7b4a4c !important; }
.summary-line, .checkout-event p, .booking-meta { color:var(--muted) !important; }
.summary-line b, .summary-card h3, .booking-event, .detail-key b, .info-list b, .ticket-detail b, .ticket-metric b { color:var(--ink) !important; }
.summary-total strong { color:#e8bd79 !important; }
.status.confirmed { color:var(--green) !important; background:rgba(119,200,163,.14) !important; }
.status.completed { color:#e8bd79 !important; background:rgba(215,168,95,.14) !important; }
.status.cancelled { color:var(--red) !important; background:rgba(240,140,136,.14) !important; }
.confirmation-check { background:rgba(119,200,163,.15) !important; color:var(--green) !important; }
.support-shell { background:var(--panel) !important; }
.stChatMessage { background:var(--panel) !important; border-color:var(--line) !important; }
.stChatInput textarea { background:var(--panel) !important; color:var(--ink) !important; border-color:var(--line) !important; }
.avatar { background:#252b38 !important; color:#e8bd79 !important; }
[data-testid="stMetric"] { background:var(--panel) !important; border-color:var(--line) !important; box-shadow:0 15px 34px rgba(0,0,0,.25) !important; }
[data-testid="stMetricLabel"] p { color:var(--muted) !important; }
[data-testid="stMetricValue"] { color:#e8bd79 !important; }
[data-testid="stDataFrame"] { border-color:var(--line) !important; }
[data-testid="stDataFrame"] * { color:var(--ink) !important; }
[data-baseweb="tab"] p, [data-baseweb="tab"] { color:var(--muted) !important; }
[data-baseweb="tab"][aria-selected="true"] p, [data-baseweb="tab"][aria-selected="true"] { color:#e8bd79 !important; }
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] b,
[data-testid="stMarkdownContainer"] strong { color:var(--ink); }
[data-testid="stMarkdownContainer"] .eyebrow,
[data-testid="stMarkdownContainer"] .section-kicker,
[data-testid="stMarkdownContainer"] .filter-label,
[data-testid="stMarkdownContainer"] .event-category { color:#e8bd79 !important; }
[data-testid="stMarkdownContainer"] .event-meta,
[data-testid="stMarkdownContainer"] .event-card-bottom,
[data-testid="stMarkdownContainer"] .page-intro p,
[data-testid="stMarkdownContainer"] .hero p,
[data-testid="stMarkdownContainer"] .venue-line,
[data-testid="stMarkdownContainer"] .confirmation-id,
[data-testid="stMarkdownContainer"] .booking-meta { color:var(--muted) !important; }
.breadcrumb { color:var(--muted) !important; }
.breadcrumb span { color:var(--blue) !important; }
.login-shell { background:rgba(27,31,40,.96) !important; border-color:var(--line) !important; box-shadow:0 24px 70px rgba(0,0,0,.4) !important; }
.login-shell .login-title, .login-shell .login-copy, .login-shell .login-hint { color:var(--ink) !important; }
.login-shell .login-copy, .login-shell .login-hint { color:var(--muted) !important; }
.stAlert { background:var(--panel) !important; border-color:var(--line) !important; color:var(--ink) !important; }
/* compact poster sizing */
[data-testid="stImage"] img { max-height:230px !important; object-fit:cover !important; }
.poster-fallback { background:radial-gradient(circle at 80% 15%, rgba(215,168,95,.28), transparent 34%), linear-gradient(145deg,#252b38,#151820 72%) !important; border-color:#3b4352 !important; }
</style>"""
LIGHT_ADDITIONS = r"""<style>
/* FlashReserve light theme additions */
[data-testid="stImage"] img { max-height:230px !important; object-fit:cover !important; }
.poster-fallback { max-height:230px; }
.theme-toggle-wrap .stButton > button { min-width:88px !important; }
</style>"""


def inject_theme_styles():
    """Apply the sample frontend design with a session-controlled light/dark theme."""
    st.markdown(LIGHT_CSS, unsafe_allow_html=True)
    st.markdown(LIGHT_ADDITIONS, unsafe_allow_html=True)
    if st.session_state.get("theme", "light") == "dark":
        st.markdown(DARK_CSS, unsafe_allow_html=True)


def inject_admin_styles():
    """Keep the admin area consistent with the selected theme."""
    dark = st.session_state.get("theme", "light") == "dark"
    if dark:
        st.markdown("""
        <style>
        .stApp { background:#111318 !important; }
        .admin-brand, [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] p { color:#f4f1ea !important; }
        .admin-brand small { color:#e8bd79 !important; }
        .admin-rule { background:#303746 !important; }
        [data-testid="stSidebar"] { background:#0c0e12 !important; border-right:1px solid #303746; }
        [data-testid="stSidebar"] * { color:#c4c8d1 !important; }
        [data-testid="stSidebar"] .stButton > button { background:transparent !important; color:#c4c8d1 !important; border-color:#303746 !important; }
        [data-testid="stSidebar"] .stButton > button:hover { background:#1b1f28 !important; color:#e8bd79 !important; }
        [data-testid="stSidebar"] .stButton > button[kind="primary"] { background:#d7a85f !important; color:#17130d !important; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stApp { background:#eef3f8; }
        .admin-brand { padding-top:.55rem; color:#13253f; }
        .admin-brand small { color:#1769e0; font-family:'DM Mono',monospace; font-size:9px; letter-spacing:.14em; margin-left:.35rem; }
        .admin-rule { height:1px; background:#dce3ea; margin:.65rem 0 1.4rem; }
        [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] p { color:#13253f !important; }
        [data-testid="stSidebar"] { background:#13253f; border-right:0; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color:#f7fbff !important; }
        [data-testid="stSidebar"] .stButton > button { color:#e8f0f8; border-color:rgba(255,255,255,.16); background:transparent; text-align:left; }
        [data-testid="stSidebar"] .stButton > button:hover { color:#fff; border-color:#6ca9ff; background:rgba(255,255,255,.08); }
        [data-testid="stSidebar"] .stButton > button[kind="primary"] { color:#fff; background:#1769e0; border-color:#1769e0; }
        </style>
        """, unsafe_allow_html=True)
