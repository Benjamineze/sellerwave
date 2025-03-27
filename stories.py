import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
#import missingno as msno
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
    "<h1 style='color:#7D4E57; font-size: 24px; font-style: italic;'>Sales Analysis</h1>", 
    unsafe_allow_html=True)

    st.markdown(
    "<h1 style='color:#BD7E58; font-size: 20px; font-weight: bold; font-style: italic;'> All Beauty & personal care products sold at $0-20</h1>", 
    unsafe_allow_html=True)


    # FILTER BEAUTY & CARE PRODUCTS, $0-20 PRICE CAT

    
    # Filter products from 'Beauty & Personal Care' category
    care_product_df = df[df['Product Category'] == 'Beauty & Personal Care']

    # Further filter products with price category $0-20
    care_product_df = care_product_df[care_product_df['Price_cat'] == '$0-20']

    # Retain only the first price per product (assuming price remains the same)
    price_mapping = care_product_df.groupby("Product Name")["Price"].first().reset_index()
    
    # Group by Product Name and Price Category, summing the quantities sold
    result = care_product_df.groupby(['Product Name', 'Price_cat'])['Qty Sold'].sum().reset_index()

    
    # Merge the price information
    result = result.merge(price_mapping, on="Product Name", how="left")


    # Select only relevant columns and reset index
    result = result[['Product Name', "Price", 'Qty Sold']].sort_values(by='Qty Sold', ascending=False)
    result.reset_index(drop=True, inplace=True)
    result.index += 1  # Start numbering from 1

    result["Qty Sold"] = result["Qty Sold"].apply(lambda x: f"{x:,}")
    result["Price"] = result["Price"].apply(lambda x: f"{x:,.2f}")
  
   # Reorder columns for better readability
    result = result[['Product Name', 'Price', 'Qty Sold']]
    
    # Display in Streamlit
    st.dataframe(result)
   



    # ALL $0-20 PRODUCTS WITH 3 MONTHS CONSECUTIVE SALES

    st.markdown(
    "<h1 style='color:#BD7E58; font-size: 18px; font-weight: bold; font-style: italic;'>All <span style='color:#7D4E57;'>$0-20 <span style='color:#BD7E58;'>Products with </span> <span style='color:#7D4E57;'> 3 Months  </span><span style='color:#BD7E58;'>Consecutive sales</h1>", 
    unsafe_allow_html=True)



    
    # Prepare the data (using the function)
    df, third_last_month, last_month, current_month, last_three_months = prepare_data(df)

    # Check if 3 months are available
    if len(last_three_months) >= 3:
        

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

                                                
        # Group by Product Name, Price_cat, and Month, and sum the quantities sold
        result = common_products_df.groupby(['Product Name', 'Price_cat', 'Month'])['Qty Sold'].sum().reset_index()

        # Pivot the data to get separate columns for each month's quantity sold
        pivot_result = result.pivot(index='Product Name', columns='Month', values='Qty Sold').reset_index()

        # Calculate growth between the current month and third last month
        
        pivot_result['Growth'] = ((pivot_result[current_month] - pivot_result[third_last_month]) / pivot_result[third_last_month]) * 100

        # Filter for rows with positive growth
        #pivot_result = pivot_result[pivot_result['Growth'] > 0]

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

        pivot_result.columns = pivot_result.columns.str.strip()
        pivot_result.columns = pivot_result.columns.str.encode('ascii', 'ignore').str.decode('utf-8')

        # Display the result as a table in Streamlit
        st.table(pivot_result)  # Display the DataFrame as a table
        

    
    else:
        st.write("<h1 style='color:grey; font-size: 16px; font-weight: bold; font-style: italic;'>.....No sufficient data at the moment.</h1>", 
        unsafe_allow_html=True)
        


    # ALL $0-20 PRODUCTS WITH 2 MONTHS CONSECUTIVE SALES

    st.markdown(
    "<h1 style='color:#BD7E58; font-size: 18px; font-weight: bold; font-style: italic;'>All <span style='color:#7D4E57;'>$0-20 <span style='color:#BD7E58;'>Products with </span> <span style='color:#7D4E57;'> 2 Months  </span><span style='color:#BD7E58;'>Consecutive sales</h1>", 
    unsafe_allow_html=True
    
    )


    # Prepare the data (using the function)
    df, third_last_month, last_month, current_month, last_three_months = prepare_data(df)

    # Filter products sold in the last two months
    products_sold_last_months = df[df['Month'].isin(last_three_months)]

    # Find common products sold across the selected months (intersection of product names)
    if last_month:
        # If 2 months are available, find products sold in both months
        common_products = set(products_sold_last_months[products_sold_last_months['Month'] == current_month]['Product Name']).intersection(
            set(products_sold_last_months[products_sold_last_months['Month'] == last_month]['Product Name'])
        )

        # Filter the DataFrame for these common products
        common_products_df = products_sold_last_months[products_sold_last_months['Product Name'].isin(common_products)]
        
        # Filter for Price_cat $0-20 only
        common_products_df = common_products_df[common_products_df['Price_cat'] == '$0-20']

        # Retain only the first price per product (assuming price remains the same)
        price_mapping = common_products_df.groupby("Product Name")["Price"].first().reset_index()

        # Group by Product Name, Price_cat, and Month, summing the quantities sold
        result = common_products_df.groupby(['Product Name', 'Price_cat', 'Month'])['Qty Sold'].sum().reset_index()

        # Pivot the data to get separate columns for each month's quantity sold
        pivot_result = result.pivot(index='Product Name', columns='Month', values='Qty Sold').reset_index()

        # Merge the price information
        pivot_result = pivot_result.merge(price_mapping, on="Product Name", how="left")

        # Calculate growth between the current month and last month
        pivot_result['Growth'] = ((pivot_result[current_month] - pivot_result[last_month]) / pivot_result[last_month]) * 100

        # Format the columns for better readability
        pivot_result[last_month] = pivot_result[last_month].apply(lambda x: f"{x:,}")
        pivot_result[current_month] = pivot_result[current_month].apply(lambda x: f"{x:,}")
        pivot_result['Growth'] = pivot_result['Growth'].apply(lambda x: f"{x:,.0f}%")
        pivot_result["Price"] = pivot_result["Price"].apply(lambda x: f"{x:,.2f}")

        # Reorder columns for better readability
        pivot_result = pivot_result[['Product Name', 'Price', last_month, current_month, 'Growth']]
        
        # Reset index and start numbering from 1
        pivot_result.reset_index(drop=True, inplace=True)
        pivot_result.index += 1  # Start numbering from 1

        # Display the result as a table in Streamlit
        #st.table(pivot_result)

        st.table(pivot_result.style.set_properties(**{'white-space': 'nowrap'}))

        
    else:
        st.markdown(
            "<h1 style='color:#4A4A48; font-size: 16px; font-weight: bold; font-style: italic;'>Sorry... last 2 months data not available at the moment...</h1>", 
            unsafe_allow_html=True
        )





    # GROWTH ANALYSIS

    st.markdown(
    "<h1 style='color:#7D4E57; font-size: 24px; font-style: italic;'>Growth Analysis</h1>", 
    unsafe_allow_html=True)



    # $0-20 PRODUCTS WITH MONTH-ON-MONTH GROWTH IN THE LAST 3 MONTHS

    st.markdown(
    "<h1 style='color:grey; font-size: 16px; font-weight: bold; font-style: italic;'>All Products with <span style='color:green;'>Month-on-Month growth <span style='color:blue;'>in the last 3 months</h1>", 
    unsafe_allow_html=True
    )
    

    # Prepare the data (using the function)
    df, third_last_month, last_month, current_month, last_three_months = prepare_data(df)

    
    # Ensure we have at least three months of data
    if len(last_three_months) < 3:
        
        # Filter products sold in the last three months
        products_sold_last_months = df[df['Month'].isin(last_three_months)]
        
        # Find common products sold across all three months
        common_products = set(products_sold_last_months[products_sold_last_months['Month'] == current_month]['Product Name'])
        common_products &= set(products_sold_last_months[products_sold_last_months['Month'] == last_month]['Product Name'])
        common_products &= set(products_sold_last_months[products_sold_last_months['Month'] == third_last_month]['Product Name'])
        
        # Filter the DataFrame for these common products
        common_products_df = products_sold_last_months[products_sold_last_months['Product Name'].isin(common_products)]
        
        # Group by Product Name and Month, summing the quantities sold
        result = common_products_df.groupby(['Product Name', 'Month'])['Qty Sold'].sum().reset_index()
        
        # Pivot the data to get separate columns for each month's quantity sold
        pivot_result = result.pivot(index='Product Name', columns='Month', values='Qty Sold').reset_index()
        
        # Ensure all required months exist in the pivot table
        for col in [third_last_month, last_month, current_month]:
            if col not in pivot_result:
                pivot_result[col] = 0  # Fill missing months with zero sales
        
        # Calculate growth percentage
        pivot_result['Growth'] = ((pivot_result[current_month] - pivot_result[third_last_month]) 
                                / pivot_result[third_last_month]) * 100
        
        # Filter rows where sales increase over the three months
        pivot_result = pivot_result[
            (pivot_result[current_month] > pivot_result[last_month]) &
            (pivot_result[last_month] > pivot_result[third_last_month])
        ]
        
        # Adjust column ordering
        pivot_result = pivot_result[['Product Name', third_last_month, last_month, current_month, 'Growth']]
        
        # Format columns as readable numbers with commas
        pivot_result[last_month] = pivot_result[last_month].apply(lambda x: f"{x:,}")
        pivot_result[current_month] = pivot_result[current_month].apply(lambda x: f"{x:,}")
        pivot_result[third_last_month] = pivot_result[third_last_month].apply(lambda x: f"{x:,}")
        pivot_result['Growth'] = pivot_result['Growth'].apply(lambda x: f"{x:,.0f}%")
        
        # Reset index and start numbering from 1
        pivot_result.reset_index(drop=True, inplace=True)
        pivot_result.index += 1  # Start numbering from 1
        
        # Display the result in Streamlit
        st.table(pivot_result)

    else:
         st.write("<h1 style='color:#BD7E58; font-size: 20px; font-weight: bold; font-style: italic;'>sorry.....Not enough data to calculate this growth.</h1>", 
        unsafe_allow_html=True)
        


    # $0-20 PRODUCTS WITH MONTH-ON-MONTH GROWTH IN THE LAST 2 MONTHS

    st.markdown(
    "<h1 style='color:#4A4A48; font-size: 16px; font-weight: bold; font-style: italic;'>$0-20 <span style='color:grey;'>Products with <span style='color:green;'>Month-on-Month Growth <span style='color:blue;'>in the last 2 months</h1>", 
    unsafe_allow_html=True
    )

    # Prepare the data (using the function)
    df, third_last_month, last_month, current_month, last_three_months = prepare_data(df)

    # Filter products sold in the last two or three months
    products_sold_last_months = df[df['Month'].isin(last_three_months)]

    # Find common products sold across the selected months (intersection of product names)
    if last_month:
        # If three months are available, find products sold in all three months
        common_products = set(products_sold_last_months[products_sold_last_months['Month'] == current_month]['Product Name']).intersection(
            set(products_sold_last_months[products_sold_last_months['Month'] == last_month]['Product Name']),
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

        # Calculate growth only if enough data is available
        if last_month in pivot_result.columns:
            # Calculate growth between the current month and last month
            pivot_result['Growth'] = (pivot_result[current_month] - pivot_result[last_month])/pivot_result[last_month]*100


        pivot_result = pivot_result[['Product Name', last_month, current_month,'Growth' ]]
   

        # Format the columns to show as readable numbers with commas
        pivot_result[last_month] = pivot_result[last_month].apply(lambda x: f"{x:,}")
        pivot_result[current_month] = pivot_result[current_month].apply(lambda x: f"{x:,}")
        pivot_result['Growth'] = pivot_result['Growth'].apply(lambda x: f"{x:,.0f}%")
        

        # Reset index and start counting from 1
        pivot_result.reset_index(drop=True, inplace=True)
        pivot_result.index += 1  # Start numbering from 1

        # Display the result in Streamlit
        st.table(pivot_result)
    else:
        st.write("<h1 style='color:#BD7E58; font-size: 20px; font-weight: bold; font-style: italic;'>sorry.....Not enough data to calculate this growth.</h1>", 
        unsafe_allow_html=True)
        



    # LAST VS THIRD LAST MONTH'S GROWTH.
    st.markdown(
    "<h1 style='color:#4A4A48; font-size: 16px; font-weight: bold; font-style: italic;'>$0-20 <span style='color:grey;'>Products with <span style='color:green;'> Growth <span style='color:blue;'>Last vs 3rd Last Month</h1>", 
    unsafe_allow_html=True
    )

    # If three months are available, add growth between the third last month and the last month
    if third_last_month:
        pivot_result['Growth (Last vs 3rd Last)'] = pivot_result[last_month] - pivot_result[third_last_month]

        # Format growth values to show as percentages and other values with commas
        pivot_result = pivot_result[pivot_result['Growth'] > 0]
        pivot_result[last_month] = pivot_result[last_month].apply(lambda x: f"{x:,}")
        pivot_result[current_month] = pivot_result[current_month].apply(lambda x: f"{x:,}")
        pivot_result['Growth'] = pivot_result['Growth'].apply(lambda x: f"{x:,.0f}%")
        

        # If third month data is available, format it
        if third_last_month:
            pivot_result[third_last_month] = pivot_result[third_last_month].apply(lambda x: f"{x:,}")
            pivot_result['Growth (Last vs 3rd Last)'] = pivot_result['Growth (Last vs 3rd Last)'].apply(lambda x: f"{x:,}")

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

    else:
        st.write("<h1 style='color:#BD7E58; font-size: 20px; font-weight: bold; font-style: italic;'>.....Not enough data to calculate Last Vs 3rd last Month's growth.</h1>", 
        unsafe_allow_html=True)


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
        pivot_result = pivot_result[pivot_result['Growth'] < 0]

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
    else:
        st.write("<h1 style='color:#BD7E58; font-size: 20px; font-weight: bold; font-style: italic;'>.....Not enough data to calculate Last Vs 3rd last Month's growth.</h1>", 
        unsafe_allow_html=True)




