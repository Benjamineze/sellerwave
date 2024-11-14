import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import missingno as msno
from collections import Counter 
import re
import numpy as np
from google.cloud import bigquery
from rich.console import Console
from rich.text import Text
import textwrap
import os
from google.oauth2 import service_account
from google.auth import default
import toml




#Load credentials from TOML file
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


    


def show_stories(df):
    st.markdown(
    "<h1 style='color:#7D4E57; font-size: 24px; font-style: italic;'>Growth Analysis</h1>", 
    unsafe_allow_html=True)


 # All PRODUCTS WITH POSITIVE GROWTH IN THE LAST 3 MONTHS

    st.markdown(
    "<h1 style='color:grey; font-size: 16px; font-weight: bold; font-style: italic;'>All Products with <span style='color:green;'>positive Growth <span style='color:blue;'>in the last 3 months</h1>", 
    unsafe_allow_html=True
    )

    # Prepare the data (using the function)
    df, third_last_month, last_month, current_month, last_three_months = prepare_data(df)

    # Filter products sold in the last two or three months
    products_sold_last_months = df[df['Month'].isin(last_three_months)]

    # Find common products sold across the selected months (intersection of product names)
    if third_last_month:
        # If three months are available, find products sold in all three months
        common_products = set(products_sold_last_months[products_sold_last_months['Month'] == current_month]['Product Name']).intersection(
            set(products_sold_last_months[products_sold_last_months['Month'] == last_month]['Product Name']),
            set(products_sold_last_months[products_sold_last_months['Month'] == third_last_month]['Product Name'])
        )
    else:
        # If fewer than three months are available, find products sold in just the last two months
        common_products = set(products_sold_last_months[products_sold_last_months['Month'] == current_month]['Product Name']).intersection(
            set(products_sold_last_months[products_sold_last_months['Month'] == last_month]['Product Name'])
        )

    # Filter the DataFrame for these common products
    common_products_df = products_sold_last_months[products_sold_last_months['Product Name'].isin(common_products)]

    # Group by Product Name and Month, and sum the quantities sold
    result = common_products_df.groupby(['Product Name', 'Month'])['Qty Sold'].sum().reset_index()

    # Pivot the data to get separate columns for each month's quantity sold
    pivot_result = result.pivot(index='Product Name', columns='Month', values='Qty Sold').reset_index()

    # Calculate growth between the current month and last month
    pivot_result['Growth'] = (pivot_result[current_month] - pivot_result[third_last_month])/pivot_result[third_last_month]*100

    # If three months are available, add growth between the third last month and the last month
    #if third_last_month:
        #pivot_result['Growth (Last vs 3rd Last)'] = pivot_result[last_month] - pivot_result[third_last_month]

    # Format growth values to show as percentages and other values with commas
    pivot_result = pivot_result[pivot_result['Growth'] > 0]
    pivot_result[last_month] = pivot_result[last_month].apply(lambda x: f"{x:,}")
    pivot_result[current_month] = pivot_result[current_month].apply(lambda x: f"{x:,}")
    pivot_result['Growth'] = pivot_result['Growth'].apply(lambda x: f"{x:,.0f}%")
    

    # If third month data is available, format it
    if third_last_month:
        pivot_result[third_last_month] = pivot_result[third_last_month].apply(lambda x: f"{x:,}")
        #pivot_result['Growth (Last vs 3rd Last)'] = pivot_result['Growth (Last vs 3rd Last)'].apply(lambda x: f"{x:,}")

    # Adjust column ordering: If third month exists, include it
    if third_last_month:
        pivot_result = pivot_result[['Product Name', third_last_month, last_month, current_month, 'Growth']]
    else:
        pivot_result = pivot_result[['Product Name', last_month, current_month, 'Growth']]

    # Reset index and start counting from 1
    pivot_result.reset_index(drop=True, inplace=True)
    pivot_result.index += 1  # Start numbering from 1
    
    # Display the result in Streamlit
    
    st.table(pivot_result)  # Display the DataFrame as a table


