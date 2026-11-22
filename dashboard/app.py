"""
Streamlit dashboard on top of the dbt marts ("Violet Ledger" design).

Run from the project root after `dbt build`:
    streamlit run dashboard/app.py

Uses the full dbt database (ecommerce.duckdb) when it exists. Otherwise, as on
Streamlit Community Cloud, it falls back to the small snapshot in
dashboard/data/dashboard.duckdb (made by scripts/export_dashboard_db.py).
The theme (colors, Sora + Inter fonts) lives in .streamlit/config.toml.
"""
import base64
from html import escape
from pathlib import Path

import duckdb
import plotly.graph_objects as go
import streamlit as st

FULL_DB = Path(__file__).resolve().parents[1] / "ecommerce.duckdb"
SNAPSHOT_DB = Path(__file__).resolve().parent / "data" / "dashboard.duckdb"
DB_PATH = FULL_DB if FULL_DB.exists() else SNAPSHOT_DB

REPO_URL = "https://github.com/dhia-sa/ecommerce-analytics-dbt"
DATASET_URL = "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"
WINDOW = "order_date between '2017-01-01' and '2018-08-31'"

# design tokens
ACCENT, ACCENT_DEEP, TEAL = "#6056FF", "#3B32F9", "#0E9384"
INK, INK_2, INK_DARK, MUTED = "#000000", "#0D162F", "#1A192B", "#868A97"
BORDER, PANEL, TINT, GRAY_BAR = "#E6E7EA", "#F3F3F4", "#F8FAFC", "#C9CBD3"

CATEGORY_NAMES = {
    "health_beauty": "Health & beauty", "watches_gifts": "Watches & gifts",
    "bed_bath_table": "Bed, bath & table", "sports_leisure": "Sports & leisure",
    "computers_accessories": "Computers & accessories", "furniture_decor": "Furniture & decor",
    "housewares": "Housewares", "cool_stuff": "Cool stuff", "auto": "Auto",
    "garden_tools": "Garden tools", "office_furniture": "Office furniture", "telephony": "Telephony",
}

st.set_page_config(page_title="Olist Analytics", page_icon="🟣", layout="wide")


# ---------- helpers ----------
@st.cache_data
def query(sql: str):
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        return con.sql(sql).df()


def nice(category: str) -> str:
    return CATEGORY_NAMES.get(category, category.replace("_", " ").capitalize())


def brl(value: float) -> str:
    if value >= 1e6:
        return f"R$ {value / 1e6:.2f}M"
    if value >= 1e3:
        return f"R$ {value / 1e3:.0f}k"
    return f"R$ {value:.0f}"


