"""
Mutual Fund FAQ Assistant — Streamlit Entry Point

Premium Groww AI glassmorphism interface for factual Q&A on HDFC mutual fund schemes.
Run with: streamlit run src/app.py
"""

import sys
import os
import re
import streamlit as st

# Ensure project root is on the import path so `src.*` modules resolve
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.backend_app import process_query  # noqa: E402

# ──────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="Groww AI — Mutual Fund FAQ Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Design System — Premium Glassmorphism CSS
# ──────────────────────────────────────────────

GROWW_CSS = """
<style>
/* ── Google Font: Geist ── */
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&display=swap');

/* ══════════════════════════════════════════════
   DESIGN TOKENS (from DESIGN.md)
   ══════════════════════════════════════════════ */
:root {
    --surface:                 #111417;
    --surface-dim:             #111417;
    --surface-bright:          #37393d;
    --surface-container-lowest:#0b0e11;
    --surface-container-low:   #191c1f;
    --surface-container:       #1d2023;
    --surface-container-high:  #272a2e;
    --surface-container-highest:#323538;
    --on-surface:              #e1e2e7;
    --on-surface-variant:      #bacac1;
    --outline:                 #85948c;
    --outline-variant:         #3c4a43;
    --primary:                 #44edb7;
    --primary-container:       #00d09c;
    --on-primary:              #003828;
    --on-primary-container:    #00533c;
    --surface-tint:            #2fe0aa;
    --error:                   #ffb4ab;
    --background:              #111417;
}

/* ══════════════════════════════════════════════
   GLOBAL RESETS & BASE
   ══════════════════════════════════════════════ */
html, body, .stApp, [data-testid="stAppViewContainer"] {
    font-family: 'Geist', -apple-system, 'Segoe UI', sans-serif !important;
    background-color: var(--surface-container-lowest) !important;
    color: var(--on-surface) !important;
}

.stApp {
    background: var(--surface-container-lowest) !important;
}

/* Ambient background glow */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    top: 50%;
    left: 55%;
    transform: translate(-50%, -50%);
    width: 800px;
    height: 800px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(0, 208, 156, 0.06) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
    filter: blur(60px);
}

/* Scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--surface-container-highest); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: #43474e; }

/* ══════════════════════════════════════════════
   SIDEBAR STYLING
   ══════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: rgba(29, 32, 35, 0.6) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-right: 1px solid var(--outline-variant) !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    background: transparent !important;
    padding-top: 0 !important;
}

/* Sidebar header / branding */
[data-testid="stSidebar"] .sidebar-brand {
    padding: 24px 16px 16px;
    border-bottom: 1px solid rgba(60, 74, 67, 0.3);
    margin-bottom: 8px;
}

[data-testid="stSidebar"] .sidebar-brand h1 {
    font-family: 'Geist', sans-serif;
    font-size: 18px;
    font-weight: 700;
    color: var(--primary) !important;
    margin: 0;
    line-height: 1.3;
}

[data-testid="stSidebar"] .sidebar-brand p {
    font-size: 12px;
    color: var(--on-surface-variant);
    margin: 2px 0 0 0;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    font-weight: 500;
}

/* Sidebar buttons — New Chat (first button only) */
[data-testid="stSidebar"] .stButton > button {
    background: var(--primary-container) !important;
    color: var(--on-primary-container) !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Geist', sans-serif !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 12px 16px !important;
    width: 100% !important;
    transition: all 0.25s ease !important;
    margin-bottom: 8px !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--primary) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(0, 208, 156, 0.25) !important;
}

/* Sidebar recent chat buttons — subtle nav-item style */
[data-testid="stSidebar"] [class*="st-key-recent_"] .stButton > button {
    background: transparent !important;
    color: var(--on-surface-variant) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 400 !important;
    font-size: 13px !important;
    padding: 8px 12px !important;
    text-align: left !important;
    margin-bottom: 1px !important;
    box-shadow: none !important;
    transform: none !important;
    min-height: unset !important;
    height: auto !important;
}

[data-testid="stSidebar"] [class*="st-key-recent_"] .stButton > button:hover {
    background: rgba(255, 255, 255, 0.05) !important;
    color: var(--on-surface) !important;
    transform: none !important;
    box-shadow: none !important;
}

/* Sidebar nav links */
.sidebar-nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border-radius: 10px;
    color: var(--on-surface-variant);
    font-size: 14px;
    font-weight: 400;
    text-decoration: none;
    transition: all 0.2s ease;
    margin: 2px 0;
    cursor: default;
}

.sidebar-nav-item:hover {
    background: rgba(255, 255, 255, 0.04);
    color: var(--on-surface);
}

.sidebar-nav-item.active {
    background: rgba(255, 255, 255, 0.05);
    color: var(--primary);
    font-weight: 600;
}

.sidebar-nav-item .nav-icon {
    font-size: 20px;
    width: 24px;
    text-align: center;
}

.sidebar-section-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--on-surface-variant);
    padding: 16px 14px 6px;
    opacity: 0.7;
}

/* Sidebar disclaimer */
.sidebar-disclaimer {
    font-size: 11px;
    color: rgba(186, 202, 193, 0.4);
    text-align: center;
    padding: 16px 14px;
    border-top: 1px solid rgba(60, 74, 67, 0.3);
    margin-top: auto;
    line-height: 1.5;
}

/* ══════════════════════════════════════════════
   MAIN CONTENT AREA
   ══════════════════════════════════════════════ */

/* Remove default Streamlit padding/margins */
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

[data-testid="stMainBlockContainer"] {
    padding: 0 !important;
    max-width: 100% !important;
}

/* Hide Streamlit branding */
#MainMenu, footer, header[data-testid="stHeader"] {
    visibility: hidden;
    height: 0;
}

/* ══════════════════════════════════════════════
   WELCOME HERO SECTION
   ══════════════════════════════════════════════ */

.welcome-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px 20px;
    position: relative;
    z-index: 1;
}

.welcome-icon {
    width: 64px;
    height: 64px;
    border-radius: 16px;
    background: rgba(29, 32, 35, 0.5);
    border: 1px solid rgba(60, 74, 67, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 28px;
    backdrop-filter: blur(12px);
    box-shadow: 0 0 40px rgba(0, 208, 156, 0.08);
}

.welcome-icon svg {
    width: 32px;
    height: 32px;
    fill: var(--primary);
}

.welcome-title {
    font-family: 'Geist', sans-serif;
    font-size: 34px;
    font-weight: 600;
    color: var(--on-surface);
    margin-bottom: 10px;
    letter-spacing: -0.02em;
    text-align: center;
    line-height: 1.2;
}

.welcome-title .accent {
    color: var(--primary);
    font-weight: 700;
}

.welcome-subtitle {
    font-size: 16px;
    color: var(--on-surface-variant);
    margin-bottom: 40px;
    text-align: center;
    line-height: 1.6;
}

/* ══════════════════════════════════════════════
   EXAMPLE QUESTION CARDS — Styled Streamlit Buttons
   ══════════════════════════════════════════════ */

/* Style ALL main-area Streamlit buttons to look like design cards
   (sidebar buttons have their own overrides above) */
[data-testid="stMainBlockContainer"] .stButton > button,
[data-testid="stMain"] .stButton > button,
main .stButton > button {
    background: rgba(29, 32, 35, 0.35) !important;
    border: 1px solid #3c4a43 !important;
    border-radius: 14px !important;
    padding: 18px 20px !important;
    color: #e1e2e7 !important;
    font-family: 'Geist', sans-serif !important;
    font-size: 14px !important;
    font-weight: 400 !important;
    text-align: left !important;
    line-height: 1.5 !important;
    transition: all 0.25s ease !important;
    height: auto !important;
    min-height: 58px !important;
    width: 100% !important;
    margin-bottom: 0 !important;
    box-shadow: none !important;
}

[data-testid="stMainBlockContainer"] .stButton > button:hover,
[data-testid="stMain"] .stButton > button:hover,
main .stButton > button:hover {
    border-color: rgba(68, 237, 183, 0.45) !important;
    background: rgba(29, 32, 35, 0.6) !important;
    color: #44edb7 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3) !important;
}

[data-testid="stMainBlockContainer"] .stButton > button:active,
[data-testid="stMain"] .stButton > button:active,
main .stButton > button:active {
    transform: translateY(0px) !important;
}

[data-testid="stMainBlockContainer"] .stButton > button:focus,
[data-testid="stMain"] .stButton > button:focus,
main .stButton > button:focus {
    box-shadow: 0 0 0 2px rgba(68, 237, 183, 0.2) !important;
    border-color: rgba(68, 237, 183, 0.5) !important;
}

/* ══════════════════════════════════════════════
   CHAT MESSAGES
   ══════════════════════════════════════════════ */

/* Date divider */
.chat-date-divider {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    margin: 16px auto 24px;
    max-width: 800px;
    opacity: 0.5;
}

.chat-date-divider .line {
    flex: 1;
    height: 1px;
    background: var(--outline-variant);
}

.chat-date-divider .label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--on-surface-variant);
}

/* Override Streamlit chat message containers */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 4px 0 !important;
    margin-bottom: 8px !important;
    gap: 0 !important;
    max-width: 800px;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* Hide Streamlit's default avatar icons — aggressive targeting */
[data-testid="stChatMessage"] img[data-testid="chatAvatarIcon-user"],
[data-testid="stChatMessage"] img[data-testid="chatAvatarIcon-assistant"],
[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"],
[data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"],
[data-testid="stChatMessage"] .stChatMessageAvatarContainer,
[data-testid="stChatMessage"] [class*="Avatar"],
[data-testid="stChatMessage"] > div:first-child {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* USER BUBBLE — dark, right-aligned */
.user-bubble {
    background: var(--surface-container) !important;
    border: 1px solid rgba(60, 74, 67, 0.3);
    padding: 16px 20px;
    border-radius: 18px 18px 4px 18px;
    max-width: 78%;
    margin-left: auto;
    color: var(--on-surface);
    font-size: 15px;
    line-height: 1.6;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

/* AI / ASSISTANT BUBBLE — glass with green left border */
.ai-bubble-wrapper {
    display: flex;
    gap: 14px;
    max-width: 88%;
}

.ai-avatar {
    width: 34px;
    height: 34px;
    min-width: 34px;
    border-radius: 50%;
    background: rgba(68, 237, 183, 0.1);
    border: 1px solid rgba(68, 237, 183, 0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 2px;
    flex-shrink: 0;
}

.ai-avatar svg {
    width: 16px;
    height: 16px;
    fill: var(--primary);
}

.ai-bubble {
    background: rgba(25, 28, 31, 0.4);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--outline-variant);
    border-left: 2.5px solid var(--primary);
    padding: 18px 22px;
    border-radius: 18px 18px 18px 4px;
    color: var(--on-surface);
    font-size: 15px;
    line-height: 1.7;
    box-shadow: -20px 0 50px -20px rgba(0, 208, 156, 0.04);
    flex: 1;
}

.ai-bubble p {
    margin: 0 0 8px 0;
}

.ai-bubble p:last-child {
    margin-bottom: 0;
}

/* Clickable links inside AI bubble */
.ai-bubble a,
.ai-bubble a:visited {
    color: #44edb7 !important;
    text-decoration: underline !important;
    text-underline-offset: 3px !important;
    transition: opacity 0.2s ease !important;
    word-break: break-all !important;
}

.ai-bubble a:hover {
    opacity: 0.8 !important;
    text-decoration-color: rgba(68, 237, 183, 0.5) !important;
}

/* Source citation badge */
.source-citation {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: rgba(68, 237, 183, 0.08);
    border: 1px solid rgba(68, 237, 183, 0.2);
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12px;
    color: var(--primary);
    margin-top: 12px;
    text-decoration: none;
    transition: all 0.2s ease;
}

.source-citation:hover {
    background: rgba(68, 237, 183, 0.15);
    border-color: rgba(68, 237, 183, 0.4);
}

/* Footer / last-updated line */
.response-footer {
    font-size: 12px;
    color: rgba(186, 202, 193, 0.45);
    margin-top: 10px;
    display: flex;
    align-items: center;
    gap: 5px;
}

/* ══════════════════════════════════════════════
   CHAT INPUT AREA
   ══════════════════════════════════════════════ */

/* Dock the input at the bottom — hardcoded dark colors */
[data-testid="stBottom"],
[data-testid="stBottom"] > div,
[data-testid="stBottom"] > div > div,
[data-testid="stBottom"] * {
    background-color: #0b0e11 !important;
    border-top: none !important;
}

[data-testid="stBottom"] {
    background: linear-gradient(to top,
        #0b0e11 0%,
        #0b0e11 70%,
        transparent 100%
    ) !important;
    padding: 0 !important;
    border: none !important;
}

[data-testid="stBottom"] > div {
    max-width: 840px !important;
    margin: 0 auto !important;
    padding: 0 20px 12px !important;
    background: transparent !important;
}

/* Chat input box — use hardcoded colors for max specificity */
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
.stChatInput,
.stChatInput > div {
    background: #272a2e !important;
    border: 1px solid #3c4a43 !important;
    border-radius: 16px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
}

[data-testid="stChatInput"]:focus-within,
[data-testid="stChatInput"] > div:focus-within {
    border-color: #44edb7 !important;
    box-shadow: 0 0 0 2px rgba(68, 237, 183, 0.15), 0 8px 32px rgba(0, 0, 0, 0.3) !important;
}

[data-testid="stChatInput"] textarea,
.stChatInput textarea {
    background: transparent !important;
    border: none !important;
    color: #e1e2e7 !important;
    font-family: 'Geist', sans-serif !important;
    font-size: 15px !important;
    padding: 12px 16px !important;
    caret-color: #44edb7 !important;
}

[data-testid="stChatInput"] textarea::placeholder,
.stChatInput textarea::placeholder {
    color: rgba(186, 202, 193, 0.4) !important;
}

[data-testid="stChatInput"] textarea:focus,
.stChatInput textarea:focus {
    box-shadow: none !important;
    outline: none !important;
    border: none !important;
}

/* Send button — flat green, no inner box */
[data-testid="stChatInputSubmitButton"],
[data-testid="stChatInput"] button,
.stChatInput button {
    background-color: #00d09c !important;
    background: #00d09c !important;
    color: #111417 !important;
    border: none !important;
    border-radius: 10px !important;
    width: 34px !important;
    height: 34px !important;
    min-width: 34px !important;
    min-height: 34px !important;
    max-width: 34px !important;
    max-height: 34px !important;
    padding: 0 !important;
    margin: 4px 6px 4px 4px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.2s ease !important;
    box-shadow: none !important;
    outline: none !important;
    flex-shrink: 0 !important;
}

[data-testid="stChatInputSubmitButton"]:hover,
[data-testid="stChatInput"] button:hover,
.stChatInput button:hover {
    background-color: #44edb7 !important;
    background: #44edb7 !important;
    box-shadow: 0 0 20px rgba(0, 208, 156, 0.25) !important;
    transform: scale(1.05);
}

/* Force the SVG icon to be plain, no container styling */
[data-testid="stChatInputSubmitButton"] svg,
[data-testid="stChatInput"] button svg {
    fill: #111417 !important;
    color: #111417 !important;
    width: 18px !important;
    height: 18px !important;
}

/* Remove any inner div / span background that creates the black square */
[data-testid="stChatInputSubmitButton"] > *,
[data-testid="stChatInput"] button > * {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* Input disclaimer */
.input-disclaimer {
    text-align: center;
    font-size: 11px;
    color: rgba(186, 202, 193, 0.35);
    padding: 6px 0 0;
    letter-spacing: 0.02em;
}

/* ══════════════════════════════════════════════
   SPINNER OVERRIDE
   ══════════════════════════════════════════════ */

.stSpinner > div > div {
    border-top-color: var(--primary) !important;
}

.stSpinner > div > span {
    color: var(--on-surface-variant) !important;
    font-family: 'Geist', sans-serif !important;
}

/* ══════════════════════════════════════════════
   STREAMLIT ELEMENT OVERRIDES
   ══════════════════════════════════════════════ */

/* st.markdown text */
.stMarkdown p, .stMarkdown li, .stMarkdown {
    color: var(--on-surface) !important;
    font-family: 'Geist', sans-serif !important;
}

/* Divider */
[data-testid="stDivider"] {
    border-color: rgba(60, 74, 67, 0.3) !important;
}

/* Hide Streamlit's header bar */
header[data-testid="stHeader"] {
    display: none !important;
}
</style>

<!-- Material Symbols for icons -->
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&display=swap" rel="stylesheet">
"""

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