# All PRODUCTS WITH NEGATIVE GROWTH IN THE LAST 3 MONTHS

    st.markdown(
    "<h1 style='color:grey; font-size: 16px; font-weight: bold; font-style: italic;'>All Products with <span style='color:green;'>Negative Growth<span style='color:blue;'> in the last 3 months</h1>", 
    unsafe_allow_html=True
    )

    # Prepare the data (using the function)
    df, third_last_month, last_month, current_month, last_three_months = prepare_data(df)

    # Filter products sold in the last two or three months
    products_sold_last_months = df[df['Month'].isin(last_three_months)]

    # Find common products sold across the selected months (intersection of product names)
    if third_last_month:
        # If three months are available, find products sold in all three months
        common_products = set(products_sold_last_months[products_sold_last_months['Month'] == current_month]['Product Name']).intersection(
            set(products_sold_last_months[products_sold_last_months['Month'] == last_month]['Product Name']),
            set(products_sold_last_months[products_sold_last_months['Month'] == third_last_month]['Product Name'])
        )
    else:
        # If fewer than three months are available, find products sold in just the last two months
        common_products = set(products_sold_last_months[products_sold_last_months['Month'] == current_month]['Product Name']).intersection(
            set(products_sold_last_months[products_sold_last_months['Month'] == last_month]['Product Name'])
        )

    # Filter the DataFrame for these common products
    common_products_df = products_sold_last_months[products_sold_last_months['Product Name'].isin(common_products)]

    # Group by Product Name and Month, and sum the quantities sold
    result = common_products_df.groupby(['Product Name', 'Month'])['Qty Sold'].sum().reset_index()

    # Pivot the data to get separate columns for each month's quantity sold
    pivot_result = result.pivot(index='Product Name', columns='Month', values='Qty Sold').reset_index()

    # Calculate growth between the current month and last month
    pivot_result['Growth'] = (pivot_result[current_month] - pivot_result[third_last_month])/pivot_result[third_last_month]*100

    # Filter for when GROWTH equals zero or Negative
    pivot_result = pivot_result[pivot_result['Growth'] <= 0]

    # Format growth values to show as percentages and other values with commas
    pivot_result[last_month] = pivot_result[last_month].apply(lambda x: f"{x:,}")
    pivot_result[current_month] = pivot_result[current_month].apply(lambda x: f"{x:,}")
    pivot_result['Growth'] = pivot_result['Growth'].apply(lambda x: f"{x:,.0f}%")
    

    # If third month data is available, format it
    if third_last_month:
        pivot_result[third_last_month] = pivot_result[third_last_month].apply(lambda x: f"{x:,}")
        #pivot_result['Growth (Last vs 3rd Last)'] = pivot_result['Growth (Last vs 3rd Last)'].apply(lambda x: f"{x:,}")

    # Adjust column ordering: If third month exists, include it
    if third_last_month:
        pivot_result = pivot_result[['Product Name', third_last_month, last_month, current_month, 'Growth']]
    else:
        pivot_result = pivot_result[['Product Name', last_month, current_month, 'Growth']]

    # Reset index and start counting from 1
    pivot_result.reset_index(drop=True, inplace=True)
    pivot_result.index += 1  # Start numbering from 1
    
    # Display the result in Streamlit
    
    st.table(pivot_result)  # Display the DataFrame as a table





# ALL PRODUCTS WITH MONTH ON MONTH GROWTH IN THE LAST 3 MONTHS


    st.markdown(
    "<h1 style='color:grey; font-size: 16px; font-weight: bold; font-style: italic;'>All Products with <span style='color:green;'>Month-on-Month growth <span style='color:blue;'>in the last 3 months</h1>", 
    unsafe_allow_html=True
    )
    

    # Prepare the data (using the function)
    df, third_last_month, last_month, current_month, last_three_months = prepare_data(df)

    # Filter products sold in the last three months
    products_sold_last_months = df[df['Month'].isin(last_three_months)]

    # Find common products sold across all three months (if available)
    common_products = set(products_sold_last_months[products_sold_last_months['Month'] == current_month]['Product Name']).intersection(
        set(products_sold_last_months[products_sold_last_months['Month'] == last_month]['Product Name']),
        set(products_sold_last_months[products_sold_last_months['Month'] == third_last_month]['Product Name'])
    )

    # Filter the DataFrame for these common products
    common_products_df = products_sold_last_months[products_sold_last_months['Product Name'].isin(common_products)]

    

    # Group by Product Name and Month, and sum the quantities sold
    result = common_products_df.groupby(['Product Name', 'Month'])['Qty Sold'].sum().reset_index()

    # Pivot the data to get separate columns for each month's quantity sold
    pivot_result = result.pivot(index='Product Name', columns='Month', values='Qty Sold').reset_index()

    # Filter the data to only include rows where:
    # current month sales > last month sales AND last month sales > third last month sales
    pivot_result = pivot_result[
        (pivot_result[current_month] > pivot_result[last_month]) &
        (pivot_result[last_month] > pivot_result[third_last_month])
    ]

    # Adjust column ordering: 

    pivot_result = pivot_result[['Product Name', third_last_month, last_month, current_month]]
   

    # Format the columns to show as readable numbers with commas
    pivot_result[last_month] = pivot_result[last_month].apply(lambda x: f"{x:,}")
    pivot_result[current_month] = pivot_result[current_month].apply(lambda x: f"{x:,}")
    pivot_result[third_last_month] = pivot_result[third_last_month].apply(lambda x: f"{x:,}")

    # Reset index and start counting from 1
    pivot_result.reset_index(drop=True, inplace=True)
    pivot_result.index += 1  # Start numbering from 1

    # Display the result in Streamlit
    
    st.table(pivot_result)  # Display the DataFrame as a table