def pct(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def month_label(ts) -> str:
    return ts.strftime("%b %y")


def svg_img(svg: str, alt: str = "", cls: str = "") -> str:
    """st.html's sanitizer strips inline <svg>, so graphics are embedded as data-URI images."""
    data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f'<img class="{cls}" alt="{escape(alt)}" src="data:image/svg+xml;base64,{data}">'


def sparkline(values) -> str:
    """Sparkline with the indigo gradient stroke and a faint area fill."""
    w, h = 300, 44
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    pts = [(i / (len(values) - 1) * w, h - 4 - (v - lo) / span * (h - 14)) for i, v in enumerate(values)]
    line = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" preserveAspectRatio="none">
      <defs>
        <linearGradient id="f" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{ACCENT}" stop-opacity=".18"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/></linearGradient>
        <linearGradient id="s" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#A49EFF"/><stop offset="1" stop-color="{ACCENT_DEEP}"/></linearGradient>
      </defs>
      <path d="{line}L{w},{h}L0,{h}Z" fill="url(#f)"/>
      <path d="{line}" fill="none" stroke="url(#s)" stroke-width="1.6" vector-effect="non-scaling-stroke"/>
    </svg>"""
    return svg_img(svg, cls="spark")


def style_fig(fig: go.Figure, height: int) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=4, r=8, t=8, b=4),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", size=12, color=MUTED),
        hoverlabel=dict(bgcolor=INK_DARK, bordercolor=INK_DARK, font=dict(family="Inter, sans-serif", color="#fff")),
        showlegend=False, dragmode=False, bargap=0.35,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=BORDER, ticks="", fixedrange=True, automargin=True)
    fig.update_yaxes(gridcolor=BORDER, zeroline=False, ticks="", fixedrange=True, automargin=True)
    return fig


def chart(fig: go.Figure) -> None:
    st.plotly_chart(fig, theme=None, config={"displayModeBar": False, "responsive": True})


def card_head(title: str, subtitle: str) -> None:
    st.html(f'<div class="vl-card-head"><h4>{escape(title)}</h4><p>{escape(subtitle)}</p></div>')


def callout(items) -> None:
    cells = "".join(f"<div><b>{big}</b>{escape(label)}</div>" for big, label in items)
    st.html(f'<div class="vl-callout">{cells}</div>')


# ---------- styles ----------
st.html(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Sora:wght@400;500&display=swap');
:root {{
  --grad: radial-gradient(circle, rgb(96,86,255), rgb(59,50,249));
  --card-shadow: rgba(13,22,47,.06) 0 1px 2px 0, rgba(13,22,47,.14) 0 6px 18px -4px, rgba(255,255,255,.9) 0 1px 0 0 inset;
  --soft-shadow: rgba(255,255,255,.8) 0 1px 0 0 inset, rgba(13,22,47,.07) 0 2px 8px 0;
  --ease: cubic-bezier(.4,0,.2,1);
}}
/* top padding keeps the nav clear of Streamlit's own toolbar (top-right, also on Community Cloud) */
.block-container {{ max-width: 1300px; padding: 3rem 40px 2rem; }}
[data-testid="stHeader"] {{ background: transparent; }}
.vl, .vl * {{ box-sizing: border-box; }}
.vl {{ font-family: Inter, system-ui, sans-serif; color: {INK}; }}
.vl a {{ text-decoration: none; color: inherit; }}

/* nav */
.vl-nav {{ height: 65px; display: flex; align-items: center; gap: 32px; }}
.vl-brand {{ display: flex; align-items: center; gap: 10px; font: 500 17px/1 Sora, Inter, sans-serif; letter-spacing: -.4px; color: {INK_DARK}; }}
.vl-brand i {{ width: 22px; height: 22px; border-radius: 50%; background: var(--grad); display: block; }}
.vl-links {{ display: flex; gap: 24px; font-size: 14px; color: {INK_2}; }}
.vl-links a {{ opacity: .8; transition: opacity .15s var(--ease); }}
.vl-links a:hover {{ opacity: 1; }}
.vl-actions {{ margin-left: auto; display: flex; gap: 10px; }}
.vl-btn {{ display: inline-flex; align-items: center; justify-content: center; height: 42px; padding: 10px 20px; font: 500 14px/1 Inter, sans-serif; border-radius: 9999px; transition: box-shadow .15s var(--ease), background .15s var(--ease); white-space: nowrap; }}
.vl-btn-primary {{ background: var(--grad); color: #fff !important; box-shadow: rgba(59,50,249,.25) 0 1.6px 6.4px 0; }}
.vl-btn-primary:hover {{ box-shadow: rgba(59,50,249,.35) 0 3.2px 9.6px 0; }}
.vl-btn-nav {{ border-radius: 4.8px; }}
.vl-btn-outline {{ color: {INK_2}; border: 1px solid {BORDER}; border-radius: 4.8px; }}
.vl-btn-outline:hover, .vl-btn-ghost:hover {{ background: #F9FAFB; }}
.vl-btn-ghost {{ color: #374151; height: 38px; padding: 8px 16px; border-radius: 6px; }}

/* hero */
.vl-hero {{ padding: 48px 0 8px; }}
/* Corner washes behind the hero. Painted on the scrolling container (st.html blocks clip their
   own overflow), sized to the hero band and scrolled with the content (attachment: local). */
[data-testid="stMain"] {{ background-color: #fff; background-repeat: no-repeat; background-size: 100% 860px; background-attachment: local; background-image:
  radial-gradient(40% 60% at 0% 0%, rgba(138,105,255,.22) 0%, rgba(138,105,255,0) 62%),
  radial-gradient(38% 55% at 100% 0%, rgba(109,74,255,.20) 0%, rgba(109,74,255,0) 62%),
  radial-gradient(30% 22% at 96% 78%, rgba(138,105,255,.14) 0%, rgba(138,105,255,0) 60%),
  radial-gradient(30% 22% at 4% 78%, rgba(199,207,255,.35) 0%, rgba(199,207,255,0) 65%); }}
.vl-hero-top {{ display: grid; grid-template-columns: 1.15fr 1fr; gap: 80px; align-items: end; }}
.vl-eyebrow {{ font: 500 13px/1.4 Inter, sans-serif; color: {MUTED}; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }}
.vl-eyebrow span {{ width: 6px; height: 6px; border-radius: 50%; background: {TEAL}; }}
.vl h1 {{ font: 400 48px/1.2 Sora, Inter, sans-serif; letter-spacing: -2.4px; margin: 0; padding: 0; color: {INK_DARK}; }}
.vl h2 {{ font: 400 36px/1.35 Sora, Inter, sans-serif; letter-spacing: -.9px; margin: 0; padding: 0; color: {INK_DARK}; }}
.vl-lede {{ color: {INK_2}; opacity: .78; margin: 0 0 24px; max-width: 520px; font-size: 16px; line-height: 1.6; }}
.vl-ctas {{ display: flex; gap: 10px; flex-wrap: wrap; }}
.vl-metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; margin-top: 56px; }}
.vl-metric {{ background: rgba(255,255,255,.75); border: 1px solid {BORDER}; border-radius: 12px; padding: 20px 20px 0; box-shadow: var(--soft-shadow); overflow: hidden; }}
.vl-metric .l {{ font: 500 13px/1.4 Inter, sans-serif; color: {MUTED}; }}
.vl-metric .v {{ font: 400 36px/1.15 Sora, Inter, sans-serif; letter-spacing: -1.4px; color: {INK}; margin: 6px 0 4px; font-variant-numeric: tabular-nums; }}
.vl-metric .d {{ font: 500 13px/1.4 Inter, sans-serif; color: {MUTED}; }}
.vl-metric .d.good {{ color: {TEAL}; }} .vl-metric .d.bad {{ color: {INK_2}; }}
.vl-metric .spark {{ display: block; margin: 14px -20px 0; width: calc(100% + 40px); max-width: none; height: 44px; }}
.vl-icard .ico img {{ width: 18px; height: 18px; display: block; }}

/* insights */
.vl-insights {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 40px 0 24px; }}
.vl-icard {{ background: {PANEL}; border-radius: 12px; padding: 24px; }}
.vl-icard .ico {{ width: 36px; height: 36px; border-radius: 8px; background: #fff; display: grid; place-items: center; box-shadow: var(--soft-shadow); margin-bottom: 18px; }}
.vl-icard .big {{ font: 400 32px/1.1 Sora, Inter, sans-serif; letter-spacing: -1.2px; color: {INK_DARK}; }}
.vl-icard h3 {{ font: 500 20px/1.4 Inter, sans-serif; letter-spacing: -.5px; margin: 10px 0 6px; padding: 0; color: {INK}; }}
.vl-icard p {{ margin: 0; color: {MUTED}; font-size: 15px; line-height: 1.6; }}

/* section heads */
.vl-section {{ padding-top: 48px; }}
.vl-section p {{ margin: 6px 0 0; color: {MUTED}; font-size: 16px; }}

/* pill tab switcher (st.segmented_control) */
.st-key-view [data-testid="stButtonGroup"] {{ padding: 4px; border: 1px solid {BORDER}; border-radius: 9999px; background: #fff; box-shadow: var(--soft-shadow); width: max-content; max-width: 100%; }}
.st-key-view button {{ border: 0 !important; border-radius: 9999px !important; background: transparent !important; color: {INK_2} !important; font: 500 14px/1 Inter, sans-serif !important; padding: 10px 16px !important; min-height: 0 !important; box-shadow: none !important; transition: background .15s var(--ease); }}
.st-key-view button:hover {{ background: #F9FAFB !important; }}
.st-key-view button[aria-checked="true"], .st-key-view button[kind$="Active"] {{ background: {PANEL} !important; color: {INK} !important; }}
.st-key-view button p {{ font: inherit !important; }}
.st-key-view {{ display: flex; justify-content: flex-end; }}

/* cards (bordered containers with a key starting "card_") */
[class*="st-key-card_"] {{ background: #fff; border: 1px solid {BORDER} !important; border-radius: 12px !important; box-shadow: var(--card-shadow); padding: 24px !important; }}
.vl-card-head h4 {{ font: 500 16px/1.4 Inter, sans-serif; letter-spacing: -.3px; margin: 0; padding: 0; color: {INK}; }}
.vl-card-head p {{ font-size: 13px; color: {MUTED}; margin: 2px 0 4px; }}
.vl-callout {{ display: flex; flex-wrap: wrap; gap: 12px 28px; padding-top: 16px; border-top: 1px solid {BORDER}; font-family: Inter, sans-serif; }}
.vl-callout div {{ font-size: 13px; color: {MUTED}; }}
.vl-callout b {{ display: block; font: 400 26px/1.2 Sora, Inter, sans-serif; letter-spacing: -.8px; color: {INK_DARK}; }}

/* how it's built */
.vl-process {{ display: grid; grid-template-columns: 1.4fr 1fr 1fr; gap: 20px; margin-top: 28px; }}
.vl-stage {{ border: 1px solid {BORDER}; border-radius: 16px; padding: 24px; background: #fff; }}
.vl-stage.first {{ border-color: transparent; background: linear-gradient(160deg, rgb(230,230,251) 0%, rgb(226,227,250) 50%, rgb(223,226,250) 100%); }}
.vl-checks {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 28px; }}
.vl-checks span {{ display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px 5px 8px; border-radius: 9999px; background: rgba(255,255,255,.85); border: 1px solid {BORDER}; font: 500 12px/1.3 Inter, sans-serif; color: {INK_2}; }}
.vl-checks span::before {{ content: ""; width: 14px; height: 14px; border-radius: 50%; background: {TEAL} url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 14 14'%3E%3Cpath d='M4 7.2l2 2 4-4.4' fill='none' stroke='white' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") center/contain no-repeat; }}
.vl-stage .wk {{ font: 500 12px/1 Inter, sans-serif; color: {MUTED}; letter-spacing: .3px; text-transform: uppercase; }}
.vl-stage h3 {{ font: 500 20px/1.4 Inter, sans-serif; letter-spacing: -.5px; margin: 8px 0 6px; padding: 0; color: {INK}; }}
.vl-stage p {{ margin: 0; color: {MUTED}; font-size: 15px; line-height: 1.6; }}
.vl-flow {{ margin-top: 20px; border-radius: 16px; padding: 28px; background: linear-gradient(160deg, rgb(230,230,251) 0%, rgb(226,227,250) 50%, rgb(223,226,250) 100%); overflow-x: auto; }}
.vl-flow img {{ width: 100%; height: auto; display: block; min-width: 860px; max-width: none; }}

/* footer */
.vl-footer {{ border-top: 1px solid {BORDER}; margin-top: 56px; padding: 40px 0 24px; color: {MUTED}; font-size: 14px; display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 32px; line-height: 1.6; }}
.vl-footer h5 {{ font: 500 13px/1 Inter, sans-serif; color: {INK_2}; margin: 4px 0 14px; padding: 0; }}
.vl-footer a {{ display: block; margin-bottom: 8px; transition: color .15s var(--ease); }}
.vl-footer a:hover {{ color: {INK_2}; }}

@media (max-width: 1000px) {{
  .vl-hero-top {{ grid-template-columns: 1fr; gap: 24px; }}
  .vl-metrics {{ grid-template-columns: repeat(2, 1fr); }}
  .vl-insights, .vl-process {{ grid-template-columns: 1fr; }}
  .vl-links {{ display: none; }}
  .vl-footer {{ grid-template-columns: 1fr 1fr; }}
  .st-key-view {{ justify-content: flex-start; }}
}}
@media (max-width: 640px) {{
  .block-container {{ padding: 3rem 16px 2rem; }}
  .vl h1 {{ font-size: 34px; letter-spacing: -1.4px; }}
  .vl h2 {{ font-size: 28px; letter-spacing: -.6px; }}
  .vl-metrics {{ gap: 12px; }}
  .vl-metric {{ padding: 16px 16px 0; }}
  .vl-metric .v {{ font-size: 26px; letter-spacing: -.8px; }}
  .vl-metric .spark {{ margin: 10px -16px 0; width: calc(100% + 32px); }}
  .vl-btn-outline {{ display: none; }}
  .st-key-view [data-testid="stButtonGroup"] {{ border-radius: 22px; width: 100%; }}
  .st-key-view [data-testid="stButtonGroup"] > div {{ flex-wrap: wrap; overflow: visible; }}
  .st-key-view button {{ white-space: nowrap; padding: 10px 12px !important; }}
  [class*="st-key-card_"] {{ padding: 18px !important; }}
  .vl-flow {{ padding: 16px; }}
}}
</style>""")


