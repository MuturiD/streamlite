# -*- coding: utf-8 -*-
"""
Created on Mon Aug 26 09:20:27 2024

@author: FrancisKioni
@contributor: DavidMuturi
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
from PIL import Image
import requests
import openpyxl

# Load the M-Gas logo
logo_url = "https://mgas.ke/wp-content/uploads/2023/08/mgas-logo.png"
logo_image = Image.open(requests.get(logo_url, stream=True).raw)

# Set the page configuration
st.set_page_config(
    page_title="M-Gas Stocktake Analysis",
    page_icon=logo_image,
    layout="wide",
    initial_sidebar_state="expanded",
)


# Display the logo and title in the sidebar
st.sidebar.image(logo_image, use_column_width=True)
st.sidebar.title("M-Gas Stocktake Analysis")
st.sidebar.markdown("<h3 style='text-align: center; color: #A9A9A9;'>This scripts helps to generate csv files which can be used to update the stock value in the system. <br>"
                    "it takes the raw scans of cylinders in each depot as the input <br>"
                    "You can download each of the displayed tables </h3>"
                    , unsafe_allow_html=True)

# Main header
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>M-Gas Stocktake Analysis</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #4CAF50;'>Upload, Process, and Analyze Your Stocktake Data</h3>",
            unsafe_allow_html=True)

# Upload Excel files
uploaded_files = st.file_uploader("Upload Depot Stock Take Excel files", type="xlsx", accept_multiple_files=True)

# Process the uploaded files
if uploaded_files:
    df_list = []
    for file in uploaded_files:
        # Read each Excel file with all sheets
        sheets_dict = pd.read_excel(file, sheet_name=None)

        for sheet_name, df in sheets_dict.items():
            if not df.empty:  # Check if the dataframe is not empty
                # Rename the first column to 'QR'
                df.rename(columns={df.columns[0]: "QR"}, inplace=True)

                # Add an empty row at the beginning
                empty_row = pd.DataFrame([[np.nan] * len(df.columns)], columns=df.columns)
                df = pd.concat([empty_row, df], ignore_index=True)

                # Add the file path and sheet name as new columns
                df['file_path'] = file.name
                df['sheet_name'] = sheet_name

                # Append the processed dataframe to the list
                df_list.append(df)

    # Concatenate all dataframes into a single dataframe
    if df_list:  # Check if df_list is not empty
        stocktake_df = pd.concat(df_list, ignore_index=True)


        # st.write("### ALL DEPOTS STOCK:")
        # st.dataframe(stocktake_df.head(), width=1500)

        # Define the state based on sheet_name
        def get_state(row):
            if row['sheet_name'] == 'Full Cylinders':
                return 'Available'
            elif row['sheet_name'] == 'Half Cylinders':
                return 'Not Ready'
            elif row['sheet_name'] in ['Full Defectives', 'Half Defectives']:
                return 'Defective'
            else:
                return 'Unknown'


        stocktake_df['state'] = stocktake_df.apply(get_state, axis=1)

        # Extract depot name from file path
        stocktake_df['depot'] = stocktake_df['file_path'].apply(lambda x: x.split('/')[-1].split('.')[0])


        # Clean QR codes

        def clean_qr(qr_code):
            if pd.isna(qr_code):
                return qr_code
            elif isinstance(qr_code, str):
                match = re.search(r'[^/]*$', qr_code)  # Extract everything after the last '/'
                if match:
                    return match.group(0).upper()
                return qr_code.upper()
            else:
                return str(qr_code).upper()


        stocktake_df['QR'] = stocktake_df['QR'].apply(clean_qr)
        stocktake_df.head()
        st.write("### ALL DEPOTS STOCK-processed:")
        st.dataframe(stocktake_df.head(), width=1500)

        # Generate a pivot table for QR count per state per depot
        pivot_table = stocktake_df.pivot_table(index='depot', columns='state', values='QR', aggfunc='count',
                                               fill_value=0)
        pivot_table['Total'] = pivot_table.sum(axis=1)

        st.write("### Pivot Table (QR Count per State per Depot):")
        st.dataframe(pivot_table)

        # Find duplicates
        duplicates = stocktake_df[stocktake_df.duplicated(subset=['QR'], keep=False)]
        duplicates=duplicates[duplicates['QR'].notna()]
        result = duplicates[['QR', 'depot', 'state']]

        st.write("### LIST 1 - Duplicates:")
        st.dataframe(result)
        # Generate a pivot table for duplicates per state per depot
        duplicates_pivot_table = duplicates.pivot_table(index='depot', columns='state', values='QR', aggfunc='count',
                                                                              fill_value=0)
        duplicates_pivot_table['Total'] = duplicates_pivot_table.sum(axis=1)

        st.write("### Summary Table (Duplicate QR Count per Depot with State):")
        st.dataframe(duplicates_pivot_table)
    else:
        st.warning("No data to merge. All sheets were empty.")