# CURRENT VS LAST MONTH'S GROWTH (2 MONTHS)


    st.write("### last vs current Month's Growth")


    st.markdown(
    "<h1 style='color:grey; font-size: 16px; font-weight: bold; font-style: italic;'>Products with <span style='color:green;'>Month-on-month <span style='color:red;'>Growth <span style='color:blue;'>(2Months)</h1>", 
    unsafe_allow_html=True
    )

    # Prepare the data (using the function)
    df, third_last_month, last_month, current_month, last_three_months = prepare_data(df)

    # Filter products sold in the last three months
    products_sold_last_months = df[df['Month'].isin(last_three_months)]

    # Find common products sold across all three months (if available)
    common_products = set(products_sold_last_months[products_sold_last_months['Month'] == current_month]['Product Name']).intersection(
        set(products_sold_last_months[products_sold_last_months['Month'] == last_month]['Product Name']),
        set(products_sold_last_months[products_sold_last_months['Month'] == third_last_month]['Product Name'])
    )

    # Filter the DataFrame for these common products
    common_products_df = products_sold_last_months[products_sold_last_months['Product Name'].isin(common_products)]

    # Group by Product Name and Month, and sum the quantities sold
    result = common_products_df.groupby(['Product Name', 'Month'])['Qty Sold'].sum().reset_index()

    # Pivot the data to get separate columns for each month's quantity sold
    pivot_result = result.pivot(index='Product Name', columns='Month', values='Qty Sold').reset_index()

    # Filter the data to only include rows where:
    # current month sales > last month sales AND last month sales > third last month sales
    pivot_result = pivot_result[
        (pivot_result[current_month] > pivot_result[last_month]) 
    ]

    pivot_result['Growth'] = (pivot_result[current_month] - pivot_result[last_month])/pivot_result[last_month]*100

    pivot_result['Growth'] = pivot_result['Growth'].apply(lambda x: f"{x:,.0f}%")

    # Format the columns to show as readable numbers with commas
    pivot_result[last_month] = pivot_result[last_month].apply(lambda x: f"{x:,}")
    pivot_result[current_month] = pivot_result[current_month].apply(lambda x: f"{x:,}")
    

    # Adjust column ordering: If third month exists, include it

    pivot_result = pivot_result[['Product Name', last_month, current_month, 'Growth']]

    # Reset index and start counting from 1
    pivot_result.reset_index(drop=True, inplace=True)
    pivot_result.index += 1  # Start numbering from 1

    # Display the result in Streamlit
    
    st.table(pivot_result)  # Display the DataFrame as a table