# ---------- data ----------
kpi = query(f"""
    select
        count(*) filter (where is_valid_order)                              as orders,
        sum(items_value) filter (where is_valid_order)                      as gmv,
        avg(items_value) filter (where is_valid_order and item_count > 0)   as aov,
        avg(case when is_late_delivery then 1.0 else 0.0 end)
            filter (where is_late_delivery is not null)                     as late_rate
    from core.fct_orders where {WINDOW}
""").iloc[0]

monthly = query(f"""
    select date_trunc('month', order_date)                                  as month,
           count(*) filter (where is_valid_order)                           as orders,
           sum(items_value) filter (where is_valid_order)                   as gmv,
           avg(items_value) filter (where is_valid_order and item_count > 0) as aov,
           avg(case when is_late_delivery then 1.0 else 0.0 end)
               filter (where is_late_delivery is not null)                  as late_rate
    from core.fct_orders where {WINDOW}
    group by 1 order by 1
""")

# Jan–Aug 2018 vs Jan–Aug 2017, for the metric deltas
yoy = query("""
    select year(order_date)                                                 as year,
           count(*) filter (where is_valid_order)                           as orders,
           sum(items_value) filter (where is_valid_order)                   as gmv,
           avg(items_value) filter (where is_valid_order and item_count > 0) as aov,
           avg(case when is_late_delivery then 1.0 else 0.0 end)
               filter (where is_late_delivery is not null)                  as late_rate
    from core.fct_orders
    where month(order_date) <= 8 and year(order_date) in (2017, 2018)
    group by 1 order by 1
""").set_index("year")
y17, y18 = yoy.loc[2017], yoy.loc[2018]

