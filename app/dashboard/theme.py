# Dashboard 테마 상수 (streamlit 미사용)

CHART_COLORS = ["#1d4ed8", "#2563eb", "#3b82f6", "#60a5fa", "#93c5fd", "#bfdbfe", "#dbeafe"]
CTR_COLOR = "#1d4ed8"
CVR_COLOR = "#0ea5e9"

PLOTLY_LAYOUT = {
    "paper_bgcolor": "#ffffff",
    "plot_bgcolor": "#ffffff",
    "margin": {"l": 8, "r": 16, "t": 44, "b": 8},
    "font": {"family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif", "color": "#374151"},
    "title": {"font": {"size": 14, "color": "#111827"}, "x": 0},
    "legend": {
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "right",
        "x": 1,
        "bgcolor": "rgba(0,0,0,0)",
    },
    "xaxis": {
        "showgrid": True,
        "gridcolor": "#f3f4f6",
        "linecolor": "#e5e7eb",
        "tickfont": {"color": "#6b7280", "size": 11},
        "title_font": {"color": "#6b7280", "size": 11},
    },
    "yaxis": {
        "showgrid": False,
        "linecolor": "#e5e7eb",
        "tickfont": {"color": "#4b5563", "size": 11},
        "title_font": {"color": "#6b7280", "size": 11},
    },
    "coloraxis_colorbar": {
        "tickfont": {"color": "#6b7280"},
        "outlinewidth": 0,
    },
}