# PRODUCTS THAT COSTS $0-20, AND HAS POSITIVE GROWTH IN THE LAST 3 MONTHS


    st.markdown(
    "<h1 style='color:green; font-size: 16px; font-weight: bold; font-style: italic;'>$0-20 <span style='color:grey;'>Products with <span style='color:green;'>Positive Growth<span style='color:blue;'> in the last 3 months</h1>", 
    unsafe_allow_html=True
    )
    

    # Prepare the data (using the function)
    df, third_last_month, last_month, current_month, last_three_months = prepare_data(df)

    # Filter products sold in the last two or three months
    products_sold_last_months = df[df['Month'].isin(last_three_months)]

    # Find common products sold across the selected months (intersection of product names)
    if third_last_month:
        # If three months are available, find products sold in all three months
        common_products = set(products_sold_last_months[products_sold_last_months['Month'] == current_month]['Product Name']).intersection(
            set(products_sold_last_months[products_sold_last_months['Month'] == last_month]['Product Name']),
            set(products_sold_last_months[products_sold_last_months['Month'] == third_last_month]['Product Name'])
        )
    else:
        # If fewer than three months are available, find products sold in just the last two months
        common_products = set(products_sold_last_months[products_sold_last_months['Month'] == current_month]['Product Name']).intersection(
            set(products_sold_last_months[products_sold_last_months['Month'] == last_month]['Product Name'])
        )

    # Filter the DataFrame for these common products
    common_products_df = products_sold_last_months[products_sold_last_months['Product Name'].isin(common_products)]

    # Filter for Price_cat $0-20 only
    common_products_df = common_products_df[common_products_df['Price_cat'] == '$0-20']

    # Group by Product Name, Price_cat, and Month, and sum the quantities sold
    result = common_products_df.groupby(['Product Name', 'Price_cat', 'Month'])['Qty Sold'].sum().reset_index()

    # Pivot the data to get separate columns for each month's quantity sold
    pivot_result = result.pivot(index='Product Name', columns='Month', values='Qty Sold').reset_index()

    # Calculate growth between the current month and third last month
    if third_last_month in pivot_result.columns:
        pivot_result['Growth'] = ((pivot_result[current_month] - pivot_result[third_last_month]) / pivot_result[third_last_month]) * 100

    # Filter for rows with positive growth
    pivot_result = pivot_result[pivot_result['Growth'] > 0]

    # Format the columns for better readability
    pivot_result[last_month] = pivot_result[last_month].apply(lambda x: f"{x:,}")
    pivot_result[current_month] = pivot_result[current_month].apply(lambda x: f"{x:,}")
    pivot_result['Growth'] = pivot_result['Growth'].apply(lambda x: f"{x:,.0f}%")

    # Format the third last month if data is available
    if third_last_month in pivot_result.columns:
        pivot_result[third_last_month] = pivot_result[third_last_month].apply(lambda x: f"{x:,}")
        pivot_result = pivot_result[['Product Name', third_last_month, last_month, current_month, 'Growth']]
    else:
        pivot_result = pivot_result[['Product Name', last_month, current_month, 'Growth']]

    # Reset index and start numbering from 1
    pivot_result.reset_index(drop=True, inplace=True)
    pivot_result.index += 1  # Start numbering from 1

    # Display the result as a table in Streamlit
    st.table(pivot_result)  # Display the DataFrame as a table