review_avg = query("""
    select case when is_late_delivery then 'late' else 'on_time' end as delivery, avg(review_score) as score
    from core.fct_orders where is_late_delivery is not null and review_score is not null group by 1
""").set_index("delivery")["score"]

categories = query("""
    select product_category, sum(gmv) as gmv
    from analytics.mart_monthly_sales group by 1 order by 2 desc
""")
top_cat = categories.head(10)
top10_share = top_cat.gmv.sum() / categories.gmv.sum()

repeat_rate = query("select avg((frequency > 1)::int) as r from analytics.mart_customer_rfm").r.iloc[0]
month1_retention = query(
    "select avg(retention_rate) as r from analytics.mart_cohort_retention where months_since_first = 1"
).r.iloc[0]


# ---------- nav + hero ----------
metrics = [
    ("GMV", brl(kpi.gmv), monthly.gmv, f"▲ {pct(y18.gmv / y17.gmv - 1, 0)} vs Jan–Aug 2017", "good"),
    ("Orders", f"{kpi.orders:,.0f}", monthly.orders, f"▲ {pct(y18.orders / y17.orders - 1, 0)} vs Jan–Aug 2017", "good"),
    ("Average order value", f"R$ {kpi.aov:,.0f}", monthly.aov, f"Flat · R$ {y17.aov:.0f} → R$ {y18.aov:.0f}", ""),
    ("Late delivery rate", pct(kpi.late_rate), monthly.late_rate,
     f"▲ {(y18.late_rate - y17.late_rate) * 100:.1f} pts vs Jan–Aug 2017", "bad"),
]
metric_cards = "".join(
    f'<div class="vl-metric"><div class="l">{label}</div><div class="v">{value}</div>'
    f'<div class="d {cls}">{delta}</div>{sparkline(list(series))}</div>'
    for label, value, series, delta, cls in metrics
)


