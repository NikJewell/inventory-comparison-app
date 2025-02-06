import pandas as pd
import streamlit as st
import os
import glob

# Set page configuration for a wider view
st.set_page_config(layout="wide")

st.title("Inventory Comparison Report")

# File uploader for user flexibility
st.subheader("Upload Inventory Files")
prod_file = st.file_uploader("Upload PROD Inventory File", type=["xlsx"])
uat_file = st.file_uploader("Upload UAT Inventory File", type=["xlsx"])
dev_file = st.file_uploader("Upload DEV Inventory File", type=["xlsx"])

if not prod_file or not uat_file or not dev_file:
    st.warning("Please upload all three files to proceed.")
    st.stop()

# Load all three files
def load_excel(file):
    return pd.read_excel(file, sheet_name="Data")

prod_df = load_excel(prod_file)
uat_df = load_excel(uat_file)
dev_df = load_excel(dev_file)

# Standardize column names
def clean_column_names(df):
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df

prod_df = clean_column_names(prod_df)
uat_df = clean_column_names(uat_df)
dev_df = clean_column_names(dev_df)

# Define key column
key_column = "inventory_id"

# Merge dataframes on Inventory ID
prod_uat = prod_df.merge(uat_df, on=key_column, how="left", suffixes=("", "_uat"))
prod_dev = prod_df.merge(dev_df, on=key_column, how="left", suffixes=("", "_dev"))

# Find missing Inventory IDs
missing_in_uat = prod_df[~prod_df[key_column].isin(uat_df[key_column])]
missing_in_dev = prod_df[~prod_df[key_column].isin(dev_df[key_column])]

# Identify mismatched columns
common_columns = list(set(prod_df.columns) & set(uat_df.columns) & set(dev_df.columns) - {key_column})

def find_mismatches(df1, df2, suffix):
    mismatch_data = []
    for col in common_columns:
        col_compare = col + suffix
        if col_compare in df2.columns:
            mismatched_rows = df1[df1[col] != df2[col_compare]][[key_column, col]].copy()
            mismatched_rows["expected_value"] = df1[col].astype(str)
            mismatched_rows["actual_value"] = df2[col_compare].astype(str)
            mismatched_rows["column_name"] = col
            mismatch_data.append(mismatched_rows)
    return pd.concat(mismatch_data, ignore_index=True) if mismatch_data else pd.DataFrame()

mismatches_uat = find_mismatches(prod_uat, prod_uat, "_uat")
mismatches_dev = find_mismatches(prod_dev, prod_dev, "_dev")

# Summary DataFrame
summary = pd.DataFrame({
    "Environment": ["PROD", "UAT", "DEV"],
    "Total Inventory Items": [len(prod_df), len(uat_df), len(dev_df)],
    "Missing in UAT": [len(missing_in_uat), None, None],
    "Missing in DEV": [len(missing_in_dev), None, None],
    "Total Mismatches in UAT": [len(mismatches_uat), None, None],
    "Total Mismatches in DEV": [len(mismatches_dev), None, None]
})

# Display Summary at the Top
st.subheader("Summary Report")
st.dataframe(summary, use_container_width=True)

# Display Missing Items First
st.subheader("Missing Item Details")
with st.expander("Missing in UAT"):
    st.dataframe(missing_in_uat, use_container_width=True)
    st.download_button("Download Missing in UAT Report", missing_in_uat.to_csv(index=False), "missing_in_uat.csv", "text/csv")

with st.expander("Missing in DEV"):
    st.dataframe(missing_in_dev, use_container_width=True)
    st.download_button("Download Missing in DEV Report", missing_in_dev.to_csv(index=False), "missing_in_dev.csv", "text/csv")

# Display Mismatched Items per Line Item
st.subheader("Mismatch Details")
with st.expander("Mismatches in UAT - Per Line Item"):
    if mismatches_uat.empty:
        st.write("No mismatches found in UAT.")
    else:
        st.dataframe(mismatches_uat, use_container_width=True)
        st.download_button("Download UAT Mismatch Report", mismatches_uat.to_csv(index=False), "uat_mismatches.csv", "text/csv")

with st.expander("Mismatches in DEV - Per Line Item"):
    if mismatches_dev.empty:
        st.write("No mismatches found in DEV.")
    else:
        st.dataframe(mismatches_dev, use_container_width=True)
        st.download_button("Download DEV Mismatch Report", mismatches_dev.to_csv(index=False), "dev_mismatches.csv", "text/csv")

# Final Note
st.write("Run the script using `streamlit run compare_inventory.py` to view results interactively.")
