"""UI theme layer for the MDPS Streamlit experience.

The main app owns behavior. This module owns presentation so the visual system
can be reviewed, explained, and evolved without touching prediction logic.
"""

MODERN_EDGE_CSS = """
<style>
:root {
    --mdps-bg: #f6f8fb;
    --mdps-panel: #ffffff;
    --mdps-panel-muted: #f9fafb;
    --mdps-ink: #07111f;
    --mdps-muted: #5b6677;
    --mdps-line: #d8dee8;
    --mdps-line-strong: #aeb8c8;
    --mdps-brand: #0f4c81;
    --mdps-brand-strong: #073b67;
    --mdps-teal: #087f7b;
    --mdps-amber: #b7791f;
    --mdps-green: #157347;
    --mdps-red: #b42318;
    --mdps-radius: 4px;
    --mdps-radius-card: 10px;
    --mdps-sidebar-pad: 1.25rem;
    --mdps-shadow: 0 14px 34px rgba(7, 17, 31, 0.09);
    --mdps-shadow-soft: 0 8px 18px rgba(7, 17, 31, 0.06);
}

html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    color: var(--mdps-ink) !important;
    letter-spacing: 0 !important;
}

[data-testid="stAppViewContainer"] {
    background:
        linear-gradient(180deg, #f7fafc 0%, #eef3f8 52%, #f8fafc 100%) !important;
}

.main .block-container {
    max-width: 1320px;
    padding-top: 2.2rem;
    animation: mdpsPageIn 420ms ease-out both;
}

[data-testid="stHeader"] {
    background: rgba(246, 248, 251, 0.92) !important;
    border-bottom: 1px solid rgba(216, 222, 232, 0.75);
}

[data-testid="stSidebar"] {
    background: #07111f !important;
    border-right: 1px solid #1d2b3f !important;
    box-shadow: none !important;
}

[data-testid="stSidebar"] * {
    color: #e8edf5 !important;
}

/* ── Navigation rail ───────────────────────────────────────────────────────
   The nav is a rail, not a stack of buttons: rows run edge to edge in the
   sidebar and state is carried by an accent bar plus a left-to-right wash,
   so nothing floats inside a box. Streamlit pads the sidebar content, so the
   padding is pinned to a known value and the radio group breaks back out of
   it by exactly that amount. */
/* Streamlit insets sidebar content twice (10px on stSidebarContent, 20px on
   stSidebarUserContent). Collapsing the outer one and pinning the inner one
   makes the total inset exactly one known token, so the nav can break out of
   it with `-1 * that token` instead of a magic number that drifts between
   Streamlit versions. */
[data-testid="stSidebarContent"] {
    padding-left: 0 !important;
    padding-right: 0 !important;
    align-items: stretch !important;
    /* Streamlit sets `scrollbar-gutter: stable both-edges`, which reserves the
       scrollbar width on BOTH sides — a ~10px dead strip down the left of the
       sidebar that no width or margin on the content can cross. That strip was
       what kept the nav from reaching the edge. `auto` reclaims the left side,
       and the thin bar below keeps the right side down to a hairline. */
    scrollbar-gutter: auto !important;
}

[data-testid="stSidebarContent"]::-webkit-scrollbar {
    width: 6px;
}

[data-testid="stSidebarContent"]::-webkit-scrollbar-track {
    background: transparent;
}

[data-testid="stSidebarContent"]::-webkit-scrollbar-thumb {
    background: #24384f;
    border-radius: 999px;
}

[data-testid="stSidebarContent"]::-webkit-scrollbar-thumb:hover {
    background: #38628d;
}

[data-testid="stSidebarUserContent"] {
    padding-left: var(--mdps-sidebar-pad) !important;
    padding-right: var(--mdps-sidebar-pad) !important;
    width: 100% !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
}

/* Streamlit gives element containers an explicit width, which beats the
   parent's align-items: stretch — without this the nav collapses to its
   text width and the break-out maths resolves against the wrong base. */
[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.stRadio) {
    width: 100% !important;
}

[data-testid="stSidebar"] .stRadio {
    margin-left: calc(-1 * var(--mdps-sidebar-pad)) !important;
    margin-right: calc(-1 * var(--mdps-sidebar-pad)) !important;
    width: calc(100% + (2 * var(--mdps-sidebar-pad))) !important;
}

/* The collapsed widget label is still in the DOM; the rules below force
   display on labels, so it has to be hidden explicitly or it renders as a
   phantom first nav row. */
[data-testid="stSidebar"] .stRadio > label[data-testid="stWidgetLabel"] {
    display: none !important;
}

[data-testid="stSidebar"] .stRadio > div,
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
    width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 1px !important;
}

[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label,
[data-testid="stSidebar"] .stRadio label {
    width: 100% !important;
    min-height: 2.75rem !important;
    display: flex !important;
    align-items: center !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
    padding: 0.6rem var(--mdps-sidebar-pad) !important;
    margin: 0 !important;
    box-sizing: border-box !important;
    cursor: pointer !important;
    position: relative !important;
    overflow: hidden !important;
    color: #9fb0c6 !important;
    transition:
        background 180ms ease,
        color 180ms ease !important;
}

/* Accent bar: always present, collapsed to zero width until the row is
   active or hovered, so the row never shifts when state changes. */
[data-testid="stSidebar"] .stRadio label::before {
    content: "";
    position: absolute;
    inset: 0 auto 0 0;
    width: 3px;
    background: linear-gradient(180deg, #5db7ff, #2ee6cd);
    transform: scaleY(0);
    transform-origin: center;
    transition: transform 200ms cubic-bezier(0.16, 1, 0.3, 1);
}

[data-testid="stSidebar"] .stRadio label:hover {
    background: linear-gradient(
        90deg,
        rgba(93, 183, 255, 0.09) 0%,
        rgba(93, 183, 255, 0) 78%
    ) !important;
    color: #ffffff !important;
}

[data-testid="stSidebar"] .stRadio label:hover::before {
    transform: scaleY(0.45);
}

[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] > div:first-child,
[data-testid="stSidebar"] .stRadio label > div:first-child {
    display: none !important;
}

[data-testid="stSidebar"] .stRadio label:has(input:checked) {
    background: linear-gradient(
        90deg,
        rgba(93, 183, 255, 0.18) 0%,
        rgba(46, 230, 205, 0.06) 45%,
        rgba(93, 183, 255, 0) 100%
    ) !important;
    color: #ffffff !important;
}

[data-testid="stSidebar"] .stRadio label:has(input:checked)::before {
    transform: scaleY(1);
}

[data-testid="stSidebar"] .stRadio label:focus-within {
    outline: none !important;
    box-shadow: inset 0 0 0 1px rgba(93, 183, 255, 0.45) !important;
}

[data-testid="stSidebar"] .stRadio label p,
[data-testid="stSidebar"] .stRadio label span {
    width: 100% !important;
    color: inherit !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    white-space: nowrap !important;
}

[data-testid="stSidebar"] .stRadio label:has(input:checked) p,
[data-testid="stSidebar"] .stRadio label:has(input:checked) span {
    font-weight: 700 !important;
}

.sidebar-brand {
    background: none !important;
    -webkit-text-fill-color: #ffffff !important;
    color: #ffffff !important;
    letter-spacing: 0 !important;
}

.sidebar-tagline {
    color: #93a4ba !important;
    letter-spacing: 0.08em !important;
}

.main-title {
    color: var(--mdps-ink) !important;
    letter-spacing: 0 !important;
    font-size: clamp(2rem, 2.5vw, 2.6rem) !important;
}

.subtitle {
    color: var(--mdps-muted) !important;
    max-width: 840px;
}

.hero-banner {
    border-radius: var(--mdps-radius) !important;
    background:
        linear-gradient(135deg, #07111f 0%, #0f4c81 58%, #087f7b 100%) !important;
    border: 1px solid #17385a !important;
    box-shadow: var(--mdps-shadow) !important;
    padding: 3rem 2.4rem !important;
    animation: mdpsPageIn 520ms ease-out both;
}

.hero-banner::before {
    display: none !important;
}

.hero-banner h1 {
    background: none !important;
    -webkit-text-fill-color: #ffffff !important;
    color: #ffffff !important;
    letter-spacing: 0 !important;
}

.hero-badge,
.live-badge,
.risk-chip {
    border-radius: var(--mdps-radius) !important;
    letter-spacing: 0.03em !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
}

.hero-badge {
    background: rgba(255, 255, 255, 0.12) !important;
    border-color: rgba(255, 255, 255, 0.28) !important;
}

.live-badge {
    background: #edf8f6 !important;
    color: var(--mdps-teal) !important;
    border-color: #b7ddd8 !important;
}

.metric-card,
.feature-tile,
.section-card,
.upload-zone,
.risk-row,
.risk-meter-card,
.report-summary,
.assistant-shell,
.care-panel,
.clean-callout,
.clinical-card,
.signal-card,
.analysis-stat,
.report-workspace,
.stat-pill {
    background: var(--mdps-panel) !important;
    border: 1px solid var(--mdps-line) !important;
    border-radius: var(--mdps-radius) !important;
    box-shadow: var(--mdps-shadow-soft) !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
    transition:
        transform 180ms ease,
        box-shadow 180ms ease,
        border-color 180ms ease,
        background-color 180ms ease !important;
}

.metric-card:hover,
.feature-tile:hover,
.risk-row:hover,
.signal-card:hover,
.clinical-card:hover {
    transform: translateY(-2px) !important;
    border-color: var(--mdps-line-strong) !important;
    box-shadow: var(--mdps-shadow) !important;
}

/* ── Stat & feature cards ──────────────────────────────────────────────────
   Both rows are single grids rather than st.columns, because sibling columns
   size independently: a value that wraps ("PDF / Image") makes its own card
   taller than the rest. `grid-auto-rows: 1fr` forces one shared height, and
   pushing the value to the end of a column flex keeps every number sitting on
   the same baseline whether it wraps or not. */
.metric-grid,
.feature-grid {
    display: grid !important;
    gap: 0.9rem !important;
    grid-auto-rows: 1fr !important;
    margin: 0.35rem 0 1.6rem !important;
}

.metric-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
}

.feature-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
}

.metric-card,
.feature-tile {
    position: relative;
    overflow: hidden;
    height: 100% !important;
    border-radius: var(--mdps-radius-card) !important;
    display: flex !important;
    flex-direction: column !important;
}

/* Accent bar reads as a hairline at rest and thickens on hover, so the row
   has a resting state that is calm and a hover state that is legible. */
.metric-card::after,
.feature-tile::after {
    content: "";
    position: absolute;
    inset: 0 auto 0 0;
    width: 2px;
    background: linear-gradient(180deg, var(--mdps-brand), var(--mdps-teal));
    opacity: 0.7;
    transition:
        width 200ms cubic-bezier(0.16, 1, 0.3, 1),
        opacity 200ms ease;
}

.metric-card:hover::after,
.feature-tile:hover::after {
    width: 4px;
    opacity: 1;
}

.metric-card {
    min-height: 8.5rem !important;
    padding: 1.15rem 1.3rem 1.2rem 1.5rem !important;
    justify-content: space-between !important;
    gap: 0.7rem !important;
}

.metric-label {
    display: block !important;
    color: var(--mdps-muted) !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    line-height: 1.3 !important;
    letter-spacing: 0.09em !important;
    text-transform: uppercase !important;
}

.metric-value {
    display: block !important;
    margin-top: auto !important;
    font-family: 'Outfit', sans-serif !important;
    color: var(--mdps-brand) !important;
    font-size: clamp(1.5rem, 1.85vw, 2.1rem) !important;
    font-weight: 800 !important;
    line-height: 1.12 !important;
    letter-spacing: -0.02em !important;
    text-wrap: balance;
    overflow-wrap: break-word;
}

.stat-pill .num,
.signal-card .signal-score {
    color: var(--mdps-brand) !important;
}

.feature-tile {
    min-height: 10.5rem !important;
    padding: 1.35rem 1.4rem 1.4rem 1.6rem !important;
}

.feature-desc {
    margin-top: 0.35rem !important;
}

@media (max-width: 1100px) {
    .metric-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
    }

    .feature-grid {
        grid-template-columns: minmax(0, 1fr) !important;
    }
}

.feature-icon {
    width: 42px !important;
    height: 42px !important;
    border-radius: var(--mdps-radius) !important;
    background: #edf3f8 !important;
    border: 1px solid #d8e2ed;
    color: var(--mdps-brand) !important;
    font-size: 0.86rem !important;
    font-weight: 800 !important;
}

.feature-title,
.risk-title,
.signal-card .signal-name,
.gauge-title {
    color: var(--mdps-ink) !important;
}

.feature-desc,
.risk-detail,
.signal-card .signal-note,
.report-meta {
    color: var(--mdps-muted) !important;
}

.clean-callout,
.status-note {
    border-left: 4px solid var(--mdps-brand) !important;
    background: #ffffff !important;
    color: var(--mdps-ink) !important;
}

.profile-card,
.analysis-panel {
    border-radius: var(--mdps-radius) !important;
    background:
        linear-gradient(135deg, #07111f 0%, #0f4c81 62%, #087f7b 100%) !important;
    border: 1px solid #17385a !important;
    box-shadow: var(--mdps-shadow) !important;
}

.profile-avatar {
    border-radius: var(--mdps-radius) !important;
    background: rgba(255, 255, 255, 0.14) !important;
    border: 1px solid rgba(255, 255, 255, 0.42) !important;
    box-shadow: none !important;
}

/* ── Buttons ───────────────────────────────────────────────────────────────
   A flat rectangle in one solid blue is the default look everywhere. These
   get a depth model instead: a deep-to-brand vertical gradient, a lighter
   inset top edge reading as a lit surface, and a shadow tinted with the
   brand hue rather than grey. Press physically sinks the button by removing
   the lift, so the control feels mechanical rather than merely recoloured. */
.stButton > button,
.stDownloadButton > button,
button[kind="primary"],
button[kind="secondary"],
button[kind="primaryFormSubmit"],
button[kind="secondaryFormSubmit"] {
    position: relative !important;
    border-radius: 8px !important;
    background: linear-gradient(180deg, #1a5f9e 0%, var(--mdps-brand) 55%, #0c4373 100%) !important;
    border: 1px solid var(--mdps-brand-strong) !important;
    color: #ffffff !important;
    font-weight: 650 !important;
    letter-spacing: 0.01em !important;
    min-height: 2.7rem;
    padding: 0.5rem 1.15rem !important;
    overflow: hidden !important;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.18),
        0 1px 2px rgba(7, 17, 31, 0.16),
        0 6px 14px -6px rgba(15, 76, 129, 0.5) !important;
    transition:
        background 180ms ease,
        box-shadow 180ms ease,
        transform 140ms cubic-bezier(0.16, 1, 0.3, 1) !important;
}

/* Sheen sweep on hover — a single moving highlight, no permanent gloss. */
.stButton > button::after,
.stDownloadButton > button::after,
.stFormSubmitButton > button::after {
    content: "";
    position: absolute;
    inset: 0 auto 0 -60%;
    width: 45%;
    background: linear-gradient(
        100deg,
        transparent 0%,
        rgba(255, 255, 255, 0.22) 50%,
        transparent 100%
    );
    transform: skewX(-18deg);
    transition: left 520ms cubic-bezier(0.16, 1, 0.3, 1);
    pointer-events: none;
}

.stButton > button:hover::after,
.stDownloadButton > button:hover::after,
.stFormSubmitButton > button:hover::after {
    left: 115%;
}

.stButton > button:hover,
.stDownloadButton > button:hover,
.stFormSubmitButton > button:hover,
button[kind="primary"]:hover,
button[kind="secondary"]:hover,
button[kind="primaryFormSubmit"]:hover,
button[kind="secondaryFormSubmit"]:hover {
    background: linear-gradient(180deg, #2270b4 0%, #12558c 55%, var(--mdps-brand-strong) 100%) !important;
    border-color: #0a3560 !important;
    transform: translateY(-1px) !important;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.24),
        0 2px 4px rgba(7, 17, 31, 0.18),
        0 12px 22px -8px rgba(15, 76, 129, 0.55) !important;
    filter: none !important;
}

.stButton > button:active,
.stDownloadButton > button:active,
.stFormSubmitButton > button:active,
button[kind="primary"]:active,
button[kind="secondary"]:active,
button[kind="primaryFormSubmit"]:active,
button[kind="secondaryFormSubmit"]:active {
    transform: translateY(1px) !important;
    background: linear-gradient(180deg, #0c4373 0%, #0e4a7e 100%) !important;
    box-shadow:
        inset 0 2px 5px rgba(4, 24, 45, 0.45),
        0 1px 1px rgba(7, 17, 31, 0.12) !important;
}

.stButton > button:focus-visible,
.stDownloadButton > button:focus-visible,
.stFormSubmitButton > button:focus-visible {
    outline: none !important;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.18),
        0 0 0 3px rgba(15, 76, 129, 0.28) !important;
}

/* Secondary weight: the sidebar Logout and other in-panel actions should not
   compete with a page's primary action. */
[data-testid="stSidebar"] .stButton > button,
[data-testid="stSidebar"] .stFormSubmitButton > button,
[data-testid="stSidebar"] .stDownloadButton > button {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    color: #dbe4f0 !important;
    box-shadow: none !important;
}

[data-testid="stSidebar"] .stButton > button:hover,
[data-testid="stSidebar"] .stFormSubmitButton > button:hover,
[data-testid="stSidebar"] .stDownloadButton > button:hover {
    background: rgba(93, 183, 255, 0.14) !important;
    border-color: rgba(93, 183, 255, 0.4) !important;
    color: #ffffff !important;
    box-shadow: none !important;
}

div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div,
.stSelectbox > div,
div[data-baseweb="select"] > div {
    border-radius: var(--mdps-radius) !important;
    border-color: var(--mdps-line) !important;
    background: #ffffff !important;
}

div[data-baseweb="input"] > div:focus-within,
div[data-baseweb="textarea"] > div:focus-within,
div[data-baseweb="select"] > div:focus-within {
    border-color: var(--mdps-brand) !important;
    box-shadow: 0 0 0 3px rgba(15, 76, 129, 0.14) !important;
}

div[data-testid="stFileUploader"] section {
    border-radius: var(--mdps-radius) !important;
    background: #ffffff !important;
    border: 1px dashed var(--mdps-line-strong) !important;
}

.message-user,
.message-assistant {
    border-radius: var(--mdps-radius) !important;
    box-shadow: var(--mdps-shadow-soft) !important;
}

.message-user {
    background: var(--mdps-brand) !important;
}

.message-assistant {
    background: #ffffff !important;
}

.report-workspace {
    padding: 1.3rem !important;
}

.analysis-hero {
    gap: 1rem !important;
}

.signal-card.high {
    background: #fff7f6 !important;
    border-color: #f0b8b2 !important;
}

.signal-card.high .signal-score,
.risk-high,
.result-positive {
    color: var(--mdps-red) !important;
}

.risk-low,
.result-negative {
    color: var(--mdps-green) !important;
}

.result-positive,
.result-negative {
    border-radius: var(--mdps-radius) !important;
    box-shadow: var(--mdps-shadow-soft) !important;
}

.pulse-dot {
    animation: mdpsPulse 1.8s ease-out infinite !important;
}

@keyframes mdpsPageIn {
    from {
        opacity: 0;
        transform: translateY(8px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes mdpsPulse {
    0% {
        box-shadow: 0 0 0 0 rgba(8, 127, 123, 0.35);
    }
    75% {
        box-shadow: 0 0 0 9px rgba(8, 127, 123, 0);
    }
    100% {
        box-shadow: 0 0 0 0 rgba(8, 127, 123, 0);
    }
}

@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        scroll-behavior: auto !important;
        transition-duration: 0.01ms !important;
    }
}

@media (max-width: 980px) {
    .main .block-container {
        padding-top: 1.3rem;
    }

    .hero-banner {
        padding: 2rem 1.35rem !important;
    }
}
</style>
"""