def icon(path: str) -> str:
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" '
           f'stroke="{INK_2}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{path}</svg>')
    return f'<div class="ico">{svg_img(svg)}</div>'


insights = [
    (icon('<path d="M3 7h11v8H3zM14 10h4l3 3v2h-7"/><circle cx="7" cy="17" r="1.6"/><circle cx="17" cy="17" r="1.6"/>'),
     f"{review_avg.late:.1f}★ vs {review_avg.on_time:.1f}★", "Late delivery costs two stars",
     f"Late orders average {review_avg.late:.1f} stars against {review_avg.on_time:.1f} for on-time ones. "
     f"{pct(kpi.late_rate)} of delivered orders arrive late."),
    (icon('<path d="M17 2l4 4-4 4"/><path d="M3 11V9a3 3 0 013-3h15M7 22l-4-4 4-4"/><path d="M21 13v2a3 3 0 01-3 3H3"/>'),
     pct(repeat_rate), "Almost no repeat buyers",
     f"Only {pct(repeat_rate, 0)} of customers ever order twice, and month-1 cohort retention is "
     f"{pct(month1_retention, 2)}. Growth is all acquisition."),
    (icon('<path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 6-6"/>'),
     brl(top_cat.gmv.iloc[0]), f"{nice(top_cat.product_category.iloc[0])} leads GMV",
     f"Followed by {nice(top_cat.product_category.iloc[1]).lower()} and "
     f"{nice(top_cat.product_category.iloc[2]).lower()}. The top 10 categories make up {pct(top10_share, 0)} of GMV."),
]
insight_cards = "".join(
    f'<div class="vl-icard">{ico}<div class="big">{big}</div><h3>{escape(h)}</h3><p>{escape(p)}</p></div>'
    for ico, big, h, p in insights
)

st.html(f"""
<div class="vl">
  <nav class="vl-nav">
    <a class="vl-brand" href="#overview"><i></i>Olist Analytics</a>
    <div class="vl-links"><a href="#analysis">Analysis</a><a href="#built">How it's built</a><a href="{REPO_URL}#readme" target="_blank">README</a></div>
    <div class="vl-actions">
      <a class="vl-btn vl-btn-outline" href="{DATASET_URL}" target="_blank">Dataset</a>
      <a class="vl-btn vl-btn-primary vl-btn-nav" href="{REPO_URL}" target="_blank">View on GitHub</a>
    </div>
  </nav>
  <header class="vl-hero" id="overview">
    <div class="vl-hero-top">
      <div>
        <div class="vl-eyebrow"><span></span>Brazilian marketplace · Jan 2017 – Aug 2018</div>
        <h1>{kpi.orders / 1000:.0f}k marketplace orders, modeled end to end.</h1>
      </div>
      <div>
        <p class="vl-lede">Raw Olist CSVs turned into a tested dbt star schema on DuckDB. Every number on this page comes from those marts, the same models that pass 66 data tests in CI.</p>
        <div class="vl-ctas">
          <a class="vl-btn vl-btn-primary" href="#analysis">Explore the analysis</a>
          <a class="vl-btn vl-btn-ghost" href="#built">How it's built →</a>
        </div>
      </div>
    </div>
    <div class="vl-metrics">{metric_cards}</div>
  </header>
  <div class="vl-insights">{insight_cards}</div>
</div>
""")