EXAMPLE_QUESTIONS = [
    ("🔍", "What is the expense ratio of HDFC Large Cap Fund?"),
    ("🛡️", "What is the risk category of HDFC Mid Cap Fund?"),
    ("📋", "What is the exit load for HDFC Small Cap Fund?"),
    ("💰", "What is the minimum SIP amount for HDFC Mid Cap Fund?"),
]

BOLT_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M11 21h-1l1-7H7.5c-.88 0-.33-.75-.31-.78C8.48 10.94 10.42 7.54 13.01 3h1l-1 7h3.51c.4 0 .62.19.4.66C12.97 17.55 11 21 11 21z"/></svg>'

SPARKLE_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2L13.09 8.26L18 6L15.74 10.91L22 12L15.74 13.09L18 18L13.09 15.74L12 22L10.91 15.74L6 18L8.26 13.09L2 12L8.26 10.91L6 6L10.91 8.26L12 2Z"/></svg>'


# ──────────────────────────────────────────────
# Inject CSS
# ──────────────────────────────────────────────

st.markdown(GROWW_CSS, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Session State Initialisation
# ──────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_example" not in st.session_state:
    st.session_state.pending_example = None

if "recents" not in st.session_state:
    st.session_state.recents = []  # list of {"title": str, "messages": list}

if "load_recent" not in st.session_state:
    st.session_state.load_recent = None

if "active_recent_idx" not in st.session_state:
    st.session_state.active_recent_idx = None  # index of currently-loaded recent chat

# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────

with st.sidebar:
    # Brand header
    st.markdown(
        """
        <div class="sidebar-brand">
            <h1>Groww AI</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # New Chat button
    if st.button("+  New Chat", key="new_chat", use_container_width=True):
        # Only save to recents if this is a NEW chat (not one loaded from recents)
        if st.session_state.messages and st.session_state.active_recent_idx is None:
            first_user_msg = next(
                (
                    m["content"]
                    for m in st.session_state.messages
                    if m["role"] == "user"
                ),
                "Untitled Chat",
            )
            st.session_state.recents.insert(
                0,
                {"title": first_user_msg, "messages": list(st.session_state.messages)},
            )
        st.session_state.messages = []
        st.session_state.pending_example = None
        st.session_state.active_recent_idx = None
        st.rerun()

    # Recents navigation — clickable nav items
    st.markdown(
        '<div class="sidebar-section-label">RECENTS</div>', unsafe_allow_html=True
    )
    if not st.session_state.recents:
        st.markdown(
            '<div class="sidebar-nav-item" style="opacity: 0.5; font-size: 13px;">No recent chats</div>',
            unsafe_allow_html=True,
        )
    else:
        for idx, recent in enumerate(st.session_state.recents):
            title = recent["title"]
            display_title = title[:28] + "…" if len(title) > 28 else title
            with st.container(key=f"recent_{idx}"):
                if st.button(
                    f"💬  {display_title}",
                    key=f"recent_btn_{idx}",
                    use_container_width=True,
                ):
                    st.session_state.load_recent = idx
                    st.rerun()

    st.markdown("---")

    # Covered schemes info
    st.markdown(
        """
        <div class="sidebar-section-label">COVERED SCHEMES</div>
        <div class="sidebar-nav-item">
            <span class="nav-icon" style="font-size:14px;">📈</span>
            HDFC Large Cap
        </div>
        <div class="sidebar-nav-item">
            <span class="nav-icon" style="font-size:14px;">📊</span>
            HDFC Mid Cap
        </div>
        <div class="sidebar-nav-item">
            <span class="nav-icon" style="font-size:14px;">🚀</span>
            HDFC Small Cap
        </div>
        <div class="sidebar-nav-item">
            <span class="nav-icon" style="font-size:14px;">🥇</span>
            HDFC Gold ETF FoF
        </div>
        <div class="sidebar-nav-item">
            <span class="nav-icon" style="font-size:14px;">🪙</span>
            HDFC Silver ETF FoF
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Bottom links
    st.markdown("---")
    st.markdown(
        """
        <div class="sidebar-nav-item">
            <span class="nav-icon material-symbols-outlined">help</span>
            Help Center
        </div>
        <div class="sidebar-nav-item">
            <span class="nav-icon material-symbols-outlined">settings</span>
            Settings
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Disclaimer
    st.markdown(
        """
        <div class="sidebar-disclaimer">
            ⚠️ Facts-only assistant. No investment advice.<br>
            Data sourced from Groww.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────
# Query Processing Helper
# ──────────────────────────────────────────────


def _linkify(text: str) -> str:
    """Convert bare URLs in text to clickable <a> tags."""
    url_pattern = re.compile(
        r'(?<!["=\'>])'  # not preceded by href= or src= etc.
        r'(https?://[^\s<>"\)]+)',
        re.IGNORECASE,
    )
    return url_pattern.sub(
        r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>', text
    )


def _render_ai_content(raw: str) -> str:
    """Convert raw response text to HTML with clickable links."""
    html = raw.replace("\n", "<br>")
    html = _linkify(html)
    return html


def _handle_query(query: str) -> None:
    """Append user message, call backend, append assistant response."""
    # Persist user message
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(
            f'<div class="user-bubble">{query}</div>',
            unsafe_allow_html=True,
        )

    # Show spinner then generate response
    with st.chat_message("assistant"):
        with st.spinner("Groww AI is thinking..."):
            response = process_query(query)

        content = _render_ai_content(response)
        st.markdown(
            f"""
            <div class="ai-bubble-wrapper">
                <div class="ai-avatar">{BOLT_SVG}</div>
                <div class="ai-bubble">
                    {content}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.session_state.messages.append({"role": "assistant", "content": response})


# ──────────────────────────────────────────────
# Load a recent chat if requested
# ──────────────────────────────────────────────

if st.session_state.load_recent is not None:
    idx = st.session_state.load_recent
    st.session_state.load_recent = None
    if 0 <= idx < len(st.session_state.recents):
        # Save current chat only if it's a genuinely new conversation
        if st.session_state.messages and st.session_state.active_recent_idx is None:
            first_user_msg = next(
                (
                    m["content"]
                    for m in st.session_state.messages
                    if m["role"] == "user"
                ),
                "Untitled Chat",
            )
            st.session_state.recents.append(
                {"title": first_user_msg, "messages": list(st.session_state.messages)}
            )
        # Load selected chat and mark it as active
        st.session_state.messages = list(st.session_state.recents[idx]["messages"])
        st.session_state.active_recent_idx = idx

# ──────────────────────────────────────────────
# Determine the current query (from pending example or chat input)
# ──────────────────────────────────────────────

# Grab pending example BEFORE rendering
_pending = st.session_state.pending_example
if _pending:
    st.session_state.pending_example = None

# Chat input (always visible at the bottom)
user_input = st.chat_input("Ask anything about HDFC mutual funds...")

# Determine if there is a new query to process
new_query = _pending or user_input or None


# ──────────────────────────────────────────────
# Welcome Screen (when no chat history and no new query)
# ──────────────────────────────────────────────

if not st.session_state.messages and not new_query:
    # Welcome hero (pure HTML — no JS)
    st.markdown(
        f"""
        <div class="welcome-container">
            <div class="welcome-icon">
                {SPARKLE_SVG}
            </div>
            <div class="welcome-title">
                Welcome to <span class="accent">Groww AI</span>
            </div>
            <div class="welcome-subtitle">
                How can I help you navigate HDFC mutual fund schemes today?
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Example question buttons — 2 columns grid (centered)
    spacer1, center_col, spacer2 = st.columns([1, 6, 1])
    with center_col:
        for row_start in range(0, len(EXAMPLE_QUESTIONS), 2):
            row = EXAMPLE_QUESTIONS[row_start : row_start + 2]
            cols = st.columns(2)
            for idx_in_row, (col, (icon, question)) in enumerate(zip(cols, row)):
                global_idx = row_start + idx_in_row
                with col:
                    if st.button(
                        f"{icon}  {question}",
                        key=f"example_{global_idx}",
                        use_container_width=True,
                    ):
                        st.session_state.pending_example = question
                        st.rerun()


# ──────────────────────────────────────────────
# Chat View (when messages exist or new query)
# ──────────────────────────────────────────────

if st.session_state.messages or new_query:
    # Date divider
    st.markdown(
        """
        <div class="chat-date-divider">
            <div class="line"></div>
            <span class="label">Today</span>
            <div class="line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Render existing messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(
                    f'<div class="user-bubble">{msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
        else:
            with st.chat_message("assistant"):
                content = _render_ai_content(msg["content"])
                st.markdown(
                    f"""
                    <div class="ai-bubble-wrapper">
                        <div class="ai-avatar">{BOLT_SVG}</div>
                        <div class="ai-bubble">
                            {content}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # Process new query
    if new_query:
        _handle_query(new_query)


# Input area disclaimer
st.markdown(
    '<div class="input-disclaimer">Groww AI can make mistakes. Verify important financial data.</div>',
    unsafe_allow_html=True,
)
