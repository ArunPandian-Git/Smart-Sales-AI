import pandas as pd

# Extract
df = pd.read_csv("data_sales.csv")

# Transform: convert the date column
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

# Remove duplicate order IDs
df = df.drop_duplicates(subset=["OrderID"])

# Remove records with missing required values
required_columns = [
    "OrderID", "Date", "Product",
    "Quantity", "UnitPrice", "Cost"
]

df = df.dropna(subset=required_columns)

# Validate numeric values
df = df[
    (df["Quantity"] > 0) &
    (df["UnitPrice"] >= 0) &
    (df["Cost"] >= 0)
].copy()

# Calculate revenue and profit
df["Revenue"] = df["Quantity"] * df["UnitPrice"]

df["Profit"] = (
    df["Quantity"] * (df["UnitPrice"] - df["Cost"])
)

# Load: save the cleaned dataset
df.to_csv("data_processed_sales.csv", index=False)

print("ETL pipeline completed successfully!")

print(
    df[["OrderID", "Product", "Revenue", "Profit"]]
)

print("\nTotal Revenue:", df["Revenue"].sum())
print("Total Profit:", df["Profit"].sum())