# ---------- analysis ----------
head_l, head_r = st.columns([1.4, 1], vertical_alignment="bottom")
with head_l:
    st.html('<div class="vl vl-section" id="analysis"><h2>Analysis</h2>'
            '<p>Four views on the analytics marts. Switch between them here.</p></div>')
with head_r:
    view = st.segmented_control(
        "View", ["Sales", "Delivery & reviews", "Customers", "Sellers"],
        default="Sales", required=True, key="view", label_visibility="collapsed",
    )

if view == "Sales":
    left, right = st.columns([1.6, 1])
    with left, st.container(border=True, key="card_gmv"):
        card_head("Monthly GMV", "Product value, excluding freight · BRL")
        fig = go.Figure(go.Scatter(
            x=monthly.month, y=monthly.gmv, mode="lines+markers",
            line=dict(color=ACCENT, width=2.2), fill="tozeroy",
            fillgradient=dict(type="vertical", colorscale=[[0, "rgba(96,86,255,0)"], [1, "rgba(96,86,255,0.22)"]]),
            marker=dict(size=7, color="#fff", line=dict(color=ACCENT, width=1.6)),
            hovertemplate="%{x|%b %Y}<br><b>R$ %{y:,.0f}</b><extra></extra>",
        ))
        style_fig(fig, 400).update_yaxes(tickprefix="R$ ", tickformat="~s")
        fig.update_xaxes(dtick="M3", tickformat="%b %y")
        chart(fig)
    with right, st.container(border=True, key="card_categories"):
        card_head("Top categories", "GMV, Jan 2017 – Aug 2018")
        cats = top_cat.iloc[::-1]
        fig = go.Figure(go.Bar(
            x=cats.gmv, y=[nice(c) for c in cats.product_category], orientation="h",
            marker=dict(color=[GRAY_BAR] * (len(cats) - 1) + [ACCENT], cornerradius=4),
            text=[brl(v) for v in cats.gmv], textposition="outside", cliponaxis=False,
            textfont=dict(color=MUTED, size=12),
            hovertemplate="%{y}<br><b>R$ %{x:,.0f}</b><extra></extra>",
        ))
        style_fig(fig, 400).update_xaxes(visible=False, range=[0, cats.gmv.max() * 1.28])
        fig.update_yaxes(showgrid=False, tickfont=dict(color=INK_2), ticklabelstandoff=8)
        chart(fig)

elif view == "Delivery & reviews":
    left, right = st.columns([1.6, 1])
    with left, st.container(border=True, key="card_states"):
        card_head("Late delivery rate by state", "Share of delivered orders that arrived after the estimated date")
        states = query("""
            select customer_state, sum(late_orders) / sum(delivered_orders) as late_rate,
                   sum(delivered_orders) as delivered
            from analytics.mart_delivery_performance group by 1 order by 2 desc
        """)
        fig = go.Figure(go.Bar(
            x=states.customer_state, y=states.late_rate,
            marker=dict(color=[ACCENT if r >= 0.12 else GRAY_BAR for r in states.late_rate], cornerradius=3),
            customdata=states.delivered,
            hovertemplate="%{x}<br><b>%{y:.1%}</b> late<br>%{customdata:,} delivered orders<extra></extra>",
        ))
        style_fig(fig, 380).update_yaxes(tickformat=".0%")
        fig.update_xaxes(tickfont=dict(size=11))
        chart(fig)
    with right, st.container(border=True, key="card_reviews"):
        card_head("Review score: late vs on time", "Share of orders at each star rating")
        reviews = query("""
            select case when is_late_delivery then 'Late' else 'On time' end as delivery,
                   review_score, count(*) as orders
            from core.fct_orders
            where is_late_delivery is not null and review_score is not null
            group by 1, 2 order by 1, 2
        """)
        reviews["share"] = reviews.orders / reviews.groupby("delivery").orders.transform("sum")
        fig = go.Figure()
        for name, color in [("On time", INK_DARK), ("Late", ACCENT)]:
            d = reviews[reviews.delivery == name]
            fig.add_bar(x=[f"{s}★" for s in d.review_score], y=d.share, name=name,
                        marker=dict(color=color, cornerradius=3),
                        hovertemplate=f"{name} · %{{x}}<br><b>%{{y:.1%}}</b><extra></extra>")
        style_fig(fig, 280).update_layout(
            showlegend=True, barmode="group", bargroupgap=0.1,
            legend=dict(orientation="h", x=0, y=1.12, font=dict(color=MUTED, size=12)),
        )
        fig.update_yaxes(tickformat=".0%")
        chart(fig)
        late_one_star = reviews.query("delivery == 'Late' and review_score == 1").share.iloc[0]
        callout([(f"{review_avg.on_time:.2f}★", "on time"), (f"{review_avg.late:.2f}★", "late"),
                 (pct(late_one_star, 0), "of late orders get 1★")])

