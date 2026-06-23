# Dashboard 공통 스타일
import streamlit as st

CUSTOM_CSS = """
<style>
    .stApp {
        background-color: #ffffff;
    }
    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 2rem;
        max-width: 1180px;
    }
    .stApp section[data-testid="stSidebar"],
    .stApp [data-testid="stSidebar"] {
        background: #eef6ff !important;
    }
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div,
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div,
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {
        background-color: #eef6ff !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        background: transparent !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff !important;
        border-color: #dbeafe !important;
    }
    section[data-testid="stSidebar"] {
        border-right: 1px solid #dbeafe;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.25rem;
        font-size: 0.82rem;
        color: #475569;
        background-color: transparent !important;
    }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        font-size: 0.82rem !important;
    }
    [data-testid="stSidebar"] .section-label {
        font-size: 0.65rem;
        color: #64748b;
    }
    [data-testid="stSidebar"] div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #dbeafe;
        border-radius: 10px;
        padding: 0.65rem 0.75rem;
    }
    [data-testid="stSidebar"] div[data-testid="stMetric"] label {
        font-size: 0.72rem !important;
    }
    [data-testid="stSidebar"] div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.05rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stSlider"] label {
        font-size: 0.78rem !important;
    }
    div[data-testid="stMetric"] {
        background: #fafafa;
        border: 1px solid #f0f0f0;
        border-radius: 12px;
        padding: 0.9rem 1rem;
        box-shadow: none;
    }
    div[data-testid="stMetric"] label {
        color: #6b7280 !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #111827 !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important;
        border-color: #f0f0f0 !important;
        box-shadow: none !important;
        background: #ffffff !important;
        padding: 0.25rem 0.5rem;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid #f0f0f0;
        border-radius: 10px;
        overflow: hidden;
    }
    [data-testid="stDataFrame"] div[role="gridcell"] {
        font-size: 0.88rem;
    }
    h2, h3 {
        color: #111827 !important;
        font-weight: 600 !important;
    }
    .dashboard-header {
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #f3f4f6;
    }
    .dashboard-header h1 {
        font-size: 1.6rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0;
        letter-spacing: -0.02em;
    }
    .section-label {
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #9ca3af;
        margin-bottom: 0.35rem;
    }
    hr {
        margin: 0.75rem 0;
        border-color: #f3f4f6;
    }
</style>
"""


def apply_dashboard_styles() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_header(title: str, subtitle: str | None = None) -> None:
    subtitle_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div class="dashboard-header">
            <h1>{title}</h1>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
