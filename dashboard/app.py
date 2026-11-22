"""
Streamlit dashboard on top of the dbt marts.

Run from the project root after `dbt build`:
    streamlit run dashboard/app.py
"""
from pathlib import Path

import duckdb
import plotly.express as px
import streamlit as st

DB_PATH = Path(__file__).resolve().parents[1] / "ecommerce.duckdb"

st.set_page_config(page_title="Olist E-commerce Analytics", layout="wide")


@st.cache_data
def query(sql: str):
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        return con.sql(sql).df()


st.title("Olist E-commerce Analytics")
st.caption("Brazilian marketplace, Jan 2017 – Aug 2018 · modeled with dbt + DuckDB")

# ---------- KPIs ----------
kpi = query("""
    select
        count(*) filter (where is_valid_order)                          as orders,
        sum(items_value) filter (where is_valid_order)                  as gmv,
        avg(items_value) filter (where is_valid_order and item_count > 0) as aov,
        avg(case when is_late_delivery then 1.0 else 0.0 end)
            filter (where is_late_delivery is not null)                 as late_rate,
        avg(review_score)                                               as avg_review
    from core.fct_orders
    where order_date between '2017-01-01' and '2018-08-31'
""").iloc[0]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Orders", f"{kpi.orders:,.0f}")
c2.metric("GMV (BRL)", f"{kpi.gmv / 1e6:,.2f} M")
c3.metric("Avg order value", f"R$ {kpi.aov:,.0f}")
c4.metric("Late delivery rate", f"{kpi.late_rate:.1%}")
c5.metric("Avg review score", f"{kpi.avg_review:.2f} ★")

tab_sales, tab_delivery, tab_customers, tab_sellers = st.tabs(
    ["Sales", "Delivery & reviews", "Customers", "Sellers"]
)

# ---------- Sales ----------
with tab_sales:
    monthly = query("""
        select order_month, sum(gmv) as gmv
        from analytics.mart_monthly_sales group by 1 order by 1
    """)
    st.plotly_chart(px.line(monthly, x="order_month", y="gmv", title="Monthly GMV"),
                    width="stretch")

    top_cat = query("""
        select product_category, sum(gmv) as gmv
        from analytics.mart_monthly_sales group by 1 order by 2 desc limit 15
    """)
    st.plotly_chart(px.bar(top_cat, x="gmv", y="product_category", orientation="h",
                           title="Top 15 categories by GMV").update_yaxes(autorange="reversed"),
                    width="stretch")

# ---------- Delivery ----------
with tab_delivery:
    by_state = query("""
        select customer_state,
               sum(late_orders) / sum(delivered_orders) as late_rate,
               sum(delivered_orders) as delivered_orders
        from analytics.mart_delivery_performance
        group by 1 order by 2 desc
    """)
    st.plotly_chart(px.bar(by_state, x="customer_state", y="late_rate",
                           title="Late delivery rate by customer state"),
                    width="stretch")

    review = query("""
        select case when is_late_delivery then 'Late' else 'On time' end as delivery,
               review_score, count(*) as orders
        from core.fct_orders
        where is_late_delivery is not null and review_score is not null
        group by 1, 2
    """)
    st.plotly_chart(px.bar(review, x="review_score", y="orders", color="delivery",
                           barmode="group", title="Review score: late vs on-time orders"),
                    width="stretch")

# ---------- Customers ----------
with tab_customers:
    rfm = query("""
        select rfm_segment, count(*) as customers, sum(monetary) as revenue
        from analytics.mart_customer_rfm group by 1 order by 2 desc
    """)
    st.plotly_chart(px.bar(rfm, x="rfm_segment", y="customers", title="Customers by RFM segment"),
                    width="stretch")

    cohort = query("""
        select strftime(cohort_month, '%Y-%m') as cohort, months_since_first, retention_rate
        from analytics.mart_cohort_retention
        where months_since_first between 1 and 12
    """)
    heat = cohort.pivot(index="cohort", columns="months_since_first", values="retention_rate")
    st.plotly_chart(px.imshow(heat, text_auto=".1%", aspect="auto",
                              title="Cohort retention (months since first order)",
                              color_continuous_scale="Blues"),
                    width="stretch")

# ---------- Sellers ----------
with tab_sellers:
    sellers = query("""
        select seller_id, seller_state, top_category, orders, gmv,
               avg_delivery_days, late_rate, avg_review_score, seller_tier
        from analytics.mart_seller_performance
        order by gmv desc limit 50
    """)
    st.dataframe(sellers, width="stretch", hide_index=True)
