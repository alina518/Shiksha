"""
NGO Education Impact Dashboard — Fixed & Updated
=================================================
Fixes:
  - Attendance trend: aggregated properly, fallback to bar if sparse
  - Scatter: correct bubble sizing, all schools shown
  - Instructor: replaced bar chart with dropdown selector showing instructor stats
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NGO Education Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_URI = "mysql+pymysql://root:root@localhost:3306/ngo_mart"
engine = create_engine(DB_URI)

# ─────────────────────────────────────────────────────────────
# GLOBAL STYLES
# ─────────────────────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">

<style>
html, body, [class*="css"] {
    font-family: 'DM Sans', system-ui, sans-serif !important;
    font-size: 14px;
    color: #1a1d23;
}
.stApp { background: #f0f2f5 !important; }
#MainMenu, footer, header { visibility: hidden; }

/* ── Sidebar ── */
section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] > div:first-child {
    background: #1c2333 !important;
    border-right: none !important;
}
section[data-testid="stSidebar"] * { color: #a8b3c8 !important; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] label {
    color: #63708a !important;
    font-size: 10px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #242d40 !important;
    border: 1px solid #2e3a50 !important;
    color: #c5cfe0 !important;
    border-radius: 6px !important;
}
section[data-testid="stSidebar"] hr {
    border-color: #2a3347 !important;
    margin: 20px 0 !important;
}

.sb-brand {
    padding: 28px 20px 20px;
    border-bottom: 1px solid #2a3347;
    margin-bottom: 24px;
}
.sb-brand-logo {
    width: 38px; height: 38px;
    background: linear-gradient(135deg, #3b7dd8, #56c0e0);
    border-radius: 10px;
    display: inline-flex; align-items: center; justify-content: center;
    margin-bottom: 12px;
}
.sb-brand-logo i { color: #fff !important; font-size: 18px; }
.sb-brand h2 {
    color: #edf0f7 !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    margin: 0 0 2px !important;
    letter-spacing: -0.01em;
}
.sb-brand small {
    color: #4a5a73 !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
.sb-section-label {
    color: #3d5068 !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    padding: 0 20px 8px;
    display: block;
}
.sb-stat-block {
    background: #1f2b3e;
    border: 1px solid #2a3a52;
    border-radius: 8px;
    padding: 14px 16px;
    margin: 0 12px 8px;
}
.sb-stat-label { color: #4e6280 !important; font-size: 10px !important; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; }
.sb-stat-val { color: #7ec8e3 !important; font-size: 22px !important; font-weight: 700 !important; line-height: 1.2; margin-top: 2px; }

/* ── Page Header ── */
.page-header {
    background: #fff;
    border-radius: 10px;
    border: 1px solid #e3e7ef;
    padding: 20px 28px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.page-header-left h1 {
    font-size: 20px !important;
    font-weight: 700 !important;
    color: #111827 !important;
    margin: 0 0 4px !important;
    letter-spacing: -0.02em;
}
.page-header-left .breadcrumb {
    font-size: 12px; color: #8fa3bb;
    display: flex; align-items: center; gap: 6px;
}
.status-pill {
    background: #ecfdf5; border: 1px solid #86efac;
    color: #15803d !important; border-radius: 20px;
    padding: 4px 12px; font-size: 12px; font-weight: 600;
}

/* ── KPI Cards ── */
.kpi-card {
    background: #fff;
    border-radius: 10px;
    border: 1px solid #e3e7ef;
    padding: 20px 22px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    margin-bottom: 0;
}
.kpi-icon {
    width: 48px; height: 48px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; flex-shrink: 0;
}
.kpi-icon.blue   { background: #eff6ff; color: #2563eb !important; }
.kpi-icon.green  { background: #f0fdf4; color: #16a34a !important; }
.kpi-icon.amber  { background: #fffbeb; color: #d97706 !important; }
.kpi-icon.purple { background: #faf5ff; color: #7c3aed !important; }
.kpi-icon.cyan   { background: #ecfeff; color: #0891b2 !important; }
.kpi-body { flex: 1; min-width: 0; }
.kpi-label {
    font-size: 11px; font-weight: 600; color: #8fa3bb;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.kpi-value { font-size: 28px; font-weight: 700; color: #111827; line-height: 1.1; font-family: 'DM Mono', monospace !important; }
.kpi-sub   { font-size: 11px; color: #b0bec5; margin-top: 3px; }
.kpi-delta {
    font-size: 11px; font-weight: 600; padding: 2px 8px;
    border-radius: 20px; flex-shrink: 0;
}
.kpi-delta.up   { background: #dcfce7; color: #16a34a !important; }
.kpi-delta.down { background: #fee2e2; color: #dc2626 !important; }

/* ── Chart Cards ── */
.chart-card-header {
    background: #fff;
    border: 1px solid #e3e7ef;
    border-bottom: none;
    border-radius: 10px 10px 0 0;
    padding: 14px 20px;
    display: flex; align-items: center; gap: 10px;
}
.chart-card-header .cc-icon {
    width: 30px; height: 30px; border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px;
}
.cc-icon.blue   { background: #eff6ff; color: #2563eb !important; }
.cc-icon.green  { background: #f0fdf4; color: #16a34a !important; }
.cc-icon.amber  { background: #fffbeb; color: #d97706 !important; }
.cc-icon.purple { background: #faf5ff; color: #7c3aed !important; }
.cc-icon.cyan   { background: #ecfeff; color: #0891b2 !important; }
.chart-card-header .cc-title {
    font-size: 13px; font-weight: 600; color: #1f2937;
}
.chart-card-header .cc-sub {
    font-size: 11px; color: #9ca3af; margin-top: 1px;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 0 0 10px 10px !important;
    border: 1px solid #e3e7ef !important;
    border-top: none !important;
    background: #fff !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
    margin-bottom: 4px !important;
    padding: 0 4px 4px !important;
}

/* ── Instructor Dropdown Card ── */
.instructor-card {
    background: #fff;
    border-radius: 0 0 10px 10px;
    border: 1px solid #e3e7ef;
    border-top: none;
    padding: 20px 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.instructor-profile {
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 20px;
    background: #f8fafc;
    border-radius: 10px;
    border: 1px solid #e3e7ef;
    margin-top: 16px;
}
.instructor-avatar {
    width: 64px; height: 64px;
    border-radius: 50%;
    background: linear-gradient(135deg, #3b7dd8, #56c0e0);
    display: flex; align-items: center; justify-content: center;
    font-size: 24px; color: #fff;
    flex-shrink: 0;
    font-weight: 700;
}
.instructor-name { font-size: 18px; font-weight: 700; color: #111827; }
.instructor-meta { font-size: 12px; color: #6b7280; margin-top: 2px; }
.instructor-stat-row {
    display: flex; gap: 16px; margin-top: 16px; flex-wrap: wrap;
}
.instructor-stat {
    background: #fff;
    border: 1px solid #e3e7ef;
    border-radius: 8px;
    padding: 12px 18px;
    flex: 1; min-width: 120px;
    text-align: center;
}
.instructor-stat-val { font-size: 24px; font-weight: 700; color: #3b7dd8; font-family: 'DM Mono', monospace; }
.instructor-stat-lbl { font-size: 11px; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 2px; }

/* ── Section Labels ── */
.section-label {
    font-size: 11px; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: #6b7280;
    padding: 6px 0 10px; border-bottom: 1px solid #e3e7ef;
    margin-bottom: 16px;
    display: flex; align-items: center; gap: 8px;
}
.section-label::before {
    content: '';
    display: inline-block;
    width: 3px; height: 14px;
    background: #3b7dd8;
    border-radius: 2px;
}

/* ── Alert Callout ── */
.alert-card {
    background: #fff;
    border-radius: 10px;
    border: 1px solid #e3e7ef;
    border-left: 4px solid #f59e0b;
    padding: 16px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    margin-bottom: 16px;
}
.alert-card.danger { border-left-color: #ef4444; }
.alert-card-head {
    display: flex; align-items: center; gap: 10px; margin-bottom: 6px;
}
.alert-badge {
    margin-left: auto; background: #f59e0b; color: #fff !important;
    border-radius: 12px; padding: 2px 10px; font-size: 12px; font-weight: 700;
}
.alert-badge.red { background: #ef4444; }
.alert-title { font-size: 14px; font-weight: 700; color: #111827; }
.alert-body  { font-size: 13px; color: #6b7280; line-height: 1.5; }

/* ── Expanders ── */
[data-testid="stExpander"] {
    border: 1px solid #e3e7ef !important;
    border-radius: 10px !important;
    background: #fff !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
    margin-bottom: 12px !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary {
    font-weight: 600 !important; font-size: 13px !important;
    color: #1f2937 !important; padding: 14px 16px !important;
    background: #fafbfc !important;
}

/* ── Layout ── */
.block-container {
    padding: 1.5rem 2rem !important;
    max-width: 100% !important;
}
.spacer { margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# CHART THEME
# ─────────────────────────────────────────────────────────────
PALETTE = ["#3b7dd8", "#10b981", "#f59e0b", "#ef4444", "#0891b2", "#7c3aed", "#ec4899"]

PLOTLY_BASE = dict(
    font=dict(family="DM Sans, system-ui, sans-serif", size=12, color="#4b5563"),
    plot_bgcolor="#ffffff",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=20, t=10, b=45),
    xaxis=dict(gridcolor="#f3f4f6", linecolor="#e5e7eb", tickfont=dict(size=11), title_font=dict(size=12, color="#6b7280")),
    yaxis=dict(gridcolor="#f3f4f6", linecolor="#e5e7eb", tickfont=dict(size=11), title_font=dict(size=12, color="#6b7280")),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11), borderwidth=0),
    colorway=PALETTE,
)

def theme(fig, height=320):
    fig.update_layout(**PLOTLY_BASE, height=height)
    fig.update_layout(title_text="")
    return fig

# ─────────────────────────────────────────────────────────────
# HTML HELPERS
# ─────────────────────────────────────────────────────────────
def kpi(icon, icon_cls, label, value, sub="", delta=None, delta_up=True):
    delta_html = ""
    if delta:
        d_cls = "up" if delta_up else "down"
        d_arrow = "↑" if delta_up else "↓"
        delta_html = f'<span class="kpi-delta {d_cls}">{d_arrow} {delta}</span>'
    return f"""
    <div class="kpi-card">
        <div class="kpi-icon {icon_cls}"><i class="{icon}"></i></div>
        <div class="kpi-body">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {'<div class="kpi-sub">' + sub + '</div>' if sub else ''}
        </div>
        {delta_html}
    </div>"""

def chart_header(title, sub, icon, icon_cls):
    st.markdown(f"""
    <div class="chart-card-header">
        <div class="cc-icon {icon_cls}"><i class="{icon}"></i></div>
        <div>
            <div class="cc-title">{title}</div>
            {'<div class="cc-sub">' + sub + '</div>' if sub else ''}
        </div>
    </div>""", unsafe_allow_html=True)

def section(text, icon=""):
    prefix = f'<i class="{icon}" style="color:#3b7dd8"></i> ' if icon else ""
    st.markdown(f'<div class="section-label">{prefix}{text}</div>', unsafe_allow_html=True)

def spacer():
    st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# DATA LOADERS
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_school_performance():
    return pd.read_sql("SELECT * FROM vw_school_performance WHERE year IS NOT NULL AND month IS NOT NULL", engine)

@st.cache_data(ttl=300)
def load_program_effectiveness():
    return pd.read_sql("SELECT * FROM vw_program_effectiveness", engine)

@st.cache_data(ttl=300)
def load_rural_urban():
    return pd.read_sql("SELECT * FROM vw_rural_urban_comparison", engine)

@st.cache_data(ttl=300)
def load_instructor_performance():
    return pd.read_sql("SELECT * FROM vw_instructor_performance", engine)

@st.cache_data(ttl=300)
def load_exposure():
    return pd.read_sql("SELECT * FROM vw_exposure_metrics", engine)

# ─────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────
school_df_raw = load_school_performance()
program_df    = load_program_effectiveness()
ru_df         = load_rural_urban()
inst_df       = load_instructor_performance()
exp_df        = load_exposure()

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
        <div class="sb-brand-logo"><i class="fa-solid fa-graduation-cap"></i></div>
        <h2>NGO Portal</h2>
        <small>Education Impact Suite</small>
    </div>
    <span class="sb-section-label">Filters</span>
    """, unsafe_allow_html=True)

    years = sorted(school_df_raw["year"].dropna().unique())
    selected_year = st.selectbox("Academic Year", years)

    states = sorted(school_df_raw["state"].dropna().unique())
    selected_state = st.selectbox("State", ["All"] + states)

    st.markdown("---")

    total_schools  = school_df_raw["school_name"].nunique()
    total_programs = program_df["program_name"].nunique()

    st.markdown(f"""
    <span class="sb-section-label" style="padding-top:0">Quick Stats</span>
    <div class="sb-stat-block">
        <div class="sb-stat-label">Schools Tracked</div>
        <div class="sb-stat-val">{total_schools}</div>
    </div>
    <div class="sb-stat-block">
        <div class="sb-stat-label">Active Programs</div>
        <div class="sb-stat-val">{total_programs}</div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────────────────────
school_df = school_df_raw[school_df_raw["year"] == selected_year].copy()
if selected_state != "All":
    school_df = school_df[school_df["state"] == selected_state]

school_agg = school_df.groupby(["school_name", "state", "urban_rural"], as_index=False).agg(
    attendance_pct=("attendance_pct", "mean"),
    score_pct=("score_pct", "mean"),
)
school_agg["attendance_pct"] = school_agg["attendance_pct"].round(1)
school_agg["score_pct"]      = school_agg["score_pct"].round(1)

# ─────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────
state_label = selected_state if selected_state != "All" else "All States"
avg_att   = school_agg["attendance_pct"].mean() if not school_agg.empty else 0
avg_score = school_agg["score_pct"].mean()      if not school_agg.empty else 0

st.markdown(f"""
<div class="page-header">
    <div class="page-header-left">
        <h1><i class="fa-solid fa-chart-line" style="color:#3b7dd8;margin-right:10px;font-size:18px;"></i>Education Impact Dashboard</h1>
        <div class="breadcrumb">
            <i class="fa-solid fa-house"></i>
            <span style="color:#d1d5db;">/</span>
            <span>Reports</span>
            <span style="color:#d1d5db;">/</span>
            <strong style="color:#374151;">School Performance · {selected_year} · {state_label}</strong>
        </div>
    </div>
    <div style="display:flex;align-items:center;gap:8px;">
        <span class="status-pill"><i class="fa-solid fa-circle" style="font-size:8px;margin-right:5px;"></i>Live Data</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# KPI ROW
# ─────────────────────────────────────────────────────────────
section("Overview Metrics", "fa-solid fa-gauge-high")

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(kpi("fa-solid fa-user-graduate", "blue",
        "Students Reached", f"{int(exp_df['total_students'][0]):,}",
        "Cumulative"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi("fa-solid fa-chalkboard-user", "green",
        "Teachers Engaged", f"{int(exp_df['total_teachers'][0]):,}",
        "Active this period"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi("fa-solid fa-earth-asia", "amber",
        "Community Reach", f"{int(exp_df['community_reach'][0]):,}",
        "Beyond classroom"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi("fa-solid fa-calendar-check", "purple",
        "Avg Attendance", f"{avg_att:.1f}%",
        f"{selected_year} · {state_label}"), unsafe_allow_html=True)
with k5:
    st.markdown(kpi("fa-solid fa-star", "cyan",
        "Avg Score", f"{avg_score:.1f}%",
        f"{selected_year} · {state_label}"), unsafe_allow_html=True)

spacer()

# ─────────────────────────────────────────────────────────────
# ROW 1 — Attendance Trend + Score vs Attendance Scatter
# ─────────────────────────────────────────────────────────────
section("School Performance", "fa-solid fa-school")

r1c1, r1c2 = st.columns(2)

# ── Chart 1: Monthly Attendance Trend ──────────────────────
with r1c1:
    chart_header(
        "Monthly Attendance Trend",
        "Attendance % by school across months",
        "fa-solid fa-calendar-days", "blue"
    )
    with st.container(border=True):
        MONTH_NAMES = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                       7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

        monthly_raw = school_df.dropna(subset=["month", "attendance_pct"]).copy()

        # Clean values
        monthly_raw = monthly_raw[
            (monthly_raw["attendance_pct"] > 0) &
            (monthly_raw["attendance_pct"] <= 100)
            ]

        monthly_raw["month"] = monthly_raw["month"].astype(int)

        if monthly_raw.empty:
            st.info("No monthly data available for selected filters.")
        else:
            # 🔥 KEY CHANGE: DO NOT REMOVE SCHOOLS
            # Aggregate directly
            monthly_avg = (
                monthly_raw
                .groupby(["month", "school_name"], as_index=False)["attendance_pct"]
                .mean()
            )

            MONTH_NAMES = {
                1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
            }

            monthly_avg["month_label"] = monthly_avg["month"].map(MONTH_NAMES)
            monthly_avg = monthly_avg.sort_values("month")

            unique_months = monthly_avg["month"].nunique()
            unique_schools = monthly_avg["school_name"].nunique()

            # 🔥 SMART SWITCHING LOGIC
            if unique_months >= 2:
                fig1 = px.line(
                    monthly_avg,
                    x="month_label",
                    y="attendance_pct",
                    color="school_name",
                    markers=True,
                )
            else:
                # fallback: show ALL schools (not filtered ones)
                school_avg = (
                    monthly_raw
                    .groupby("school_name", as_index=False)["attendance_pct"]
                    .mean()
                    .sort_values("attendance_pct", ascending=False)
                )

                fig1 = px.bar(
                    school_avg,
                    x="school_name",
                    y="attendance_pct",
                    text="attendance_pct"
                )

            fig1 = theme(fig1)
            fig1.update_layout(
                yaxis=dict(range=[0, 100]),
                xaxis_title="Month" if unique_months >= 2 else "School",
                yaxis_title="Attendance %",
                legend_title="School"
            )

            st.plotly_chart(fig1, use_container_width=True)

# ── Chart 2: Score vs Attendance Scatter ───────────────────
with r1c2:
    chart_header(
        "Score vs Attendance by School",
        "Each bubble = one school; color = area type",
        "fa-solid fa-chart-scatter", "purple"
    )
    with st.container(border=True):
        if school_agg.empty:
            st.info("No data for selected filters.")
        else:
            scatter_df = school_agg.dropna(subset=["attendance_pct", "score_pct"]).copy()

            if scatter_df.empty:
                st.info("No valid score/attendance data to display.")
            else:
                # Fixed bubble size — uniform so all schools show up clearly
                scatter_df["bubble_size"] = 20

                fig2 = px.scatter(
                    scatter_df,
                    x="attendance_pct",
                    y="score_pct",
                    color="urban_rural",
                    size="bubble_size",
                    size_max=22,
                    hover_name="school_name",
                    hover_data={
                        "attendance_pct": ":.1f",
                        "score_pct": ":.1f",
                        "bubble_size": False,
                        "urban_rural": False,
                    },
                    color_discrete_map={
                        "Urban": "#3b7dd8",
                        "Rural": "#10b981",
                        "Unknown": "#9ca3af",
                    },
                )
                fig2 = theme(fig2)
                fig2.update_layout(
                    xaxis_title="Attendance %",
                    yaxis_title="Score %",
                    legend_title="Area Type",
                    xaxis=dict(range=[0, 110]),
                    yaxis=dict(range=[0, 110]),
                )
                fig2.add_hline(y=50, line_dash="dot", line_color="#e5e7eb", line_width=1)
                fig2.add_vline(x=50, line_dash="dot", line_color="#e5e7eb", line_width=1)
                st.plotly_chart(fig2, use_container_width=True)

spacer()

# ─────────────────────────────────────────────────────────────
# ROW 2 — Program Effectiveness + Rural vs Urban
# ─────────────────────────────────────────────────────────────
section("Program & Regional Analysis", "fa-solid fa-book-open")

r2c1, r2c2 = st.columns(2)

with r2c1:
    chart_header(
        "Program Effectiveness",
        "Attendance % vs Score % per program",
        "fa-solid fa-clipboard-check", "green"
    )
    with st.container(border=True):
        if program_df.empty:
            st.info("No program data available.")
        else:
            prog = program_df.dropna(subset=["attendance_pct", "score_pct"])
            prog = prog.sort_values("score_pct", ascending=False)

            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                name="Attendance %",
                x=prog["program_name"],
                y=prog["attendance_pct"],
                marker_color="#3b7dd8",
                text=prog["attendance_pct"].round(1).astype(str) + "%",
                textposition="outside",
                textfont=dict(size=10),
            ))
            fig3.add_trace(go.Bar(
                name="Score %",
                x=prog["program_name"],
                y=prog["score_pct"],
                marker_color="#10b981",
                text=prog["score_pct"].round(1).astype(str) + "%",
                textposition="outside",
                textfont=dict(size=10),
            ))
            fig3.update_layout(barmode="group")
            fig3 = theme(fig3)
            fig3.update_layout(
                xaxis_tickangle=-30,
                xaxis_title="Program",
                yaxis_title="Percentage (%)",
                legend_title="Metric",
                yaxis=dict(range=[0, 115]),
            )
            st.plotly_chart(fig3, use_container_width=True)

with r2c2:
    chart_header(
        "Rural vs Urban Comparison",
        "Attendance % and Score % by area type",
        "fa-solid fa-map-location-dot", "amber"
    )
    with st.container(border=True):
        ru_clean = ru_df[ru_df["urban_rural"].notna()].copy()
        ru_clean = ru_clean[ru_clean["urban_rural"].str.strip() != ""]
        ru_clean = ru_clean[
            (ru_clean["attendance_pct"].fillna(0) > 0) |
            (ru_clean["score_pct"].fillna(0) > 0)
        ]

        if ru_clean.empty:
            st.info("No rural/urban data available.")
        else:
            fig4 = go.Figure()
            fig4.add_trace(go.Bar(
                name="Attendance %",
                x=ru_clean["urban_rural"],
                y=ru_clean["attendance_pct"],
                marker_color="#3b7dd8",
                text=ru_clean["attendance_pct"].round(1).astype(str) + "%",
                textposition="outside",
                textfont=dict(size=11),
                width=0.3,
            ))
            fig4.add_trace(go.Bar(
                name="Score %",
                x=ru_clean["urban_rural"],
                y=ru_clean["score_pct"],
                marker_color="#f59e0b",
                text=ru_clean["score_pct"].round(1).astype(str) + "%",
                textposition="outside",
                textfont=dict(size=11),
                width=0.3,
            ))
            fig4.update_layout(barmode="group")
            fig4 = theme(fig4)
            fig4.update_layout(
                xaxis_title="Area Type",
                yaxis_title="Percentage (%)",
                legend_title="Metric",
                yaxis=dict(range=[0, 115]),
            )
            st.plotly_chart(fig4, use_container_width=True)

spacer()

# ─────────────────────────────────────────────────────────────
# ROW 3 — Instructor Dropdown (REPLACED BAR CHART)
# ─────────────────────────────────────────────────────────────
section("Instructor Activity", "fa-solid fa-person-chalkboard")

chart_header(
    "Instructor Profile Lookup",
    "Select an instructor to view their performance details",
    "fa-solid fa-user-tie", "cyan"
)

# Clean instructor data
inst_clean = inst_df.copy()
inst_clean = inst_clean[inst_clean["instructor_name"].str.strip().replace("", pd.NA).notna()]
inst_clean = inst_clean[inst_clean["instructor_name"].str.strip() != "--"]
inst_clean = inst_clean.sort_values("instructor_name")

if inst_clean.empty:
    st.info("No instructor data available.")
else:
    # Dropdown + profile card in a styled container
    st.markdown('<div class="instructor-card">', unsafe_allow_html=True)

    selected_instructor = st.selectbox(
        "Select Instructor",
        options=inst_clean["instructor_name"].tolist(),
        key="instructor_selector",
        label_visibility="collapsed",
        placeholder="Choose an instructor…",
    )

    if selected_instructor:
        row = inst_clean[inst_clean["instructor_name"] == selected_instructor].iloc[0]
        sessions   = int(row["sessions_conducted"])
        initials   = "".join([w[0].upper() for w in selected_instructor.split()[:2]])

        # Rank among all instructors
        inst_sorted = inst_clean.sort_values("sessions_conducted", ascending=False).reset_index(drop=True)
        rank = inst_sorted[inst_sorted["instructor_name"] == selected_instructor].index[0] + 1
        total_instr = len(inst_clean)
        max_sessions = int(inst_clean["sessions_conducted"].max())
        avg_sessions = round(inst_clean["sessions_conducted"].mean(), 1)

        pct_of_max = round((sessions / max_sessions * 100) if max_sessions > 0 else 0, 1)

        st.markdown(f"""
        <div class="instructor-profile">
            <div class="instructor-avatar">{initials}</div>
            <div style="flex:1">
                <div class="instructor-name">{selected_instructor}</div>
                <div class="instructor-meta">
                    <i class="fa-solid fa-ranking-star" style="color:#f59e0b;margin-right:4px;"></i>
                    Ranked #{rank} of {total_instr} instructors
                </div>
                <div class="instructor-stat-row">
                    <div class="instructor-stat">
                        <div class="instructor-stat-val">{sessions}</div>
                        <div class="instructor-stat-lbl">Sessions Conducted</div>
                    </div>
                    <div class="instructor-stat">
                        <div class="instructor-stat-val">#{rank}</div>
                        <div class="instructor-stat-lbl">Rank</div>
                    </div>
                    <div class="instructor-stat">
                        <div class="instructor-stat-val">{avg_sessions}</div>
                        <div class="instructor-stat-lbl">Team Average</div>
                    </div>
                    <div class="instructor-stat">
                        <div class="instructor-stat-val">{pct_of_max}%</div>
                        <div class="instructor-stat-lbl">vs Top Performer</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Mini comparison bar showing this instructor vs all others
        st.markdown("<div style='margin-top:16px;'>", unsafe_allow_html=True)
        compare_top10 = inst_sorted.head(10).copy()
        compare_top10["highlight"] = compare_top10["instructor_name"].apply(
            lambda n: "#3b7dd8" if n == selected_instructor else "#cbd5e1"
        )
        fig_cmp = go.Figure(go.Bar(
            x=compare_top10["instructor_name"],
            y=compare_top10["sessions_conducted"],
            marker_color=compare_top10["highlight"].tolist(),
            text=compare_top10["sessions_conducted"],
            textposition="outside",
            textfont=dict(size=10),
        ))
        fig_cmp = theme(fig_cmp, height=250)
        fig_cmp.update_layout(
            xaxis_title="",
            yaxis_title="Sessions",
            xaxis_tickangle=-30,
            yaxis=dict(range=[0, max_sessions * 1.2]),
            showlegend=False,
            margin=dict(l=40, r=20, t=10, b=70),
        )
        st.plotly_chart(fig_cmp, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

spacer()

# ─────────────────────────────────────────────────────────────
# ATTENTION REQUIRED
# ─────────────────────────────────────────────────────────────
section("Attention Required", "fa-solid fa-triangle-exclamation")

low_perf = school_agg[
    (school_agg["attendance_pct"] < 50) |
    (school_agg["score_pct"] < 50)
].copy()

count      = len(low_perf)
is_danger  = count > 5
danger_cls = "danger" if is_danger else ""
badge_cls  = "red" if is_danger else ""
icon_c     = "#ef4444" if is_danger else "#f59e0b"

st.markdown(f"""
<div class="alert-card {danger_cls}">
    <div class="alert-card-head">
        <i class="fa-solid fa-circle-exclamation" style="color:{icon_c};font-size:18px;"></i>
        <span class="alert-title">Low Performing Schools</span>
        <span class="alert-badge {badge_cls}">{count} flagged</span>
    </div>
    <div class="alert-body">
        Schools with <strong>Attendance &lt; 50%</strong> or <strong>Score &lt; 50%</strong>
        require immediate intervention. Expand below to review individual records.
    </div>
</div>
""", unsafe_allow_html=True)

with st.expander(f"🔍  View {count} Flagged School Record{'s' if count != 1 else ''}", expanded=False):
    if count == 0:
        st.success("✅  No schools are currently flagged — great performance across the board!")
    else:
        display_cols = ["school_name", "state", "urban_rural", "attendance_pct", "score_pct"]
        display_cols = [c for c in display_cols if c in low_perf.columns]
        st.dataframe(
            low_perf[display_cols].sort_values("score_pct").reset_index(drop=True),
            use_container_width=True,
        )

spacer()

# ─────────────────────────────────────────────────────────────
# FULL DATA TABLE
# ─────────────────────────────────────────────────────────────
section("Full School Performance Data", "fa-solid fa-table")

with st.expander(f"📋  View All Records  ({len(school_agg)} schools)", expanded=False):
    sort_col = st.selectbox("Sort by", ["school_name", "attendance_pct", "score_pct"], key="sort_col")
    asc = st.checkbox("Ascending", value=True, key="sort_asc")
    st.dataframe(
        school_agg.sort_values(sort_col, ascending=asc).reset_index(drop=True),
        use_container_width=True,
    )