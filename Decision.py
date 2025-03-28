import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter 
import re
import numpy as np
from google.cloud import bigquery
from rich.text import Text
import textwrap
import os
from google.oauth2 import service_account
from google.auth import default
import toml



credentials_info = st.secrets["GOOGLE_CREDENTIAL_FOR_AMAZON"]

credentials = service_account.Credentials.from_service_account_info(credentials_info)

# Initialize BigQuery Client with correct credentials
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

# Define your SQL query to load data
query = """
SELECT *
FROM `amaz-project-438116.Existing_data.Sales` 
LIMIT 1000  -- You can adjust the limit as needed
"""

# Load data into a DataFrame
df = client.query(query).to_dataframe()


def prepare_data(df):
    df['coll_date'] = pd.to_datetime(df['coll_date'])
    df = df.sort_values(by='coll_date')
    last_three_months = df['Month'].drop_duplicates().tail(3).tolist()

    if len(last_three_months) == 3:
        third_last_month, last_month, current_month = last_three_months
    elif len(last_three_months) == 2:
        third_last_month = None
        last_month, current_month = last_three_months
    else:
        third_last_month = None
        last_month = current_month = last_three_months[0]

    return df, third_last_month, last_month, current_month, last_three_months







def show_Decision(df):
    
    # Display the dataframe to verify the data
    st.write("Data Sample:", df.head())

    # to visualize total rows
    num_rows = len(df)
    st.write(f"Row Total: {num_rows}")




    

     # PRODUCTS THAT COSTS $0-20, AND HAS EXCELLENT RATING IN THE LAST 3 MONTHS

    st.markdown(
    "<h1 style='color:#BD7E58; font-size: 24px; font-weight: bold; font-style: italic;'>Looking for products to sell? here you go!!!</h1>", 
    unsafe_allow_html=True
)

    st.markdown(
    "<h1 style='color:green; font-size: 17px; font-weight: bold; font-style: italic;'>$0-20 <span style='color:grey;'>Products with <span style='color:green;'>Excellent Rating</span> and <span style='color:green;'>Positive Growth </span><span style='color:blue;'>in the last 3 months</h1>", 
    unsafe_allow_html=True
)
    

    # Prepare the data (using the function)
    df, third_last_month, last_month, current_month, last_three_months = prepare_data(df)

    # Check if at least last two months are available
    if len(last_three_months) < 2:
        st.write("Suficient data are not available yet.")
        return pd.DataFrame()


    # FILTER ALL PRODUCTS SOLD IN THE LAST 3 MONTHS
    products_sold_last_months = df[df['Month'].isin(last_three_months)]

    # Find common products sold across the selected months (intersection of product names)
    if third_last_month:
        # If three months are available, find products sold in all three months
        common_products = set(products_sold_last_months[products_sold_last_months['Month'] == current_month]['Product Name']).intersection(
            set(products_sold_last_months[products_sold_last_months['Month'] == last_month]['Product Name']),
            set(products_sold_last_months[products_sold_last_months['Month'] == third_last_month]['Product Name'])
        )
        


        # Filter the DataFrame for these common products
        common_products_df = products_sold_last_months[products_sold_last_months['Product Name'].isin(common_products)]

        # Filter for Price_cat $0-20 only
        common_products_df = common_products_df[common_products_df['Price_cat'] == '$0-20']

        common_products_df = common_products_df[common_products_df['Rating_cat'] == 'Excellent']
                                                
        # Group by Product Name, Price_cat, and Month, and sum the quantities sold
        result = common_products_df.groupby(['Product Name', 'Price_cat', 'Rating_cat', 'Month'])['Qty Sold'].sum().reset_index()

        # Pivot the data to get separate columns for each month's quantity sold
        pivot_result = result.pivot(index='Product Name', columns='Month', values='Qty Sold').reset_index()

        # Calculate growth between the current month and third last month
        
        pivot_result['Growth'] = ((pivot_result[current_month] - pivot_result[third_last_month]) / pivot_result[third_last_month]) * 100

        # Filter for rows with positive growth
        pivot_result = pivot_result[pivot_result['Growth'] > 0]

        # Format the columns for better readability
        pivot_result[last_month] = pivot_result[last_month].apply(lambda x: f"{x:,}")
        pivot_result[current_month] = pivot_result[current_month].apply(lambda x: f"{x:,}")
        pivot_result['Growth'] = pivot_result['Growth'].apply(lambda x: f"{x:,.0f}%")

        # Format the third last month if data is available
        
        pivot_result[third_last_month] = pivot_result[third_last_month].apply(lambda x: f"{x:,}")
        pivot_result = pivot_result[['Product Name', third_last_month, last_month, current_month, 'Growth']]
        
        # Reset index and start numbering from 1
        pivot_result.reset_index(drop=True, inplace=True)
        pivot_result.index += 1  # Start numbering from 1

        # Display the result as a table in Streamlit
        st.dataframe(pivot_result)  # Display the DataFrame as a table

    else:
        st.markdown(
    "<h1 style='color:#4A4A48; font-size: 16px; font-weight: bold; font-style: italic;'>sorry...last 3 months data not available at the momemt... </h1>", 
    unsafe_allow_html=True
)
    


    
    st.markdown(
    "<h1 style='color:green; font-size: 16px; font-weight: bold; font-style: italic;'>$0-20 <span style='color:grey;'>Products with <span style='color:green;'>Excellent Rating</span> and <span style='color:green;'>Positive Growth  </span><span style='color:blue;'>in the last 2 months</h1>", 
    unsafe_allow_html=True
)
    

    # Prepare the data (using the function)
    df, third_last_month, last_month, current_month, last_three_months = prepare_data(df)


    # Filter products sold in the last two  months
    products_sold_last_months = df[df['Month'].isin(last_three_months)]

    # Find common products sold across the selected months (intersection of product names)
    if last_month:
        # If 2 months are available, find products sold in all 2 months
        common_products = set(products_sold_last_months[products_sold_last_months['Month'] == current_month]['Product Name']).intersection(
            set(products_sold_last_months[products_sold_last_months['Month'] == last_month]['Product Name'])
        )

        # Filter the DataFrame for these common products
        common_products_df = products_sold_last_months[products_sold_last_months['Product Name'].isin(common_products)]

        # Filter for Price_cat $0-20 only
        common_products_df = common_products_df[common_products_df['Price_cat'] == '$0-20']

        common_products_df = common_products_df[common_products_df['Rating_cat'] == 'Excellent']


                                            
        # Group by Product Name, Price_cat, and Month, and sum the quantities sold
        result = common_products_df.groupby(['Product Name', 'Price_cat', 'Rating_cat', 'Month'])['Qty Sold'].sum().reset_index()

        # Pivot the data to get separate columns for each month's quantity sold
        pivot_result = result.pivot(index='Product Name', columns='Month', values='Qty Sold').reset_index()



        # Calculate growth between the current month and last month
        
        pivot_result['Growth'] = ((pivot_result[current_month] - pivot_result[last_month]) / pivot_result[last_month]) * 100

        # Filter for rows with positive growth
        pivot_result = pivot_result[pivot_result['Growth'] > 0]


        pivot_result = pivot_result[
        (pivot_result[current_month] > pivot_result[last_month])
        ]

        # Format the columns for better readability
        pivot_result[last_month] = pivot_result[last_month].apply(lambda x: f"{x:,}")
        pivot_result[current_month] = pivot_result[current_month].apply(lambda x: f"{x:,}")
        pivot_result['Growth'] = pivot_result['Growth'].apply(lambda x: f"{x:,.0f}%")

        pivot_result = pivot_result[['Product Name',  last_month, current_month, 'Growth']]
        
        # Reset index and start numbering from 1
        pivot_result.reset_index(drop=True, inplace=True)
        pivot_result.index += 1  # Start numbering from 1

        # Display the result as a table in Streamlit
        st.dataframe(pivot_result)  # Display the DataFrame as a table
    else:
          st.markdown(
    "<h1 style='color:#4A4A48; font-size: 16px; font-weight: bold; font-style: italic;'>sorry...last 2 months data not available at the momemt... </h1>", 
    unsafe_allow_html=True
    )
    





