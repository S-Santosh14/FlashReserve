import streamlit as st


def inject_premium_styles():
    st.markdown(
        """
        <style>
        :root {
          color-scheme: dark;
          --bg: #0a0c11;
          --bg-glow: #111722;
          --surface: #11151d;
          --surface-raised: #191f29;
          --surface-soft: #222b38;
          --line: #2a3340;
          --line-strong: #3b4655;
          --text: #f5f3ee;
          --text-soft: #c5cbd3;
          --muted: #9aa4b1;
          --accent: #e8ad72;
          --accent-bright: #ffd09c;
          --accent-ink: #21150c;
          --violet: #aaa1ff;
          --success: #77d1ad;
          --warning: #f2c079;
          --danger: #f18e8a;
          --font-body: "DM Sans", "Segoe UI", Arial, sans-serif;
          --font-heading: "Manrope", "DM Sans", "Segoe UI", Arial, sans-serif;
          --shadow: 0 22px 65px rgba(0, 0, 0, .28);
          --radius: 18px;
        }

        *, *::before, *::after { box-sizing: border-box; }
        html, body {
          max-width: 100%;
          overflow-x: hidden;
          background: var(--bg);
        }
        body, .stApp {
          color: var(--text) !important;
          font-family: var(--font-body);
          line-height: 1.55;
        }
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
          background:
            radial-gradient(ellipse at 82% -18%, rgba(170, 161, 255, .08), transparent 34%),
            radial-gradient(ellipse at 6% 6%, rgba(232, 173, 114, .075), transparent 28%),
            var(--bg) !important;
          min-width: 0;
          overflow-x: clip;
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer {
          display: none !important;
        }
        .block-container {
          max-width: 1320px;
          padding: 1.65rem 2.4rem 4rem !important;
          animation: page-enter .35s ease-out both;
        }
        @keyframes page-enter {
          from { opacity: 0; transform: translateY(7px); }
          to { opacity: 1; transform: translateY(0); }
        }
        h1, h2, h3, h4 {
          color: var(--text) !important;
          font-family: var(--font-heading);
          letter-spacing: -.035em;
        }
        h1 { line-height: 1.04; }
        p, li { color: var(--text-soft); }
        a { color: var(--accent-bright); }
        ::selection { color: var(--accent-ink); background: var(--accent-bright); }
        :focus-visible { outline: 2px solid var(--accent-bright) !important; outline-offset: 3px; }

        .brand, .footer-brand, .login-brand {
          color: var(--text) !important;
          font-size: .88rem;
          font-weight: 850;
          letter-spacing: .11em;
          white-space: nowrap;
        }
        .brand-mark {
          display: inline-block;
          width: 14px;
          height: 14px;
          margin: 0 9px -2px 0;
          position: relative;
          transform: rotate(45deg);
          border-radius: 4px;
          background: linear-gradient(135deg, var(--accent-bright), #d47c4d) !important;
          box-shadow: 0 0 22px rgba(229, 164, 100, .26);
        }
        .brand-mark::after {
          content: "";
          position: absolute;
          inset: 4px;
          border-radius: 50%;
          background: var(--bg) !important;
        }
        .nav-rule, .admin-rule {
          height: 1px;
          background: linear-gradient(90deg, transparent, var(--line-strong), transparent) !important;
          margin: .2rem 0 1.25rem;
        }
        .nav-space { height: .7rem; }
        .admin-brand small { color: var(--accent-bright) !important; letter-spacing: .15em; }
        .st-key-main-navigation, .st-key-admin-header { gap: .45rem; }

        .stButton > button,
        .stLinkButton > a,
        [data-testid="stFormSubmitButton"] button {
          min-height: 42px;
          border: 1px solid var(--line-strong) !important;
          border-radius: 11px !important;
          background: #252b35 !important;
          color: #f1eee8 !important;
          -webkit-text-fill-color: currentColor !important;
          opacity: 1 !important;
          font-weight: 650;
          transition: color .16s ease, box-shadow .16s ease, border-color .16s ease, background-color .16s ease !important;
        }
        .stButton > button *,
        .stLinkButton > a *,
        [data-testid="stFormSubmitButton"] button * {
          color: inherit !important;
          -webkit-text-fill-color: currentColor !important;
          opacity: 1 !important;
        }
        .stButton > button svg,
        .stLinkButton > a svg,
        [data-testid="stFormSubmitButton"] button svg {
          color: inherit !important;
          fill: currentColor !important;
        }
        .stButton > button:hover:not(:disabled),
        .stLinkButton > a:hover,
        [data-testid="stFormSubmitButton"] button:hover:not(:disabled) {
          background: #303741 !important;
          color: #f5f1e9 !important;
          border-color: #82705f !important;
          box-shadow: 0 4px 12px rgba(0, 0, 0, .18);
        }
        .stButton > button:active:not(:disabled),
        .stLinkButton > a:active,
        [data-testid="stFormSubmitButton"] button:active:not(:disabled) {
          background: #202630 !important;
          color: #f5f1e9 !important;
          border-color: #8d7965 !important;
          box-shadow: inset 0 1px 3px rgba(0, 0, 0, .2);
        }
        .stButton > button:focus-visible,
        .stLinkButton > a:focus-visible,
        [data-testid="stFormSubmitButton"] button:focus-visible,
        .st-key-mode_selector_main [role="radio"]:focus-visible {
          outline: 2px solid #edbd91 !important;
          outline-offset: 2px;
          box-shadow: 0 0 0 4px rgba(232, 173, 114, .18);
        }
        .stButton > button[kind="primary"],
        .stButton > button[data-testid^="stBaseButton-primary"],
        [data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"],
        [data-testid="stFormSubmitButton"] button[kind="primary"] {
          background: #d7a071 !important;
          color: #28190f !important;
          border-color: #c99265 !important;
          box-shadow: 0 3px 10px rgba(215, 160, 113, .12);
        }
        .stButton > button[kind="primary"]:hover:not(:disabled),
        .stButton > button[data-testid^="stBaseButton-primary"]:hover:not(:disabled),
        [data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"]:hover:not(:disabled),
        [data-testid="stFormSubmitButton"] button[kind="primary"]:hover:not(:disabled) {
          background: #ce9568 !important;
          color: #24160d !important;
          border-color: #bf895e !important;
          box-shadow: 0 4px 12px rgba(215, 160, 113, .16);
        }
        .stButton > button[kind="primary"]:active:not(:disabled),
        .stButton > button[data-testid^="stBaseButton-primary"]:active:not(:disabled),
        [data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"]:active:not(:disabled),
        [data-testid="stFormSubmitButton"] button[kind="primary"]:active:not(:disabled) {
          background: #c48859 !important;
          color: #21140c !important;
          border-color: #b77c50 !important;
          box-shadow: inset 0 1px 3px rgba(67, 38, 19, .2);
        }
        .stButton > button:disabled,
        .stLinkButton > a[aria-disabled="true"],
        [data-testid="stFormSubmitButton"] button:disabled {
          background: #302d2a !important;
          color: #d2c2b0 !important;
          border-color: #51463c !important;
          -webkit-text-fill-color: currentColor !important;
          opacity: 1 !important;
          box-shadow: none !important;
          transition: none !important;
          cursor: not-allowed;
        }
        .stButton > button[kind="primary"]:disabled,
        .stButton > button[data-testid^="stBaseButton-primary"]:disabled,
        [data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"]:disabled,
        [data-testid="stFormSubmitButton"] button[kind="primary"]:disabled {
          background: #b58a66 !important;
          color: #2b1d13 !important;
          border-color: #9e7757 !important;
          -webkit-text-fill-color: currentColor !important;
          opacity: 1 !important;
          transition: none !important;
        }
        .st-key-mode_selector_main [role="radio"] {
          background: #252b35 !important;
          color: #f1eee8 !important;
          -webkit-text-fill-color: currentColor !important;
          opacity: 1 !important;
          transition: color .16s ease, box-shadow .16s ease, border-color .16s ease, background-color .16s ease !important;
        }
        .st-key-mode_selector_main [role="radio"]:hover:not(:disabled):not([aria-checked="true"]) {
          background: #303741 !important;
          color: #f5f1e9 !important;
          border-color: #82705f !important;
        }
        .st-key-mode_selector_main [role="radio"][aria-checked="true"] {
          background: #d7a071 !important;
          color: #28190f !important;
          border-color: #c99265 !important;
        }
        .st-key-mode_selector_main [role="radio"][aria-checked="true"]:hover {
          background: #ce9568 !important;
          color: #24160d !important;
          border-color: #bf895e !important;
        }
        .st-key-mode_selector_main [role="radio"]:disabled {
          background: #302d2a !important;
          color: #d2c2b0 !important;
          -webkit-text-fill-color: currentColor !important;
          opacity: 1 !important;
          transition: none !important;
        }
        .st-key-mode_selector_main [role="radio"] * {
          color: inherit !important;
          -webkit-text-fill-color: currentColor !important;
          opacity: 1 !important;
        }

        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input,
        [data-testid="stTimeInput"] input,
        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
        [data-testid="stFileUploaderDropzone"],
        [data-testid="stChatInput"] {
          color: var(--text) !important;
          background: var(--surface) !important;
          border: 1px solid var(--line-strong) !important;
          border-radius: 11px !important;
          box-shadow: none !important;
        }
        [data-testid="stTextInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus,
        [data-testid="stNumberInput"] input:focus {
          border-color: var(--accent) !important;
          box-shadow: 0 0 0 3px rgba(229, 164, 100, .13) !important;
        }
        [data-testid="stTextInput"] input::placeholder,
        [data-testid="stTextArea"] textarea::placeholder { color: #778091 !important; }
        [data-testid="stTextInput"] label,
        [data-testid="stTextArea"] label,
        [data-testid="stNumberInput"] label,
        [data-testid="stDateInput"] label,
        [data-testid="stTimeInput"] label,
        [data-testid="stSelectbox"] label,
        [data-testid="stMultiSelect"] label,
        [data-testid="stFileUploader"] label,
        [data-testid="stRadio"] label,
        [data-testid="stCheckbox"] label { color: var(--text-soft) !important; }
        [data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] {
          color: var(--text) !important;
          background: var(--surface-raised) !important;
          border: 1px solid var(--line-strong) !important;
        }
        [role="option"] { color: var(--text) !important; }
        [role="option"]:hover { background: var(--surface-soft) !important; }

        [data-testid="stForm"] {
          padding: 1.25rem !important;
          border: 1px solid var(--line) !important;
          border-radius: var(--radius) !important;
          background: linear-gradient(145deg, rgba(27, 31, 43, .96), rgba(20, 23, 33, .96)) !important;
          box-shadow: var(--shadow);
        }
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
          gap: .6rem;
          background: transparent;
          border-bottom: 1px solid var(--line);
        }
        [data-baseweb="tab"] { color: var(--muted) !important; }
        [data-baseweb="tab"][aria-selected="true"] { color: var(--accent-bright) !important; }
        [data-testid="stTabs"] [data-baseweb="tab-highlight"] { background: var(--accent) !important; }
        [data-testid="stAlert"], [data-testid="stStatusWidget"] {
          color: var(--text) !important;
          background: var(--surface-raised) !important;
          border: 1px solid var(--line-strong) !important;
          border-radius: 13px !important;
        }
        [data-testid="stCaptionContainer"] p { color: var(--muted) !important; }

        .hero {
          max-width: 900px;
          margin: 2.8rem auto 1.55rem !important;
          text-align: center;
        }
        .home-hero { max-width: 980px; margin-top: 2rem !important; }
        .home-hero h1 { font-family: var(--font-heading); }
        .home-hero p { font-size: 1.02rem; }
        .eyebrow, .section-kicker, .filter-label, .event-category {
          color: var(--accent-bright) !important;
          font-size: .67rem;
          font-weight: 700;
          letter-spacing: .17em;
          text-transform: uppercase;
        }
        .hero h1 {
          margin: .65rem 0 .9rem;
          font-size: clamp(2.7rem, 7vw, 5.6rem) !important;
          font-weight: 850;
          line-height: .98;
          letter-spacing: -.07em !important;
        }
        .hero h1 em {
          color: var(--accent-bright) !important;
          font-style: normal;
          background: linear-gradient(100deg, #f8d19b, #d98e61 65%, #b4aaff);
          background-clip: text;
          -webkit-text-fill-color: transparent;
        }
        .hero p {
          max-width: 610px;
          margin: 0 auto;
          color: var(--text-soft) !important;
          font-size: 1rem;
          line-height: 1.75;
        }
        .section-head {
          display: flex;
          align-items: baseline;
          justify-content: space-between;
          gap: 1rem;
          margin: 2.4rem 0 1rem;
        }
        .section-head h2 { margin: 0; font-size: 1.35rem; font-weight: 780; }
        .section-head span, .event-meta, .event-card-bottom { color: var(--text-soft) !important; }
        .section-head span { font-size: .78rem; }
        .section-spacer { height: 1.7rem; }
        [class*="st-key-event-card-"] {
          height: 100%;
          margin-bottom: 1.1rem;
          padding: .7rem;
          overflow: hidden;
          border: 1px solid var(--line);
          border-radius: var(--radius);
          background: linear-gradient(155deg, rgba(31, 35, 48, .98), rgba(19, 22, 31, .98));
          box-shadow: 0 14px 36px rgba(0, 0, 0, .17);
          transition: transform .22s ease, border-color .22s ease, box-shadow .22s ease;
        }
        [class*="st-key-event-card-"]:hover {
          transform: translateY(-5px);
          border-color: rgba(229, 164, 100, .7);
          box-shadow: 0 22px 48px rgba(0, 0, 0, .3);
        }
        .event-card-copy { padding: .95rem .35rem .65rem !important; }
        .event-title {
          margin: .4rem 0 .35rem;
          color: var(--text) !important;
          font-size: 1.08rem;
          font-weight: 780;
          letter-spacing: -.025em;
        }
        .event-meta { font-size: .77rem; line-height: 1.6; }
        .event-card-bottom { margin-top: .75rem; font-size: .78rem; }
        .event-card-bottom b, .summary-total strong { color: var(--accent-bright) !important; }
        [data-testid="stImage"] img {
          max-width: 100%;
          width: 100%;
          height: auto;
          border: 1px solid rgba(255,255,255,.045);
          border-radius: 13px !important;
          background: var(--surface-raised);
          object-fit: cover;
        }
        [class*="st-key-event-poster-card-"] [data-testid="stImage"] img,
        [class*="st-key-event-poster-card-"] .poster-fallback { aspect-ratio: 2 / 3; }
        [class*="st-key-event-poster-hero-"] [data-testid="stImage"] img,
        [class*="st-key-event-poster-hero-"] .poster-fallback { aspect-ratio: 16 / 9; }
        [class*="st-key-event-poster-compact-"] [data-testid="stImage"] img,
        [class*="st-key-event-poster-compact-"] .poster-fallback { aspect-ratio: 4 / 3; }
        .poster-fallback {
          min-height: 170px;
          height: 100%;
          padding: 1.3rem;
          display: flex;
          flex-direction: column;
          justify-content: flex-end;
          gap: .5rem;
          overflow: hidden;
          border: 1px solid var(--line-strong);
          border-radius: 13px;
          background:
            radial-gradient(circle at 82% 12%, rgba(229,164,100,.32), transparent 34%),
            radial-gradient(circle at 15% 50%, rgba(156,146,255,.2), transparent 45%),
            linear-gradient(145deg, #252b3a, #11131a 75%);
        }
        .poster-fallback span { color: var(--accent-bright) !important; font-size: .65rem; letter-spacing: .16em; }
        .poster-fallback strong { color: var(--text) !important; font-size: 1.35rem; line-height: 1.1; }
        .poster-fallback small { color: var(--muted) !important; font-size: .6rem; letter-spacing: .1em; }
        .editorial-note {
          display: flex;
          align-items: baseline;
          gap: 1.1rem;
          margin: 3rem 0 1rem;
          padding: 1.15rem 1.3rem;
          border: 1px solid var(--line);
          border-radius: 14px;
          background: linear-gradient(100deg, rgba(229,164,100,.08), rgba(156,146,255,.05));
        }
        .editorial-note span { color: var(--accent-bright) !important; font-size: .65rem; font-weight: 700; letter-spacing: .13em; }
        .editorial-note p { margin: 0; color: var(--text) !important; font-weight: 750; }
        .editorial-note small { color: var(--muted) !important; }
        .st-key-home-featured {
          margin: 1.5rem 0 2.2rem;
          padding: clamp(1rem, 2.5vw, 1.8rem);
          border-color: var(--line-strong) !important;
          border-radius: 22px !important;
          background:
            radial-gradient(ellipse at 100% 0, rgba(170,161,255,.09), transparent 38%),
            linear-gradient(140deg, #171d27, #10141b 78%) !important;
          box-shadow: var(--shadow);
        }
        .st-key-home-featured [data-testid="stImage"] img {
          aspect-ratio: 16 / 9;
          object-fit: cover;
          border-radius: 15px !important;
        }
        .home-featured-copy { padding: .45rem .25rem; }
        .home-featured-copy .section-kicker { margin-bottom: .85rem; }
        .home-featured-copy .event-category { display: block; margin-bottom: .35rem; }
        .home-featured-copy h2 {
          margin: .25rem 0 .65rem;
          font-size: clamp(1.7rem, 3.4vw, 2.8rem);
          line-height: 1.08;
        }
        .home-featured-copy p {
          color: var(--text-soft) !important;
          font-size: .9rem;
          line-height: 1.8;
        }
        .home-featured-price {
          margin: 1rem 0 1.15rem;
          color: var(--muted) !important;
          font-size: .78rem;
        }
        .home-featured-price strong {
          margin-left: .35rem;
          color: var(--accent-bright) !important;
          font-size: 1.15rem;
        }
        .home-empty { margin: 1.5rem 0 2rem; }

        .page-intro { margin: 1.65rem 0 1.35rem !important; }
        .page-intro h1 {
          margin: .45rem 0 .45rem !important;
          font-size: clamp(2.1rem, 4vw, 3.6rem) !important;
          font-weight: 830;
          letter-spacing: -.06em !important;
        }
        .page-intro p { margin: 0; color: var(--text-soft) !important; font-size: .93rem; }
        .breadcrumb { margin: -.25rem 0 1rem; color: var(--muted) !important; font-size: .72rem; }
        .breadcrumb span { padding: 0 .4rem; color: var(--accent) !important; }
        .location-pill { padding-top: .7rem; color: var(--text-soft) !important; font-size: .8rem; font-weight: 650; }
        .filter-label { margin: 1.25rem 0 .5rem; }
        .result-count { margin: 1.2rem 0 .85rem; color: var(--muted) !important; font-size: .78rem; }
        .empty-state {
          margin: .7rem 0;
          padding: 1.25rem;
          border: 1px dashed var(--line-strong);
          border-radius: 13px;
          background: rgba(255,255,255,.015);
          color: var(--text-soft) !important;
          text-align: center;
        }
        .detail-summary { padding: .5rem .2rem 0; }
        .detail-summary h1, .detail-summary h2 { margin: .55rem 0 .5rem; font-size: clamp(2.1rem, 4vw, 3.2rem) !important; }
        .venue-line { color: var(--text-soft) !important; line-height: 1.65; }
        .detail-rule { height: 1px; margin: 1.2rem 0 1rem; background: var(--line); }
        .detail-key, .info-list > div:not(.section-kicker) {
          display: flex;
          justify-content: space-between;
          gap: 1rem;
          padding: .72rem 0;
          border-bottom: 1px solid var(--line);
          font-size: .82rem;
        }
        .detail-key span, .info-list span, .ticket-detail span, .ticket-metric span,
        .confirmation-grid span, .profile-label {
          color: var(--muted) !important;
          font-size: .65rem;
          font-weight: 650;
          letter-spacing: .12em;
          text-transform: uppercase;
        }
        .detail-key b, .info-list b { color: var(--text) !important; text-align: right; line-height: 1.55; }
        .content-section { padding-top: 2.4rem; }
        .content-section h2 { margin: .5rem 0 .65rem; font-size: 1.55rem; }
        .content-section p { max-width: 680px; color: var(--text-soft) !important; font-size: .92rem; line-height: 1.9; }
        .info-list { padding-top: 2.2rem; }

        .seat-area, .summary-card, .ticket, .profile-card, .activity-card, .support-shell {
          border: 1px solid var(--line) !important;
          border-radius: var(--radius) !important;
          background: linear-gradient(155deg, var(--surface-raised), var(--surface)) !important;
          box-shadow: 0 16px 38px rgba(0, 0, 0, .18);
        }
        .seat-area { padding: 1.35rem 1.2rem .8rem; }
        .screen-label, .row-label, .seat-legend, .secure-note { color: var(--text-soft) !important; }
        .screen-label { text-align: center; font-size: .65rem; font-weight: 700; letter-spacing: .2em; }
        .screen-line {
          width: 66%;
          height: 4px;
          margin: .55rem auto 1.8rem;
          border-radius: 50%;
          background: linear-gradient(90deg, transparent, var(--accent), var(--violet), transparent) !important;
          box-shadow: 0 5px 22px rgba(229,164,100,.2);
        }
        .row-label { padding-top: .6rem; color: var(--accent-bright) !important; font-size: .7rem; font-weight: 700; }
        .st-key-seat-map { border-color: var(--line) !important; border-radius: var(--radius) !important; background: var(--surface) !important; }
        .st-key-seat-map .stButton > button {
          min-width: 2.55rem;
          min-height: 2.35rem;
          padding: .25rem .4rem;
          border-radius: 8px !important;
          font-family: "Segoe UI", Arial, sans-serif;
          font-size: .72rem;
          font-weight: 700;
        }
        .st-key-seat-map .stButton > button[kind="primary"] {
          color: #28190f !important;
          background: #d7a071 !important;
          border-color: #c99265 !important;
          box-shadow: 0 0 0 3px rgba(215,160,113,.12);
        }
        .st-key-seat-map [class*="st-key-seat-reserved"] .stButton > button:disabled {
          color: var(--warning) !important; background: #403522 !important; border-color: #705b37 !important; opacity: 1;
        }
        .st-key-seat-map [class*="st-key-seat-booked"] .stButton > button:disabled {
          color: #e29a98 !important; background: #40282d !important; border-color: #694047 !important; opacity: 1;
        }
        .st-key-seat-map [class*="st-key-seat-row"] { overflow-x: auto; scrollbar-color: var(--line-strong) transparent; }
        .st-key-seat-map [class*="st-key-seat-row"] .row-label {
          position: sticky; left: 0; z-index: 1; min-width: 2rem; padding: .35rem .25rem; background: var(--surface);
        }
        .st-key-seat-summary { position: sticky; top: 1rem; align-self: flex-start; }
        .seat-legend { display: flex; flex-wrap: wrap; gap: 1rem; margin: .95rem .15rem .1rem; font-size: .72rem; }
        .seat-legend span { display: flex; align-items: center; gap: .35rem; }
        .seat-swatch { display: inline-block; width: 11px; height: 11px; border-radius: 4px; }
        .seat-swatch.available { border: 1px solid var(--text-soft); }
        .seat-swatch.selected { background: var(--accent); }
        .seat-swatch.reserved { background: var(--warning); }
        .seat-swatch.sold { background: #754248; }
        .summary-card { padding: 1.35rem; }
        .summary-card h3 { margin: .58rem 0 1rem; color: var(--text) !important; font-size: 1.05rem; }
        .summary-line { display: flex; justify-content: space-between; align-items: flex-start; gap: .8rem; padding: .62rem 0; color: var(--text-soft) !important; font-size: .8rem; }
        .summary-line b { color: var(--text) !important; text-align: right; }
        .summary-total { display: flex; justify-content: space-between; align-items: center; padding-top: 1rem; margin-top: .55rem; border-top: 1px solid var(--line); font-size: .8rem; }
        .summary-total strong { font-size: 1.2rem; }
        .checkout-event { padding: 1.25rem 0; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
        .checkout-event h2 { margin: .45rem 0; font-size: 1.7rem; }
        .checkout-event p { color: var(--text-soft) !important; font-size: .86rem; line-height: 1.75; }
        .checkout-seats { display: flex; justify-content: space-between; gap: 1rem; font-size: .85rem; }
        .checkout-seats span { color: var(--muted) !important; font-size: .66rem; letter-spacing: .13em; }
        .secure-note { font-size: .73rem; line-height: 1.6; }
        .payment-form { margin: 1.1rem 0; }
        .confirmation {
          max-width: 650px;
          margin: 2.5rem auto 1.4rem;
          padding: 2rem;
          border: 1px solid var(--line);
          border-radius: 22px;
          background: radial-gradient(circle at 50% 0, rgba(119,209,173,.1), transparent 38%), var(--surface);
          box-shadow: var(--shadow);
          text-align: center;
        }
        .st-key-confirmation-ticket {
          margin: 1.5rem auto;
          padding: clamp(.8rem, 2vw, 1.5rem);
          border-color: var(--line-strong) !important;
          border-radius: 22px !important;
          background:
            radial-gradient(ellipse at 80% 0, rgba(119,209,173,.075), transparent 38%),
            linear-gradient(145deg, var(--surface-raised), var(--surface)) !important;
          box-shadow: var(--shadow);
        }
        .st-key-confirmation-ticket [data-testid="stImage"] img {
          aspect-ratio: 4 / 3;
          object-fit: cover;
          border-radius: 14px !important;
        }
        .st-key-confirmation-ticket .confirmation {
          max-width: none;
          margin: 0;
          padding: .65rem;
          border: 0;
          background: transparent;
          box-shadow: none;
          text-align: left;
        }
        .st-key-confirmation-ticket .confirmation-check { margin-left: 0; }
        .st-key-confirmation-ticket .confirmation-grid { max-width: 440px; }
        .confirmation-check {
          display: grid;
          place-items: center;
          width: 56px;
          height: 56px;
          margin: 0 auto 1rem;
          border: 1px solid rgba(119,209,173,.35);
          border-radius: 50%;
          background: rgba(119,209,173,.13) !important;
          color: var(--success) !important;
          font-size: 1.6rem;
          animation: success-pop .42s cubic-bezier(.2,.8,.2,1.3) both;
        }
        @keyframes success-pop { from { opacity: 0; transform: scale(.75); } to { opacity: 1; transform: scale(1); } }
        .confirmation h2 { margin: .7rem 0 .35rem; font-size: 1.35rem; }
        .confirmation p, .confirmation-id { color: var(--text-soft) !important; font-size: .82rem; line-height: 1.65; }
        .confirmation-id { margin-bottom: 1.3rem; font-family: "Segoe UI", Arial, sans-serif; }
        .confirmation-grid {
          display: grid; grid-template-columns: 1fr 1fr; margin: 1.5rem 0; padding: 1rem 0;
          border-top: 1px solid var(--line); border-bottom: 1px solid var(--line);
        }
        .confirmation-grid div + div { border-left: 1px solid var(--line); }
        .confirmation-grid span, .confirmation-grid b { display: block; }
        .confirmation-grid b { margin-top: .45rem; color: var(--text) !important; }

        .booking-card { margin: .5rem 0; padding: 1rem; border: 1px solid var(--line); border-radius: var(--radius); background: var(--surface); }
        .booking-event { margin: .5rem 0 .4rem; color: var(--text) !important; font-size: 1.1rem; font-weight: 780; }
        .booking-meta { color: var(--text-soft) !important; font-size: .78rem; line-height: 1.8; }
        .status { display: inline-block; padding: .28rem .58rem; border-radius: 999px; font-size: .66rem; font-weight: 700; letter-spacing: .05em; }
        .status.confirmed { color: var(--success) !important; background: rgba(119,209,173,.13) !important; }
        .status.pending { color: var(--warning) !important; background: rgba(242,192,121,.13) !important; }
        .status.completed { color: var(--accent-bright) !important; background: rgba(229,164,100,.13) !important; }
        .status.cancelled, .status.failed, .status.expired { color: var(--danger) !important; background: rgba(241,142,138,.13) !important; }
        .ticket { padding: 1.7rem; }
        .ticket h1 { font-size: 2.4rem; }
        .ticket-detail { margin-top: 1.15rem; }
        .ticket-detail span, .ticket-detail b, .ticket-metric span, .ticket-metric b { display: block; }
        .ticket-detail b, .ticket-metric b { margin-top: .4rem; color: var(--text) !important; font-size: .9rem; line-height: 1.65; }
        .ticket-divider { margin: 1.5rem 0 1rem; border-top: 1px dashed var(--line-strong); }

        [data-testid="stMetric"] {
          min-height: 105px;
          padding: 1rem 1.1rem;
          border: 1px solid var(--line) !important;
          border-radius: 16px !important;
          background: linear-gradient(145deg, var(--surface-raised), var(--surface)) !important;
          box-shadow: 0 12px 30px rgba(0,0,0,.15);
        }
        [data-testid="stMetricLabel"] p { color: var(--muted) !important; font-size: .67rem; font-weight: 650; letter-spacing: .1em; text-transform: uppercase; }
        [data-testid="stMetricValue"] { color: var(--accent-bright) !important; font-weight: 800; }
        [data-testid="stMetricDelta"] { color: var(--success) !important; }
        [data-testid="stDataFrame"] { overflow: hidden; border: 1px solid var(--line); border-radius: 13px; }
        [data-testid="stDataFrame"] * { color: var(--text) !important; }
        [data-testid="stSidebar"] {
          background: rgba(12, 14, 20, .97) !important;
          border-right: 1px solid var(--line) !important;
        }
        [data-testid="stSidebar"] * { color: var(--text-soft) !important; }
        [data-testid="stSidebar"] .stButton > button { justify-content: flex-start; background: transparent !important; box-shadow: none; }
        [data-testid="stSidebar"] .stButton > button:hover { color: var(--accent-bright) !important; background: var(--surface) !important; }
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {
          color: #28190f !important;
          background: #d7a071 !important;
          border-color: #c99265 !important;
        }
        [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover:not(:disabled) {
          color: #24160d !important;
          background: #ce9568 !important;
          border-color: #bf895e !important;
        }

        .login-shell {
          margin: 5vh auto 1rem;
          padding: 2rem;
          border: 1px solid var(--line);
          border-radius: 22px;
          background:
            radial-gradient(circle at 88% 0, rgba(156,146,255,.16), transparent 32%),
            radial-gradient(circle at 4% 92%, rgba(229,164,100,.13), transparent 36%),
            linear-gradient(145deg, #191c27, #101219);
          box-shadow: var(--shadow);
        }
        .login-brand { margin-bottom: 2.2rem; }
        .login-title { margin: .8rem 0 .55rem; color: var(--text) !important; font-size: clamp(2.2rem, 4.5vw, 3.8rem); font-weight: 830; letter-spacing: -.065em; line-height: 1.02; }
        .login-copy { max-width: 540px; color: var(--text-soft) !important; font-size: .95rem; line-height: 1.75; }
        .login-hint { margin-top: .8rem; color: var(--muted) !important; font-size: .78rem; }
        .login-points { display: flex; flex-wrap: wrap; gap: .55rem; margin-top: 1.5rem; }
        .login-points span { padding: .45rem .7rem; border: 1px solid var(--line-strong); border-radius: 999px; color: var(--text-soft) !important; font-size: .7rem; }
        .st-key-login-panel {
          margin: 5vh auto 1rem;
          padding: 1.35rem;
          border: 1px solid var(--line);
          border-radius: 22px;
          background: rgba(17, 21, 29, .94);
          box-shadow: var(--shadow);
        }
        .st-key-mode-selector {
          margin: .9rem 0 1rem;
          padding: .85rem 1rem .7rem;
          border-color: var(--line-strong) !important;
          border-radius: 15px !important;
          background: linear-gradient(140deg, rgba(34,43,56,.74), rgba(17,21,29,.92)) !important;
        }
        .st-key-mode-selector h4 { margin: .1rem 0 .65rem; font-size: .95rem; }

        /* Backend connection indicator */
        .backend-status {
            min-height: 44px;
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 0 15px;
            border: 1px solid var(--line);
            border-radius: 11px;
            background: rgba(119, 209, 173, 0.07);
            color: var(--text) !important;
            font-size: 0.88rem;
            font-weight: 650;
        }

        .backend-online {
            border-color: rgba(119, 209, 173, 0.25);
        }

        .backend-offline {
            background: rgba(241, 142, 138, 0.07);
            border-color: rgba(241, 142, 138, 0.3);
        }

        .status-indicator {
            width: 8px;
            height: 8px;
            flex-shrink: 0;
            border-radius: 50%;
            background: var(--success);
            box-shadow: 0 0 10px rgba(119, 209, 173, 0.5);
        }

        .backend-offline .status-indicator {
            background: var(--danger);
            box-shadow: 0 0 10px rgba(241, 142, 138, 0.5);
        }

        .status-detail {
            margin-left: auto;
            color: var(--muted) !important;
            font-size: 0.72rem;
            font-weight: 450;
        }
        .st-key-raft-cluster-status { min-width: 0; }
        [data-testid="stTable"] { max-width: 100%; overflow-x: auto; }
        [data-testid="stTable"] table { width: 100%; table-layout: fixed; }
        [data-testid="stTable"] th, [data-testid="stTable"] td {
          white-space: normal !important;
          overflow-wrap: anywhere;
          font-size: .76rem;
        }
        [data-testid="stChatMessage"] {
          margin: .7rem 0;
          padding: .5rem .7rem;
          border: 1px solid var(--line);
          border-radius: 15px;
          background: linear-gradient(145deg, var(--surface-raised), var(--surface)) !important;
        }
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
          border-color: #584733 !important;
          background: linear-gradient(145deg, #31291f, #25231f) !important;
        }
        [data-testid="stChatInput"] { border-color: var(--line-strong) !important; background: var(--surface) !important; }
        .support-welcome {
          display: flex; align-items: center; gap: 1rem; margin: .75rem 0 1.1rem; padding: 1.25rem;
          border: 1px solid var(--line); border-radius: var(--radius);
          background: radial-gradient(circle at 90% 0, rgba(229,164,100,.13), transparent 42%), var(--surface);
          box-shadow: 0 14px 34px rgba(0,0,0,.17);
        }
        .support-avatar { display: grid; place-items: center; width: 2.8rem; height: 2.8rem; flex: 0 0 2.8rem; border-radius: 50%; background: var(--accent); color: var(--accent-ink) !important; font-weight: 800; }
        .support-welcome b { color: var(--text) !important; }
        .support-welcome p { margin: .2rem 0 0; color: var(--text-soft) !important; }
        .support-seat-list { color: var(--text-soft) !important; line-height: 1.8; word-break: break-word; }
        .profile-card, .activity-card { min-height: 198px; padding: 1.5rem; }
        .profile-card p, .activity-grid span { color: var(--text-soft) !important; }
        .profile-card h2 { margin: .9rem 0 .2rem; font-size: 1.4rem; }
        .avatar { display: grid; place-items: center; width: 46px; height: 46px; border: 1px solid rgba(229,164,100,.4); border-radius: 50%; background: rgba(229,164,100,.12); color: var(--accent-bright) !important; font-weight: 800; }
        .activity-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: .7rem; margin-top: 2rem; }
        .activity-grid b, .activity-grid span { display: block; }
        .activity-grid b { font-size: 1.6rem; letter-spacing: -.04em; }
        .activity-grid span { margin-top: .2rem; font-size: .7rem; }
        .site-footer {
          display: grid; grid-template-columns: 1.35fr 1.5fr .8fr; align-items: end; gap: 1rem;
          margin-top: 3.5rem; padding: 1.35rem 0 0; border-top: 1px solid var(--line);
        }
        .footer-brand { font-size: .74rem; }
        .site-footer p, .footer-copy, .footer-links { color: var(--muted) !important; font-size: .7rem; }
        .site-footer p { margin: .35rem 0 0; }
        .footer-links { display: flex; flex-wrap: wrap; justify-content: center; gap: 1rem; }
        .footer-copy { text-align: right; }

        @media (max-width: 900px) {
          .block-container { padding: 1.25rem 1.3rem 3rem !important; }
          .st-key-seat-summary { position: static; }
          .site-footer { grid-template-columns: 1fr 1fr; }
          .footer-copy { grid-column: 1 / -1; text-align: left; }
          .st-key-home-featured { margin: 1.1rem 0 1.7rem; }
          .st-key-home-featured .home-featured-copy { padding-top: .5rem; }
        }
        @media (max-width: 640px) {
          .block-container { padding: .9rem .9rem 2.5rem !important; }
          .hero { margin: 2rem auto 1.25rem !important; }
          .home-hero { margin-top: 1.2rem !important; }
          .hero h1 { font-size: clamp(2.4rem, 13vw, 3.7rem) !important; }
          .hero p { font-size: .88rem; }
          .page-intro { margin: 1.1rem 0 1rem !important; }
          .page-intro h1 { font-size: 2.1rem !important; }
          .section-head { display: block; margin-top: 1.7rem; }
          .section-head span { display: block; margin-top: .3rem; }
          .editorial-note { display: block; }
          .editorial-note p { margin: .4rem 0; }
          .seat-area { padding: .85rem .45rem; }
          .st-key-seat-map .stButton > button { min-width: 2.1rem; min-height: 2.05rem; padding: .2rem; font-size: .62rem; }
          .summary-card, .ticket { padding: 1rem; }
          .confirmation { margin-top: 1.4rem; padding: 1.3rem; }
          .st-key-confirmation-ticket { margin: 1rem 0; padding: .8rem; }
          .st-key-confirmation-ticket .confirmation { padding: .25rem; }
          .st-key-confirmation-ticket .confirmation-grid { grid-template-columns: 1fr 1fr; }
          .login-shell, .st-key-login-panel { margin-top: 1rem; padding: 1.2rem; }
          .st-key-mode-selector { padding: .7rem; }
          .login-brand { margin-bottom: 1.1rem; }
          .support-welcome { padding: .9rem; }
          .site-footer { grid-template-columns: 1fr; }
          .footer-links { justify-content: flex-start; }
        }
        @media (prefers-reduced-motion: reduce) {
          *, *::before, *::after {
            scroll-behavior: auto !important;
            animation-duration: .01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: .01ms !important;
          }
        }

        /* ── FlashReserve visual refresh: frontend-only polish ───────────── */
        :root {
          --bg: #080d18;
          --bg-glow: #101a2c;
          --surface: #101827;
          --surface-raised: #162238;
          --surface-soft: #1d2c45;
          --line: rgba(148, 169, 202, .16);
          --line-strong: rgba(148, 169, 202, .28);
          --text: #f4f7ff;
          --text-soft: #c0cbe0;
          --muted: #8493ad;
          --accent: #8b9cff;
          --accent-bright: #b8c3ff;
          --accent-ink: #10152b;
          --violet: #c39bff;
          --success: #62d6b0;
          --warning: #f2c879;
          --danger: #ff8e9b;
          --shadow: 0 24px 70px rgba(0, 0, 0, .32);
          --radius: 20px;
        }
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
          background:
            radial-gradient(ellipse at 78% -12%, rgba(113, 128, 255, .17), transparent 34%),
            radial-gradient(ellipse at 2% 18%, rgba(52, 190, 210, .075), transparent 28%),
            linear-gradient(180deg, #080d18 0%, #0a1120 55%, #080d18 100%) !important;
        }
        .block-container { max-width: 1380px; padding-top: 1.35rem !important; }
        [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] { min-width: 0; }
        h1, h2, h3, h4 { color: #f5f7ff !important; letter-spacing: -.045em; }
        h1 { font-weight: 850 !important; }
        h2 { font-weight: 780 !important; }
        p, li { color: var(--text-soft); }
        [data-testid="stCaptionContainer"], small { color: var(--muted) !important; }

        /* Header / navigation */
        .brand, .login-brand, .footer-brand { letter-spacing: .14em; }
        .brand-mark {
          background: linear-gradient(135deg, #9aa8ff, #66d9e7) !important;
          box-shadow: 0 0 22px rgba(125, 147, 255, .48) !important;
        }
        .st-key-main-navigation, .st-key-admin-header {
          padding: .72rem .9rem;
          border: 1px solid rgba(151, 170, 212, .16);
          border-radius: 18px;
          background: rgba(14, 23, 39, .76);
          box-shadow: 0 12px 35px rgba(0,0,0,.18);
          backdrop-filter: blur(18px);
          margin-bottom: 1.5rem;
        }
        .st-key-main-navigation .stButton > button,
        .st-key-admin-header .stButton > button { min-height: 40px; padding-inline: 1rem; }

        /* Buttons: clear hierarchy, strong hover/focus, no behavior changes */
        .stButton > button, .stLinkButton > a,
        [data-testid="stFormSubmitButton"] button {
          min-height: 44px;
          border: 1px solid rgba(155, 174, 220, .25) !important;
          border-radius: 12px !important;
          background: linear-gradient(180deg, #1d2b43, #17243a) !important;
          color: #eef2ff !important;
          font-weight: 700 !important;
          letter-spacing: .005em;
          box-shadow: 0 5px 16px rgba(0,0,0,.13);
          transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease, background .16s ease !important;
        }
        .stButton > button:hover:not(:disabled), .stLinkButton > a:hover,
        [data-testid="stFormSubmitButton"] button:hover:not(:disabled) {
          transform: translateY(-1px);
          border-color: rgba(151, 169, 255, .72) !important;
          background: linear-gradient(180deg, #293b5d, #1c2d49) !important;
          box-shadow: 0 9px 24px rgba(75, 98, 190, .2) !important;
          color: #fff !important;
        }
        .stButton > button[kind="primary"],
        .stButton > button[data-testid^="stBaseButton-primary"],
        [data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"],
        [data-testid="stFormSubmitButton"] button[kind="primary"] {
          background: linear-gradient(120deg, #a6b1ff 0%, #7d91f5 52%, #6e9eea 100%) !important;
          color: #11182e !important;
          border: 1px solid rgba(205, 213, 255, .7) !important;
          box-shadow: 0 7px 22px rgba(112, 132, 245, .25) !important;
        }
        .stButton > button[kind="primary"]:hover:not(:disabled),
        .stButton > button[data-testid^="stBaseButton-primary"]:hover:not(:disabled),
        [data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"]:hover:not(:disabled),
        [data-testid="stFormSubmitButton"] button[kind="primary"]:hover:not(:disabled) {
          background: linear-gradient(120deg, #c0c8ff, #91a5ff 60%, #84b4f3) !important;
          box-shadow: 0 10px 28px rgba(112, 132, 245, .34) !important;
        }
        .stButton > button:disabled, [data-testid="stFormSubmitButton"] button:disabled {
          opacity: .52 !important; cursor: not-allowed;
        }

        /* Inputs, selectors and tabs */
        [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
        [data-testid="stNumberInput"] input, [data-testid="stDateInput"] input,
        [data-testid="stTimeInput"] input,
        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
        [data-testid="stFileUploaderDropzone"], [data-testid="stChatInput"] {
          background: rgba(12, 21, 36, .92) !important;
          border: 1px solid rgba(145, 166, 210, .24) !important;
          border-radius: 12px !important;
          color: #f3f6ff !important;
          min-height: 44px;
        }
        [data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus,
        [data-testid="stNumberInput"] input:focus {
          border-color: #98a8ff !important;
          box-shadow: 0 0 0 3px rgba(137, 155, 255, .16) !important;
        }
        [data-testid="stTextInput"] input::placeholder,
        [data-testid="stTextArea"] textarea::placeholder { color: #71819d !important; }
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
          gap: .45rem; padding: .35rem; border: 1px solid var(--line);
          border-radius: 14px; background: rgba(12, 20, 34, .7);
        }
        [data-baseweb="tab"] { border-radius: 10px !important; color: #9eacc5 !important; }
        [data-baseweb="tab"][aria-selected="true"] {
          color: #e8ebff !important; background: rgba(132, 150, 255, .16) !important;
        }
        [data-testid="stTabs"] [data-baseweb="tab-highlight"] { background: #9aa8ff !important; }
        [data-testid="stCheckbox"] label, [data-testid="stRadio"] label,
        [data-testid="stPills"] label { color: var(--text-soft) !important; }
        [data-testid="stProgressBar"] > div > div { background: linear-gradient(90deg, #7d91f5, #65d2dc) !important; }

        /* Cards and data surfaces */
        [data-testid="stVerticalBlockBorderWrapper"], [data-testid="stForm"],
        .seat-area, .summary-card, .ticket, .profile-card, .activity-card, .support-shell {
          border: 1px solid rgba(145, 166, 210, .18) !important;
          border-radius: 18px !important;
          background: linear-gradient(145deg, rgba(23, 36, 58, .94), rgba(13, 23, 39, .96)) !important;
          box-shadow: 0 16px 42px rgba(0,0,0,.2) !important;
        }
        [data-testid="stMetric"] {
          padding: 1rem 1.1rem;
          border: 1px solid rgba(145, 166, 210, .18);
          border-radius: 16px;
          background: linear-gradient(145deg, rgba(26, 42, 68, .78), rgba(14, 25, 43, .9));
        }
        [data-testid="stMetricLabel"] { color: #9eacc5 !important; font-size: .76rem !important; }
        [data-testid="stMetricValue"] { color: #f2f5ff !important; font-weight: 820 !important; }
        [data-testid="stDataFrame"], [data-testid="stTable"] {
          border: 1px solid var(--line) !important; border-radius: 14px; overflow: hidden;
        }
        [data-testid="stAlert"] { border-radius: 14px !important; }
        [data-testid="stExpander"] {
          border: 1px solid var(--line) !important; border-radius: 14px !important;
          background: rgba(17, 29, 48, .72) !important;
        }
        [data-testid="stImage"] img { border-radius: 14px; }
        .hero, .login-shell {
          border: 1px solid rgba(151, 169, 220, .18);
          border-radius: 24px;
          background:
            radial-gradient(ellipse at 88% 10%, rgba(146, 157, 255, .2), transparent 34%),
            linear-gradient(125deg, rgba(25, 40, 67, .98), rgba(12, 22, 39, .96) 68%);
          box-shadow: 0 24px 70px rgba(0,0,0,.26);
        }
        .hero { padding: clamp(1.6rem, 4vw, 3.2rem) !important; }
        .hero .eyebrow, .eyebrow, .section-kicker { color: #aebaff !important; }
        .hero h1 em { color: #aebaff !important; }
        .event-category { color: #9eafff !important; }
        .event-card, .booking-card {
          border: 1px solid rgba(145, 166, 210, .18) !important;
          border-radius: 18px !important; overflow: hidden;
          background: linear-gradient(150deg, #192943, #101b2d) !important;
          box-shadow: 0 14px 36px rgba(0,0,0,.2) !important;
          transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
        }
        .event-card:hover, .booking-card:hover {
          transform: translateY(-3px); border-color: rgba(154, 169, 255, .5) !important;
          box-shadow: 0 20px 42px rgba(0,0,0,.28) !important;
        }
        .st-key-home-featured {
          border: 1px solid rgba(147, 163, 255, .24) !important;
          background: radial-gradient(ellipse at 95% 0, rgba(139,153,255,.16), transparent 38%),
                      linear-gradient(140deg, #192943, #0e192b 78%) !important;
        }
        .home-featured-price strong, .summary-total strong { color: #bdc6ff !important; }
        .section-head { border-bottom-color: var(--line) !important; }
        .empty-state { border-color: rgba(145, 166, 210, .28) !important; background: rgba(18, 31, 51, .55); }
        .confirmation { border-color: rgba(98, 214, 176, .28) !important; background: radial-gradient(circle at 50% 0, rgba(98,214,176,.12), transparent 40%), #101d2e !important; }
        .screen-line { background: linear-gradient(90deg, transparent, #8b9cff, #65d2dc, transparent) !important; }
        .site-footer { border-top-color: var(--line) !important; }
        [data-testid="stSidebar"] {
          background: linear-gradient(180deg, #101a2b, #0b1321) !important;
          border-right: 1px solid rgba(145, 166, 210, .14);
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 { color: #f1f4ff !important; }
        [data-testid="stSidebar"] .stButton > button { width: 100%; }
        [data-testid="stPopover"] button { border-radius: 10px !important; }

        @media (max-width: 760px) {
          .block-container { padding: .85rem .9rem 2.5rem !important; }
          .st-key-main-navigation, .st-key-admin-header { padding: .55rem; }
          .hero { padding: 1.35rem !important; border-radius: 18px; }
          [data-testid="stMetric"] { padding: .8rem; }
        }

        /* ==========================================
          FLASHRESERVE - LOGIN & REGISTER POLISH
          Frontend styling only
        ========================================== */

        /* Login and registration input fields */
        .st-key-login-panel [data-testid="stTextInput"] input {
            background: #1b2638 !important;
            color: #eef2ff !important;
            border: 1px solid #3a4962 !important;
            border-radius: 11px !important;
            min-height: 48px !important;
            box-shadow: none !important;
        }

        /* Input hover */
        .st-key-login-panel [data-testid="stTextInput"] input:hover {
            border-color: #7185b3 !important;
        }

        /* Input focus */
        .st-key-login-panel [data-testid="stTextInput"] input:focus {
            border-color: #91a5ff !important;
            box-shadow: 0 0 0 3px rgba(145, 165, 255, 0.13) !important;
        }

        /* Placeholder */
        .st-key-login-panel [data-testid="stTextInput"] input::placeholder {
            color: #8291aa !important;
            opacity: 1;
        }

        /* Password visibility button */
        .st-key-login-panel [data-testid="stTextInput"] button {
            background: #1b2638 !important;
            color: #b9c7e3 !important;
            border: 1px solid #3a4962 !important;
            border-left: none !important;
            border-radius: 0 11px 11px 0 !important;
            min-height: 46px !important;
            box-shadow: none !important;
        }

        /* Password eye icon */
        .st-key-login-panel [data-testid="stTextInput"] button svg {
            color: #b9c7e3 !important;
            fill: currentColor !important;
        }

        /* Password button hover */
        .st-key-login-panel [data-testid="stTextInput"] button:hover {
            background: #293750 !important;
            color: #ffffff !important;
        }

        /* Login tabs */
        .st-key-login-panel [data-testid="stTabs"] [data-baseweb="tab-list"] {
            display: flex;
            gap: 8px !important;
            padding: 5px !important;
            border: 1px solid #2c3950 !important;
            border-radius: 12px !important;
            background: #131d2d !important;
        }

        /* Individual tabs */
        .st-key-login-panel [data-baseweb="tab"] {
            padding: 10px 18px !important;
            border-radius: 8px !important;
            color: #aab7ce !important;
            background: transparent !important;
            border: none !important;
            transition: background .2s ease, color .2s ease;
        }

        /* Selected tab */
        .st-key-login-panel [data-baseweb="tab"][aria-selected="true"] {
            color: #ffffff !important;
            background: #263653 !important;
            border: 1px solid #42577d !important;
        }

        /* Remove default tab underline */
        .st-key-login-panel [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
            display: none !important;
        }

        /* Checkbox */
        .st-key-login-panel [data-testid="stCheckbox"] label {
            color: #b9c7dc !important;
        }

        /* Form labels */
        .st-key-login-panel [data-testid="stTextInput"] label {
            color: #c5d0e3 !important;
            font-weight: 550 !important;
        }

        /* Registration password guidance */
        .st-key-login-panel [data-testid="stCaptionContainer"] p {
            color: #8999b4 !important;
            font-size: 0.82rem !important;
        }

        /* Login hint */
        .login-hint {
            color: #8999b4 !important;
            font-size: 0.78rem;
            margin-top: 1rem;
        }

        /* =====================================
          DARK ERROR / ALERT NOTIFICATIONS
        ===================================== */

        [data-testid="stAlert"] {
            background: #171f30 !important;
            border: 1px solid rgba(255, 142, 155, 0.28) !important;
            border-left: 4px solid #ff8295 !important;
            border-radius: 12px !important;
            color: #f4f5ff !important;
            box-shadow: 0 8px 22px rgba(0, 0, 0, 0.16) !important;
        }

        [data-testid="stAlert"] > div {
            background: transparent !important;
        }

        [data-testid="stAlert"] p,
        [data-testid="stAlert"] span,
        [data-testid="stAlert"] [data-testid="stMarkdownContainer"] {
            color: #e5eaff !important;
        }

        [data-testid="stAlert"] svg {
            color: #ff8295 !important;
            fill: currentColor !important;
        }

        /* =====================================
          FLASHRESERVE NAVIGATION SPACING
        ===================================== */

        .st-key-main-navigation {
            display: flex !important;
            align-items: center !important;
            gap: 14px !important;
            padding: 12px 16px !important;
        }

        .st-key-main-navigation [data-testid="stHorizontalBlock"] {
            display: flex !important;
            align-items: center !important;
            gap: 10px !important;
        }

        .st-key-main-navigation [data-testid="stElementContainer"] {
            flex: 0 0 auto !important;
            min-width: 0 !important;
        }

        .st-key-main-navigation .brand {
            margin-right: 8px;
            white-space: nowrap !important;
        }

        .st-key-main-navigation .stButton > button {
            min-height: 44px !important;
            padding: 0 18px !important;
            white-space: nowrap !important;
            border-radius: 12px !important;
            font-size: 0.88rem !important;
        }

        /* Responsive navigation */
        @media (max-width: 760px) {
            .st-key-main-navigation {
                gap: 8px !important;
                padding: 10px !important;
            }

            .st-key-main-navigation [data-testid="stHorizontalBlock"] {
                gap: 7px !important;
                flex-wrap: wrap !important;
            }

            .st-key-main-navigation .stButton > button {
                padding: 0 12px !important;
                font-size: 0.8rem !important;
            }
        }

        /* ============================================
          FLASHRESERVE - FINAL UI CONSISTENCY FIXES
          Visual changes only. No application logic.
        ============================================ */

        /* 1. EXPLORE AND EVENT SEARCH INPUTS */

        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea {
            background: #1b2638 !important;
            color: #edf2ff !important;
            border: 1px solid #40516d !important;
            border-radius: 10px !important;
        }

        [data-testid="stTextInput"] input::placeholder {
            color: #8798b5 !important;
        }


        /* 2. CATEGORY PILLS */

        [data-testid="stPills"] button,
        [data-testid="stPills"] [role="radio"] {
            background: #172338 !important;
            color: #c5d1e8 !important;
            border: 1px solid #354762 !important;
            border-radius: 22px !important;
            box-shadow: none !important;
        }

        [data-testid="stPills"] button:hover,
        [data-testid="stPills"] [role="radio"]:hover {
            background: #263957 !important;
            color: #ffffff !important;
            border-color: #7189bd !important;
        }

        [data-testid="stPills"] button[aria-pressed="true"],
        [data-testid="stPills"] [role="radio"][aria-checked="true"] {
            background: #293c62 !important;
            color: #ffffff !important;
            border: 1px solid #8299e8 !important;
        }


        /* 3. EVENT FILTER DROPDOWNS */

        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stMultiSelect"] [data-baseweb="select"] > div {
            background: #1b2638 !important;
            color: #edf2ff !important;
            border: 1px solid #40516d !important;
            border-radius: 10px !important;
        }

        [data-testid="stSelectbox"] [data-baseweb="select"] *,
        [data-testid="stMultiSelect"] [data-baseweb="select"] * {
            color: #edf2ff !important;
        }

        [data-baseweb="popover"],
        [data-baseweb="menu"],
        [role="listbox"] {
            background: #172338 !important;
            color: #edf2ff !important;
            border: 1px solid #40516d !important;
        }

        [role="option"] {
            background: #172338 !important;
            color: #edf2ff !important;
        }

        [role="option"]:hover {
            background: #293c62 !important;
        }


        /* 4. SUPPORT CHAT INPUT AND BOTTOM AREA */

        [data-testid="stBottom"] {
            background: #0b1220 !important;
            border-top: 1px solid #293750 !important;
        }

        [data-testid="stChatInput"] {
            background: #172338 !important;
            border: 1px solid #40516d !important;
            border-radius: 13px !important;
            box-shadow: none !important;
        }

        [data-testid="stChatInput"] textarea {
            background: transparent !important;
            color: #edf2ff !important;
        }

        [data-testid="stChatInput"] textarea::placeholder {
            color: #8798b5 !important;
        }

        [data-testid="stChatInput"] button {
            background: #293c62 !important;
            color: #ffffff !important;
            border-radius: 9px !important;
        }


        /* 5. LOGIN ERROR MESSAGE */

        [data-testid="stAlert"] {
            background: #192337 !important;
            border: 1px solid rgba(255, 130, 149, .35) !important;
            border-left: 4px solid #ff8295 !important;
            border-radius: 12px !important;
            color: #edf2ff !important;
        }

        [data-testid="stAlert"] p,
        [data-testid="stAlert"] span {
            color: #edf2ff !important;
        }


        /* 6. MAIN NAVIGATION SPACING */

        .st-key-main-navigation {
            display: flex !important;
            align-items: center !important;
            gap: 14px !important;
        }

        .st-key-main-navigation .stButton > button {
            min-height: 46px !important;
            padding: 0 18px !important;
            border-radius: 12px !important;
            white-space: nowrap !important;
        }

        .st-key-main-navigation .brand {
            margin-right: 6px !important;
            white-space: nowrap !important;
        }


        /* 7. RESPONSIVE NAVIGATION */

        @media (max-width: 760px) {
            .st-key-main-navigation {
                gap: 8px !important;
            }

            .st-key-main-navigation .stButton > button {
                padding: 0 12px !important;
                min-height: 40px !important;
            }
        }

        /* ==========================================
          SUPPORT CHAT - FIX WHITE FIXED BOTTOM AREA
        ========================================== */

        /* Streamlit fixed chat input container */
        [data-testid="stBottom"],
        [data-testid="stBottomBlockContainer"] {
            background: #0a0f1b !important;
            background-color: #0a0f1b !important;
            border-top: 1px solid #293750 !important;
            box-shadow: none !important;
        }

        /* Inner bottom container */
        [data-testid="stBottom"] > div,
        [data-testid="stBottomBlockContainer"] > div {
            background: #0a0f1b !important;
        }

        /* Chat input outer box */
        [data-testid="stChatInput"],
        [data-testid="stChatInput"] > div {
            background: #172338 !important;
            background-color: #172338 !important;
            border: 1px solid #40516d !important;
            border-radius: 13px !important;
            box-shadow: none !important;
        }

        /* Chat input text */
        [data-testid="stChatInput"] textarea {
            background: transparent !important;
            color: #edf2ff !important;
            -webkit-text-fill-color: #edf2ff !important;
        }

        /* Placeholder */
        [data-testid="stChatInput"] textarea::placeholder {
            color: #91a0ba !important;
            -webkit-text-fill-color: #91a0ba !important;
        }

        /* Send button */
        [data-testid="stChatInput"] button {
            background: #293c62 !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 9px !important;
        }

        /* ==========================================
          EVENTS - DARK SELECTBOXES
        ========================================== */

        [data-testid="stSelectbox"] [data-baseweb="select"] {
            background: #1b2638 !important;
            border-radius: 10px !important;
        }

        [data-testid="stSelectbox"] [data-baseweb="select"] > div {
            background: #1b2638 !important;
            border: 1px solid #40516d !important;
            border-radius: 10px !important;
            color: #edf2ff !important;
        }

        [data-testid="stSelectbox"] [data-baseweb="select"] span {
            color: #edf2ff !important;
        }

        /* Dropdown menu */
        [data-baseweb="popover"] [role="listbox"],
        [data-baseweb="menu"] {
            background: #172338 !important;
            border: 1px solid #40516d !important;
        }

        [data-baseweb="popover"] [role="option"] {
            background: #172338 !important;
            color: #edf2ff !important;
        }

        [data-baseweb="popover"] [role="option"]:hover {
            background: #293c62 !important;
        }

        /* ==========================================
          EVENTS - CATEGORY FILTERS
        ========================================== */

        .st-key-event_category [role="radiogroup"] {
            gap: 9px !important;
        }

        .st-key-event_category [role="radio"] {
            background: #172338 !important;
            border: 1px solid #354762 !important;
            border-radius: 22px !important;
            color: #c5d1e8 !important;
            padding: 7px 17px !important;
        }

        .st-key-event_category [role="radio"] p {
            color: inherit !important;
        }

        .st-key-event_category [role="radio"][aria-checked="true"] {
            background: #293c62 !important;
            border-color: #8299e8 !important;
            color: #ffffff !important;
        }

        /* =====================================
          SUPPORT CHAT COMPOSER
          Replaces Streamlit fixed chat input
        ===================================== */

        .st-key-support-composer {
            background: #111a2a !important;
            border: 1px solid #30415e !important;
            border-radius: 15px !important;
            padding: 12px 14px !important;
            margin-top: 24px !important;
            margin-bottom: 20px !important;
        }

        .st-key-support-composer [data-testid="stForm"] {
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
        }

        .st-key-support-composer [data-testid="stTextInput"] input {
            background: #1b2638 !important;
            color: #f1f4ff !important;
            border: 1px solid #40516d !important;
            border-radius: 11px !important;
            min-height: 46px !important;
        }

        .st-key-support-composer [data-testid="stTextInput"] input::placeholder {
            color: #91a0ba !important;
        }

        .st-key-support-composer .stButton > button,
        .st-key-support-composer [data-testid="stFormSubmitButton"] button {
            background: #718cf0 !important;
            color: #101a30 !important;
            border: none !important;
            border-radius: 11px !important;
            min-height: 46px !important;
            font-size: 19px !important;
        }

        .st-key-support-composer .stButton > button:hover,
        .st-key-support-composer [data-testid="stFormSubmitButton"] button:hover {
            background: #91a5ff !important;
        }

        /* Remove the old fixed chat-input area */
        [data-testid="stBottom"],
        [data-testid="stBottomBlockContainer"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