elif view == "Customers":
    left, right = st.columns(2)
    with left, st.container(border=True, key="card_rfm"):
        card_head("Customers by RFM segment", "Recency, frequency and monetary scores")
        rfm = query("""
            select rfm_segment, count(*) as customers, sum(monetary) as revenue
            from analytics.mart_customer_rfm group by 1 order by 2
        """)
        fig = go.Figure(go.Bar(
            x=rfm.customers, y=rfm.rfm_segment, orientation="h",
            marker=dict(color=GRAY_BAR, cornerradius=4), customdata=rfm.revenue,
            text=[f"{c:,}" for c in rfm.customers], textposition="outside", cliponaxis=False,
            textfont=dict(color=MUTED, size=12),
            hovertemplate="%{y}<br><b>%{x:,} customers</b><br>R$ %{customdata:,.0f} revenue<extra></extra>",
        ))
        style_fig(fig, 400).update_xaxes(visible=False, range=[0, rfm.customers.max() * 1.22])
        fig.update_yaxes(showgrid=False, tickfont=dict(color=INK_2), ticklabelstandoff=8)
        chart(fig)
        seg = rfm.set_index("rfm_segment")
        loyal = seg.loc[["Loyal", "Champions"]].customers.sum() / seg.customers.sum()
        big = seg.loc[["Big Spenders - Recent", "At Risk - High Value"]].revenue.sum() / seg.revenue.sum()
        callout([(f"{seg.customers.sum():,}", "customers scored"), (pct(loyal), "Loyal or Champions"),
                 (pct(big, 0), "of revenue from big spenders and at-risk high value")])
    with right, st.container(border=True, key="card_cohort"):
        card_head("Cohort retention", "Share of each monthly cohort ordering again, months 1–6")
        cohort = query("""
            select cohort_month, months_since_first, retention_rate
            from analytics.mart_cohort_retention where months_since_first between 1 and 6
        """)
        heat = cohort.pivot(index="cohort_month", columns="months_since_first", values="retention_rate").sort_index()
        fig = go.Figure(go.Heatmap(
            z=heat.values, x=[f"M{m}" for m in heat.columns], y=[month_label(m) for m in heat.index],
            colorscale=[[0, "#F1F0FF"], [1, ACCENT]], zmin=0, zmax=0.008, showscale=False,
            text=[[pct(v) if v == v else "" for v in row] for row in heat.values],
            texttemplate="%{text}", textfont=dict(size=11, color=INK_2), xgap=3, ygap=3,
            hovertemplate="%{y} cohort · %{x}<br><b>%{z:.2%}</b> ordered again<extra></extra>",
        ))
        style_fig(fig, 520).update_yaxes(autorange="reversed", showgrid=False, tickfont=dict(color=INK_2))
        fig.update_xaxes(side="top", linecolor="rgba(0,0,0,0)")
        chart(fig)

else:  # Sellers
    with st.container(border=True, key="card_sellers"):
        card_head("All sellers by GMV", "3,029 sellers · click a column header to sort, or use the search icon")
        sellers = query("""
            select seller_id, seller_state, top_category, orders, round(gmv) as gmv, avg_delivery_days,
                   late_rate, avg_review_score, seller_tier
            from analytics.mart_seller_performance order by gmv desc
        """)
        sellers["top_category"] = sellers.top_category.map(nice)
        st.dataframe(
            sellers, hide_index=True, height=520,
            column_config={
                "seller_id": st.column_config.TextColumn("Seller", width="small"),
                "seller_state": st.column_config.TextColumn("State", width="small"),
                "top_category": st.column_config.TextColumn("Top category"),
                "orders": st.column_config.NumberColumn("Orders", format="localized"),
                "gmv": st.column_config.NumberColumn("GMV (BRL)", format="localized"),
                "avg_delivery_days": st.column_config.NumberColumn("Avg delivery", format="%.1f d"),
                "late_rate": st.column_config.NumberColumn("Late rate", format="percent"),
                "avg_review_score": st.column_config.NumberColumn("Review", format="%.2f ★"),
                "seller_tier": st.column_config.TextColumn("Tier"),
            },
        )