# PRODUCTS THAT COSTS $0-20, AND HAS NEGATIVE GROWTH IN THE LAST 3 MONTHS


    st.markdown(
    "<h1 style='color:green; font-size: 16px; font-weight: bold; font-style: italic;'>$0-20 <span style='color:grey;'>Products with <span style='color:green;'>Negative Growth</span> in the last 3 months <span style='color:red;'>(zero to -ve)</h1>", 
    unsafe_allow_html=True
    )
    # Prepare the data (using the function)
    df, third_last_month, last_month, current_month, last_three_months = prepare_data(df)

    # Filter products sold in the last two or three months
    products_sold_last_months = df[df['Month'].isin(last_three_months)]

    # Find common products sold across the selected months (intersection of product names)
    if third_last_month:
        # If three months are available, find products sold in all three months
        common_products = set(products_sold_last_months[products_sold_last_months['Month'] == current_month]['Product Name']).intersection(
            set(products_sold_last_months[products_sold_last_months['Month'] == last_month]['Product Name']),
            set(products_sold_last_months[products_sold_last_months['Month'] == third_last_month]['Product Name'])
        )
    else:
        # If fewer than three months are available, find products sold in just the last two months
        common_products = set(products_sold_last_months[products_sold_last_months['Month'] == current_month]['Product Name']).intersection(
            set(products_sold_last_months[products_sold_last_months['Month'] == last_month]['Product Name'])
        )

    # Filter the DataFrame for these common products
    common_products_df = products_sold_last_months[products_sold_last_months['Product Name'].isin(common_products)]

    # Filter for Price_cat $0-20 only
    common_products_df = common_products_df[common_products_df['Price_cat'] == '$0-20']

    # Group by Product Name, Price_cat, and Month, and sum the quantities sold
    result = common_products_df.groupby(['Product Name', 'Price_cat', 'Month'])['Qty Sold'].sum().reset_index()

    # Pivot the data to get separate columns for each month's quantity sold
    pivot_result = result.pivot(index='Product Name', columns='Month', values='Qty Sold').reset_index()

    # Calculate growth between the current month and third last month
    if third_last_month in pivot_result.columns:
        pivot_result['Growth'] = ((pivot_result[current_month] - pivot_result[third_last_month]) / pivot_result[third_last_month]) * 100

    # Filter for rows with positive growth
    pivot_result = pivot_result[pivot_result['Growth'] <= 0]

    # Format the columns for better readability
    pivot_result[last_month] = pivot_result[last_month].apply(lambda x: f"{x:,}")
    pivot_result[current_month] = pivot_result[current_month].apply(lambda x: f"{x:,}")
    pivot_result['Growth'] = pivot_result['Growth'].apply(lambda x: f"{x:,.0f}%")

    # Format the third last month if data is available
    if third_last_month in pivot_result.columns:
        pivot_result[third_last_month] = pivot_result[third_last_month].apply(lambda x: f"{x:,}")
        pivot_result = pivot_result[['Product Name', third_last_month, last_month, current_month, 'Growth']]
    else:
        pivot_result = pivot_result[['Product Name', last_month, current_month, 'Growth']]

    # Reset index and start numbering from 1
    pivot_result.reset_index(drop=True, inplace=True)
    pivot_result.index += 1  # Start numbering from 1

    # Display the result as a table in Streamlit
    st.table(pivot_result)  # Display the DataFrame as a table




# $0-20 PRODUCTS WITH MONTH ON MONTH GROWTH (3 MONTHS)

    st.markdown(
    "<h1 style='color:green; font-size: 16px; font-weight: bold; font-style: italic;'>$0-20 <span style='color:grey;'> Products with <span style='color:green;'>Month-on-Month growth <span style='color:blue;'>in the last 3 months</h1>", 
    unsafe_allow_html=True
    )
    

    # Prepare the data (using the function)
    df, third_last_month, last_month, current_month, last_three_months = prepare_data(df)

    # Filter products sold in the last three months
    products_sold_last_months = df[df['Month'].isin(last_three_months)]

    # Find common products sold across all three months (if available)
    common_products = set(products_sold_last_months[products_sold_last_months['Month'] == current_month]['Product Name']).intersection(
        set(products_sold_last_months[products_sold_last_months['Month'] == last_month]['Product Name']),
        set(products_sold_last_months[products_sold_last_months['Month'] == third_last_month]['Product Name'])
    )

    # Filter the DataFrame for these common products
    common_products_df = products_sold_last_months[products_sold_last_months['Product Name'].isin(common_products)]
    # Filter for Price_cat $0-20 only
    common_products_df = common_products_df[common_products_df['Price_cat'] == '$0-20']
    

    # Group by Product Name and Month, and sum the quantities sold
    result = common_products_df.groupby(['Product Name', 'Month'])['Qty Sold'].sum().reset_index()

    # Pivot the data to get separate columns for each month's quantity sold
    pivot_result = result.pivot(index='Product Name', columns='Month', values='Qty Sold').reset_index()

    # Filter the data to only include rows where:
    # current month sales > last month sales AND last month sales > third last month sales
    pivot_result = pivot_result[
        (pivot_result[current_month] > pivot_result[last_month]) &
        (pivot_result[last_month] > pivot_result[third_last_month])
    ]

    # Adjust column ordering: 

    pivot_result = pivot_result[['Product Name', third_last_month, last_month, current_month]]
   

    # Format the columns to show as readable numbers with commas
    pivot_result[last_month] = pivot_result[last_month].apply(lambda x: f"{x:,}")
    pivot_result[current_month] = pivot_result[current_month].apply(lambda x: f"{x:,}")
    pivot_result[third_last_month] = pivot_result[third_last_month].apply(lambda x: f"{x:,}")

    # Reset index and start counting from 1
    pivot_result.reset_index(drop=True, inplace=True)
    pivot_result.index += 1  # Start numbering from 1

    # Display the result in Streamlit
    
    st.table(pivot_result)  # Display the DataFrame as a table








