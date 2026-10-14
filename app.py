import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="SmartSales AI",
    layout="wide"
)

st.title("SmartSales AI Dashboard")

# Load processed data
df = pd.read_csv("data/processed_sales.csv")

df["Date"] = pd.to_datetime(df["Date"])

# KPI calculations
total_revenue = df["Revenue"].sum()
total_profit = df["Profit"].sum()
total_orders = df["OrderID"].nunique()

# Display metrics
col1, col2, col3 = st.columns(3)

col1.metric("Total Revenue", f"₹{total_revenue:,.2f}")
col2.metric("Total Profit", f"₹{total_profit:,.2f}")
col3.metric("Total Orders", total_orders)

# Product revenue
product_sales = (
    df.groupby("Product", as_index=False)["Revenue"]
    .sum()
    .sort_values("Revenue", ascending=False)
)

fig1 = px.bar(
    product_sales,
    x="Product",
    y="Revenue",
    title="Revenue by Product"
)

st.plotly_chart(fig1, use_container_width=True)

# Regional profit
region_profit = (
    df.groupby("Region", as_index=False)["Profit"]
    .sum()
)

fig2 = px.pie(
    region_profit,
    names="Region",
    values="Profit",
    title="Profit by Region"
)

st.plotly_chart(fig2, use_container_width=True)

# Sales table
st.subheader("Sales Transactions")

st.dataframe(df, use_container_width=True)