# ---------- how it's built ----------
def flow_svg() -> str:
    cols = [
        (20, 190, "SOURCE", ["8 Olist CSVs"]),
        (250, 200, "STAGING", ["stg_olist__orders", "stg_olist__order_items", "stg_olist__customers", "+ 5 more"]),
        (500, 210, "INTERMEDIATE", ["int_order_items_enriched", "int_order_payments_pivoted", "int_order_reviews_dedup"]),
        (750, 200, "MARTS", ["fct_orders · fct_order_items", "4 dimensions", "5 analytics marts"]),
        (990, 170, "SERVING", ["Streamlit dashboard"]),
    ]
    pos = []
    for x, w, _, nodes in cols:
        top = 125 - (len(nodes) * 48 - 12) / 2 + 10
        pos.append([(x, top + i * 48, w, n) for i, n in enumerate(nodes)])
    edges = []
    for ci in range(len(pos) - 1):
        a_col, b_col = pos[ci], pos[ci + 1]
        for ai, a in enumerate(a_col):
            for bi, b in enumerate(b_col):
                if len(a_col) > 1 and len(b_col) > 1 and abs(ai - bi) > 1:
                    continue
                x1, y1, x2, y2 = a[0] + a[2], a[1] + 18, b[0], b[1] + 18
                mx = (x1 + x2) / 2
                edges.append(f'<path class="edge" d="M{x1},{y1}C{mx},{y1} {mx},{y2} {x2},{y2}"/>')
    labels = "".join(f'<text class="col" x="{x}" y="18">{k}</text>' for x, _, k, _ in cols)
    nodes = []
    for ci, col in enumerate(pos):
        for x, y, w, n in col:
            dot = f'<circle cx="{x + 18}" cy="{y + 18}" r="6" fill="url(#vlg)"/>' if ci == len(pos) - 1 else ""
            tx = x + (32 if dot else 14)
            nodes.append(f'<g class="node"><rect x="{x}" y="{y}" width="{w}" height="36" rx="8"/>{dot}'
                         f'<text x="{tx}" y="{y + 22}">{escape(n)}</text></g>')
    # Rendered as an <img>, so the page's web fonts don't apply: fall back to the closest system sans
    font = "Inter, 'Segoe UI', system-ui, -apple-system, Helvetica, Arial, sans-serif"
    style = (f"<style>.node rect{{fill:#fff;stroke:{BORDER}}}"
             f".node text{{font:500 12px {font};fill:{INK_2}}}"
             f".col{{font:500 10px {font};fill:{MUTED};letter-spacing:.6px}}"
             f".edge{{fill:none;stroke:{ACCENT};stroke-width:1.4;stroke-dasharray:4 4;opacity:.75;animation:dash 1.2s linear infinite}}"
             f"@keyframes dash{{to{{stroke-dashoffset:-16}}}}</style>")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1180 250">{style}'
           f'<defs><radialGradient id="vlg"><stop offset="0" stop-color="{ACCENT}"/><stop offset="1" stop-color="{ACCENT_DEEP}"/></radialGradient></defs>'
           f'{labels}{"".join(edges)}{"".join(nodes)}</svg>')
    return svg_img(svg, alt="Data flow: 8 Olist CSVs → 8 staging views → 3 intermediate views → "
                            "fact, dimension and analytics marts → Streamlit dashboard")


st.html(f"""
<div class="vl">
  <div class="vl-section" id="built">
    <h2>How it's built</h2>
    <p>Three dbt layers, each with its own job, from raw CSV to the numbers above.</p>
  </div>
  <div class="vl-process">
    <div class="vl-stage first">
      <div class="vl-checks"><span>Typed casts</span><span>Zip codes kept</span><span>1:1 with source</span></div>
      <div class="wk">Layer 01</div><h3>Staging · 8 views</h3>
      <p>Every raw column is read as text and cast explicitly, so nothing is lost on load.</p>
    </div>
    <div class="vl-stage">
      <div class="vl-checks"><span>Deduped reviews</span><span>Pivoted payments</span></div>
      <div class="wk">Layer 02</div><h3>Intermediate · 3 views</h3>
      <p>One review and one payment row per order, plus items enriched with category and seller.</p>
    </div>
    <div class="vl-stage">
      <div class="vl-checks"><span>66 tests</span><span>Star schema</span></div>
      <div class="wk">Layer 03</div><h3>Marts · 11 tables</h3>
      <p>Facts and dimensions, plus RFM, cohort, delivery, seller and sales marts.</p>
    </div>
  </div>
  <div class="vl-flow">{flow_svg()}</div>
  <footer class="vl-footer">
    <div><div class="vl-brand" style="margin-bottom:12px"><i></i>Olist Analytics</div>
      An analytics engineering portfolio project by dhia-sa.<br>dbt · DuckDB · Streamlit</div>
    <div><h5>Project</h5><a href="{REPO_URL}" target="_blank">GitHub repo</a><a href="{REPO_URL}#readme" target="_blank">README</a><a href="{REPO_URL}/actions" target="_blank">CI runs</a></div>
    <div><h5>Data</h5><a href="{DATASET_URL}" target="_blank">Olist on Kaggle</a><a href="#overview">Analysis window</a></div>
    <div><h5>Stack</h5><a href="https://www.getdbt.com/" target="_blank">dbt</a><a href="https://duckdb.org/" target="_blank">DuckDB</a><a href="https://streamlit.io/" target="_blank">Streamlit</a></div>
  </footer>
</div>
""")
