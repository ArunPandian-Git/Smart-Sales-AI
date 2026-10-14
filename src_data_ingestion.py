import pandas as pd

# Load sales data
df = pd.read_csv("data_sales.csv")

# Display the first five records
print("First five records:")
print(df.head())

# Display the number of rows and columns
print("\nDataset shape:")
print(df.shape)

# Display column information
print("\nDataset information:")
df.info()
