import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import date

# ─────────────────────────────────────────────────────────────────────────────
# SMARTSALES AI | Premium Sales Intelligence
# Compatible with the existing data/processed_sales.csv schema:
# Date, Revenue, Profit, OrderID, Product, Region
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SmartSales AI | Sales Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

GREEN = "#16A34A"
DARK_GREEN = "#064E3B"
MINT = "#D1FAE5"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { --green:#16a34a; --deep:#064e3b; --mint:#d1fae5; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background:linear-gradient(145deg,#f5fbf7 0%,#edf7f0 48%,#f8fcf9 100%); }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#052e24,#064e3b); }
[data-testid="stSidebar"] * { color:#e8fff1 !important; }
[data-testid="stSidebar"] [data-testid="stFileUploader"] { background:#ffffff12;border:1px solid #ffffff25;border-radius:14px;padding:10px; }
.block-container { padding-top:1.6rem; padding-bottom:3rem; max-width:1500px; }
.hero { background:linear-gradient(115deg,#052e24 0%,#087443 58%,#16a34a 100%);
border-radius:24px;padding:30px 34px;color:white;position:relative;overflow:hidden;
box-shadow:0 18px 45px #064e3b20;margin-bottom:22px; }
.hero:after { content:"";position:absolute;width:260px;height:260px;border:40px solid #ffffff12;border-radius:50%;right:-70px;top:-95px; }
.hero-kicker { color:#bbf7d0;letter-spacing:2.2px;font-size:11px;font-weight:800;text-transform:uppercase; }
.hero h1 { font-family:Manrope,sans-serif;font-size:clamp(30px,4vw,48px);font-weight:800;line-height:1.1;margin:12px 0 8px;color:white; }
.hero p { color:#dcfce7;font-size:15px;max-width:720px;margin:0; }
.section-title { font-family:Manrope,sans-serif;color:#064e3b;font-size:20px;font-weight:800;margin:20px 0 12px; }
.kpi { background:white;border:1px solid #dcefe2;border-radius:18px;padding:18px 20px;box-shadow:0 7px 24px #064e3b0a;min-height:126px; }
.kpi-label { color:#64748b;font-size:11px;letter-spacing:1.1px;font-weight:800;text-transform:uppercase; }
.kpi-value { color:#064e3b;font-family:Manrope,sans-serif;font-size:clamp(22px,2.3vw,31px);font-weight:800;margin:8px 0 2px; }
.kpi-note { color:#16a34a;font-size:12px;font-weight:600; }
.panel { background:white;border:1px solid #dcefe2;border-radius:18px;padding:18px;box-shadow:0 7px 24px #064e3b08; }
div[data-testid="stMetric"] { background:white;border:1px solid #dcefe2;border-radius:16px;padding:16px; }
.stButton>button, .stDownloadButton>button { border-radius:11px;border:1px solid #bbf7d0;background:#ecfdf5;color:#065f46;font-weight:700; }
.stButton>button:hover, .stDownloadButton>button:hover { background:#16a34a;color:white;border-color:#16a34a; }
[data-testid="stDataFrame"] { border:1px solid #dcefe2;border-radius:14px;overflow:hidden; }
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

def money(value):
    try:
        return f"₹{float(value):,.0f}"
    except (ValueError, TypeError):
        return "₹0"

def load_data():
    default_path = Path("data/processed_sales.csv")
    uploaded = st.sidebar.file_uploader(
        "Upload sales data",
        type=["csv", "xlsx", "xls"],
        help="Upload your own file, or use the project's processed_sales.csv file."
    )
    if uploaded is not None:
        try:
            if uploaded.name.lower().endswith((".xlsx", ".xls")):
                data = pd.read_excel(uploaded)
            else:
                data = pd.read_csv(uploaded)
            st.sidebar.success(f"Loaded: {uploaded.name}")
            return data, uploaded.name
        except Exception as exc:
            st.sidebar.error(f"Could not read file: {exc}")
            return None, None
    if default_path.exists():
        try:
            return pd.read_csv(default_path), str(default_path)
        except Exception as exc:
            st.sidebar.error(f"Could not read project dataset: {exc}")
            return None, None
    st.sidebar.info("Upload a CSV or Excel sales file to begin.")
    return None, None

def find_column(frame, candidates):
    lookup = {str(c).strip().lower(): c for c in frame.columns}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    return None

def normalize_data(raw):
    if raw is None or raw.empty:
        return None, {}
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    mapping = {
        "date": find_column(df, ["Date", "Order Date", "Transaction Date", "Sales Date"]),
        "revenue": find_column(df, ["Revenue", "Sales", "Total Sales", "Amount", "Net Sales"]),
        "profit": find_column(df, ["Profit", "Net Profit", "Margin"]),
        "order": find_column(df, ["OrderID", "Order ID", "Order", "Transaction ID", "Invoice"]),
        "product": find_column(df, ["Product", "Product Name", "Item", "Item Name", "SKU"]),
        "region": find_column(df, ["Region", "State", "Country", "City", "Territory", "Location"]),
        "quantity": find_column(df, ["Quantity", "Units", "Qty", "Units Sold"]),
        "category": find_column(df, ["Category", "Product Category", "Segment"]),
    }
    if mapping["revenue"] is None:
        st.error("A revenue/sales column is required. Expected a column such as Revenue, Sales, or Amount.")
        st.write("Detected columns:", ", ".join(map(str, df.columns)))
        return None, mapping
    df["_revenue"] = pd.to_numeric(df[mapping["revenue"]], errors="coerce").fillna(0)
    df["_profit"] = pd.to_numeric(df[mapping["profit"]], errors="coerce").fillna(0) if mapping["profit"] else 0
    df["_date"] = pd.to_datetime(df[mapping["date"]], errors="coerce") if mapping["date"] else pd.NaT
    df["_product"] = df[mapping["product"]].fillna("Unspecified").astype(str) if mapping["product"] else "All Products"
    df["_region"] = df[mapping["region"]].fillna("Unspecified").astype(str) if mapping["region"] else "Unspecified"
    df["_category"] = df[mapping["category"]].fillna("Unspecified").astype(str) if mapping["category"] else "Unspecified"
    df["_quantity"] = pd.to_numeric(df[mapping["quantity"]], errors="coerce").fillna(0) if mapping["quantity"] else 0
    df["_order"] = df[mapping["order"]].astype(str) if mapping["order"] else df.index.astype(str)
    return df, mapping

raw, source_name = load_data()

st.markdown("""
<div class="hero">
  <div class="hero-kicker">SMARTSALES AI · BUSINESS INTELLIGENCE</div>
  <h1>Turn sales data into<br>your next growth move.</h1>
  <p>An executive-ready sales intelligence workspace. Explore performance, uncover trends,
  compare regions and products, and turn your business data into clear decisions.</p>
</div>
""", unsafe_allow_html=True)

if raw is None:
    st.markdown('<div class="panel"><h3 style="color:#064e3b">Your intelligence workspace is ready</h3><p>Upload your sales CSV or Excel file from the sidebar. SmartSales AI will analyze the file you provide—no fabricated demo metrics.</p></div>', unsafe_allow_html=True)
    st.stop()

df, mapping = normalize_data(raw)
if df is None:
    st.stop()

# Data quality and filtering
with st.sidebar:
    st.markdown("### 🎛️ Analysis controls")
    st.caption(f"Source: {Path(source_name).name}")
    st.caption(f"{len(df):,} rows · {len(raw.columns):,} fields")
    date_values = df["_date"].dropna()
    if not date_values.empty:
        min_date, max_date = date_values.min().date(), date_values.max().date()
        selected_dates = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    else:
        selected_dates = None
    products = sorted(df["_product"].dropna().unique().tolist())
    regions = sorted(df["_region"].dropna().unique().tolist())
    categories = sorted(df["_category"].dropna().unique().tolist())
    selected_products = st.multiselect("Products", products, default=products)
    selected_regions = st.multiselect("Regions", regions, default=regions)
    selected_categories = st.multiselect("Categories", categories, default=categories)

filtered = df.copy()
if selected_dates and isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2 and mapping["date"]:
    start, end = pd.Timestamp(selected_dates[0]), pd.Timestamp(selected_dates[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    filtered = filtered[filtered["_date"].between(start, end)]
filtered = filtered[filtered["_product"].isin(selected_products)]
filtered = filtered[filtered["_region"].isin(selected_regions)]
filtered = filtered[filtered["_category"].isin(selected_categories)]

revenue = filtered["_revenue"].sum()
profit = filtered["_profit"].sum()
orders = filtered["_order"].nunique()
units = filtered["_quantity"].sum()
margin = (profit / revenue * 100) if revenue else 0
previous_revenue = None
if mapping["date"] and not filtered["_date"].dropna().empty:
    # Compare selected period against the immediately preceding period of equal duration.
    if selected_dates and len(selected_dates) == 2:
        days = max((pd.Timestamp(selected_dates[1]) - pd.Timestamp(selected_dates[0])).days + 1, 1)
        prior_start = pd.Timestamp(selected_dates[0]) - pd.Timedelta(days=days)
        prior_end = pd.Timestamp(selected_dates[0]) - pd.Timedelta(seconds=1)
        prior = df[df["_date"].between(prior_start, prior_end)]
        prior = prior[prior["_product"].isin(selected_products) & prior["_region"].isin(selected_regions) & prior["_category"].isin(selected_categories)]
        previous_revenue = prior["_revenue"].sum()

growth_text = "Period comparison unavailable"
if previous_revenue is not None:
    growth = ((revenue - previous_revenue) / abs(previous_revenue) * 100) if previous_revenue else None
    growth_text = f"{growth:+.1f}% vs previous period" if growth is not None else "No previous-period revenue"

st.markdown('<div class="section-title">Executive snapshot</div>', unsafe_allow_html=True)
k1, k2, k3, k4, k5 = st.columns(5)
for col, label, value, note in [
    (k1, "Total revenue", money(revenue), growth_text),
    (k2, "Net profit", money(profit), "Filtered performance"),
    (k3, "Orders", f"{orders:,}", "Unique transactions"),
    (k4, "Profit margin", f"{margin:.1f}%", "Profit ÷ revenue"),
    (k5, "Units sold", f"{units:,.0f}", "Quantity in selected data"),
]:
    col.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>', unsafe_allow_html=True)

st.markdown('<div class="section-title">Performance overview</div>', unsafe_allow_html=True)
left, right = st.columns([1.55, 1])
with left:
    if mapping["date"] and filtered["_date"].notna().any():
        trend = filtered.dropna(subset=["_date"]).groupby(filtered.dropna(subset=["_date"])["_date"].dt.to_period("M").astype(str), as_index=False)["_revenue"].sum()
        trend.columns = ["Month", "Revenue"]
        fig = px.area(trend, x="Month", y="Revenue", title="Revenue momentum", markers=True)
        fig.update_traces(line_color=GREEN, fillcolor="rgba(22,163,74,0.13)")
    else:
        trend = filtered.groupby("_product", as_index=False)["_revenue"].sum().sort_values("_revenue", ascending=False).head(15)
        fig = px.bar(trend, x="_product", y="_revenue", title="Revenue by product", color="_revenue", color_continuous_scale=["#bbf7d0", "#16a34a", "#064e3b"])
        fig.update_layout(xaxis_title="Product", yaxis_title="Revenue")
    fig.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#164e36", title_font_size=17, margin=dict(l=10,r=10,t=55,b=10))
    st.plotly_chart(fig, use_container_width=True)
with right:
    regional = filtered.groupby("_region", as_index=False)["_profit"].sum().sort_values("_profit", ascending=False)
    fig = px.bar(regional, x="_profit", y="_region", orientation="h", title="Profit by region", color="_profit", color_continuous_scale=["#bbf7d0", "#16a34a", "#064e3b"])
    fig.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#164e36", title_font_size=17, margin=dict(l=10,r=10,t=55,b=10), coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="section-title">Product intelligence</div>', unsafe_allow_html=True)
p1, p2 = st.columns(2)
product_revenue = filtered.groupby("_product", as_index=False).agg(Revenue=("_revenue","sum"), Profit=("_profit","sum")).sort_values("Revenue", ascending=False).head(10)
with p1:
    fig = px.bar(product_revenue, x="Revenue", y="_product", orientation="h", title="Top products by revenue", color="Revenue", color_continuous_scale=["#bbf7d0", "#16a34a", "#064e3b"])
    fig.update_layout(template="plotly_white", yaxis={"categoryorder":"total ascending"}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#164e36", title_font_size=17, margin=dict(l=10,r=10,t=55,b=10), coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)
with p2:
    fig = px.scatter(product_revenue, x="Revenue", y="Profit", size="Revenue", hover_name="_product", title="Revenue vs profit · product portfolio", color="Profit", color_continuous_scale=["#bbf7d0", "#16a34a", "#064e3b"])
    fig.update_layout(template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#164e36", title_font_size=17, margin=dict(l=10,r=10,t=55,b=10))
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="section-title">AI-assisted business signals</div>', unsafe_allow_html=True)
signals = []
if revenue > 0:
    signals.append(f"**Profitability:** Current filtered profit margin is **{margin:.1f}%**. Review product and regional contribution to understand what is driving it.")
if not product_revenue.empty:
    top = product_revenue.iloc[0]
    signals.append(f"**Revenue leader:** **{top['_product']}** is the leading product in this view, contributing **{money(top['Revenue'])}** in revenue.")
if not regional.empty:
    best_region = regional.iloc[0]
    signals.append(f"**Regional strength:** **{best_region['_region']}** currently leads the selected regions by total profit (**{money(best_region['_profit'])}**).")
if revenue and profit < 0:
    signals.append("**Attention:** The filtered dataset shows negative total profit. Investigate costs, discounting, and loss-making transactions.")
if not signals:
    signals.append("Select a broader date range or filters to reveal meaningful business patterns.")
for signal in signals:
    st.markdown(f'<div class="panel" style="margin-bottom:9px;border-left:4px solid #16a34a">{signal}</div>', unsafe_allow_html=True)
st.caption("These are data-derived analytical observations, not forecasts or guarantees. AI-generated narrative can be added through a configured model provider.")

st.markdown('<div class="section-title">Transaction explorer</div>', unsafe_allow_html=True)
search = st.text_input("Search visible transactions", placeholder="Search across transaction fields…")
table = filtered.copy()
if search.strip():
    mask = table.astype(str).apply(lambda col: col.str.contains(search.strip(), case=False, na=False)).any(axis=1)
    table = table[mask]
st.dataframe(table.drop(columns=[c for c in table.columns if c.startswith("_")], errors="ignore"), use_container_width=True, hide_index=True, height=340)

csv_bytes = filtered.drop(columns=[c for c in filtered.columns if c.startswith("_")], errors="ignore").to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ Export filtered transactions (CSV)", csv_bytes, file_name="smartsales_filtered_report.csv", mime="text/csv")

with st.expander("Dataset quality & field mapping"):
    quality = pd.DataFrame({
        "Check": ["Rows analyzed", "Duplicate rows", "Missing values", "Revenue field", "Profit field", "Date field"],
        "Result": [f"{len(filtered):,}", f"{filtered.duplicated().sum():,}", f"{int(filtered.isna().sum().sum()):,}",
                   mapping["revenue"] or "Not detected", mapping["profit"] or "Not detected", mapping["date"] or "Not detected"]
    })
    st.dataframe(quality, use_container_width=True, hide_index=True)
    st.caption("Optional fields are handled safely. Revenue is required for financial KPIs; profit, date, order, product, and region fields are detected when present.")

st.markdown('<div style="text-align:center;color:#658574;padding:24px 0 0;font-size:12px">SMARTSALES AI · Sales Intelligence Workspace · Built for clearer business decisions</div>', unsafe_allow_html=True)
