import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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
import textwrap


#Load credentials from TOML file
credentials_info = st.secrets["GOOGLE_CREDENTIAL_FOR_AMAZON"]

credentials = service_account.Credentials.from_service_account_info(credentials_info)

# Initialize BigQuery Client with  credentials
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








def show_Amazon_dashboard(df):
    # Streamlit app layout

    

    # Display the dataframe to verify the data
    st.write("Data Sample:", df.head())

    # to visualize total rows
    num_rows = len(df)
    st.write(f"Row Total: {num_rows}")
 
#INDIVIDUAL DISTRIBUTION OF PRODUCT CATEGORY

    # Calculate counts and percentages
    total_count = len(df)
    counts = df['Product Category'].value_counts()
    percentages = counts / total_count * 100

    # Create the plot
    plt.figure(figsize=(8, 5))
    ax = sns.countplot(x='Product Category', data=df, order=counts.index, color='skyblue')
    plt.xlabel('Product Category', labelpad=20)
    plt.ylabel("Number of Products")
    plt.title('Individual Distribution of Product Categories', pad=15)
    wrapped_labels = [textwrap.fill(label, width=10) for label in df['Product Category'].unique()]
    ax.set_xticklabels(wrapped_labels, rotation=0)  # Keep them horizontal

    # Adjusting space above the highest bar
    plt.ylim(0, max(counts) * 1.2)

    # Add number and percentage labels to the bars
    for p in ax.patches:
        count = int(p.get_height())
        percentage = count / total_count * 100
        count_label = f'{count:,}'  # Format count with commas
        percentage_label = f'{percentage:.1f}%'
        # Annotate percentage above the bar
        ax.annotate(percentage_label, (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='bottom', xytext=(2, 16), textcoords='offset points', weight='bold', fontsize=10)
        # Annotate count directly under the percentage label
        ax.annotate(count_label, (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='bottom', xytext=(2, 1), textcoords='offset points', fontsize=8.5)

    # Display plot in Streamlit app
    st.pyplot(plt)



#TOTAL QUANTITY SOLD BY PRODUCT CATEGORY

    # Calculate total quantity sold by category and percentages
    category_sales = df.groupby('Product Category')['Qty Sold'].sum().reset_index()
    total_qty_sold = category_sales['Qty Sold'].sum()
    category_sales['Percentage'] = (category_sales['Qty Sold'] / total_qty_sold) * 100
    
    

    category_sales = category_sales.sort_values(by='Qty Sold', ascending=False)

    # Create the plot
    plt.figure(figsize=(8, 5))
    ax = sns.barplot(x='Product Category', y='Qty Sold', data=category_sales, palette='viridis', hue='Product Category', dodge=False)

    plt.xlabel("Product Category", labelpad=20, )
    plt.ylabel("Total Quantity Sold")
    plt.title("Total Quantity Sold by Product Category", pad=15)
    # Wrap the text labels
    wrapped_labels = [textwrap.fill(label, width=10) for label in category_sales['Product Category'].unique()]
    ax.set_xticklabels(wrapped_labels, rotation=0)  # Keep them horizontal
    # Adding more space above the highest bar for better readability
    plt.ylim(0, max(category_sales['Qty Sold']) * 1.2)

    # Add number and percentage labels to the bars
    for p in ax.patches:
        count = int(p.get_height())
        # Find the corresponding percentage
        percentage = category_sales.loc[category_sales['Qty Sold'] == count, 'Percentage'].values[0]
        count_label = f'{count:,}'  # Format count with commas
        percentage_label = f'{percentage:.1f}%'
        
        
        # Annotate percentage below the total quantity sold label
        ax.annotate(percentage_label, (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='bottom', 
                    xytext=(0, 15), textcoords='offset points', color='green', weight="bold")

        # Annotate total quantity sold above the bar
        ax.annotate(count_label, (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='bottom', 
                    xytext=(0, 0), textcoords='offset points', fontsize=8.5)


    # Show plot
    st.pyplot(plt)





# TOP 10 PRODUCT BY QUANTITY SOLD
    
    # Group by product and sum the quantity sold for each product
    product_sales = df.groupby('Product Name')['Qty Sold'].sum().reset_index()

    # Sort the products by quantity sold in descending order and get the top 10
    top_10_products = product_sales.sort_values(by='Qty Sold', ascending=False).head(10)

    # Wrap long product names for better readability
    top_10_products['Product Name'] = top_10_products['Product Name'].apply(lambda x: '\n'.join(textwrap.wrap(x, 60)))

    # Set the plot size
    plt.figure(figsize=(7, 8))

    # Create a horizontal bar plot using the top 10 products data
    ax = sns.barplot(x='Qty Sold', y='Product Name', data=top_10_products, color='skyblue', dodge=False)

    # Add title and labels
    plt.title('Top 10 Products by Quantity Sold', fontsize=12, pad=15)
    plt.xlabel('Quantity Sold', fontsize=12, labelpad=20)
    plt.ylabel('Product Name', fontsize=12)

    # Annotate the bars with the count inside the bar
    for p in ax.patches:
        width = p.get_width()  # The width of the bar (Qty Sold)
        ax.annotate(f'{int(width):,}',  # Formatting the count with commas
                    (width - width * 0.02, p.get_y() + p.get_height() / 2),  # Position slightly inside the bar
                    ha='right', va='center', color='white', fontsize=10, weight='bold')  # Adjust label position and style
        
    # Reduce the font size of y-axis (product names)
    ax.tick_params(axis='y', labelsize=8)

    # Increase left margin to avoid cutting off long product names
    plt.subplots_adjust(left=0.4)

    # Customize font to avoid missing glyph issues
    plt.rcParams['font.family'] = 'DejaVu Sans'

    # Display the plot
    st.pyplot(plt)





    # Calculate total quantity sold by category and percentages

    category_sales = df.groupby('Rating_cat')['Qty Sold'].sum().reset_index()
    total_qty_sold = category_sales['Qty Sold'].sum()
    category_sales['Percentage'] = (category_sales['Qty Sold'] / total_qty_sold) * 100

    # Create the plot
    plt.figure(figsize=(9, 6))
    ax = sns.barplot(x='Rating_cat', y='Qty Sold', data=category_sales, palette='viridis', hue='Rating_cat', dodge=False)

    plt.xlabel("Rating Category", labelpad=20)
    plt.ylabel("Total Quantity Sold")
    plt.title("Total Quantity Sold by Rating Category", pad=15)

    # Adding more space above the highest bar for better readability
    plt.ylim(0, max(category_sales['Qty Sold']) * 1.2)

    # Add number and percentage labels to the bars
    for p in ax.patches:
        count = int(p.get_height())
        # Find the corresponding percentage
        percentage = category_sales.loc[category_sales['Qty Sold'] == count, 'Percentage'].values[0]
        count_label = f'{count:,}'  # Format count with commas
        percentage_label = f'{percentage:.1f}%'
        
        
        # Annotate percentage below the total quantity sold label
        ax.annotate(percentage_label, (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='bottom', 
                    xytext=(0, 15), textcoords='offset points', color='green', weight="bold")

        # Annotate total quantity sold above the bar
        ax.annotate(count_label, (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='bottom', 
                    xytext=(0, 0), textcoords='offset points', fontsize=8.5)


    # Show plot
    st.pyplot(plt)


    # Calculate total quantity sold by category and percentages
    category_sales = df.groupby('Price_cat')['Qty Sold'].sum().reset_index()
    total_qty_sold = category_sales['Qty Sold'].sum()
    category_sales['Percentage'] = (category_sales['Qty Sold'] / total_qty_sold) * 100

    # Sort the category sales DataFrame in descending order of Qty Sold
    category_sales = category_sales.sort_values(by='Qty Sold', ascending=False)


    # Create the plot
    plt.figure(figsize=(9, 6))
    ax = sns.barplot(x='Price_cat', y='Qty Sold', data=category_sales, palette='viridis', hue='Price_cat', dodge=False)


    plt.xlabel("Price Category", labelpad=20)
    plt.ylabel("Total Quantity Sold")
    plt.title("Total Quantity Sold by Price Category", pad=15)

    # Adding more space above the highest bar for better readability
    plt.ylim(0, max(category_sales['Qty Sold']) * 1.2)

    # Add number and percentage labels to the bars
    for p in ax.patches:
        count = int(p.get_height())
        # Find the corresponding percentage
        percentage = category_sales.loc[category_sales['Qty Sold'] == count, 'Percentage'].values[0]
        count_label = f'{count:,}'  # Format count with commas
        percentage_label = f'{percentage:.1f}%'
        
        
        # Annotate percentage below the total quantity sold label
        ax.annotate(percentage_label, (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='bottom', 
                    xytext=(0, 15), textcoords='offset points', color='green', weight="bold")

        # Annotate total quantity sold above the bar
        ax.annotate(count_label, (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='bottom', 
                    xytext=(0, 0), textcoords='offset points', fontsize=8.5)


    # Show plot
    st.pyplot(plt)


    # TOP 10 POTENTIAL HIGH SALE PRODUCTS
    st.markdown(
    "<h1 style='color:grey; font-size: 17px; font-weight: bold; font-style: italic;'>Top 10 </span><span style='color:green;'>Potential High sale products</h1>", 
    unsafe_allow_html=True
    )

    def calculate_moving_average(product_df, window=3):
        """Calculate the moving average of sales for each product."""
        product_df['Moving_Avg'] = product_df['Qty Sold'].rolling(window=window).mean()
        return product_df

    def detect_high_sales(product_df, threshold=1.1):
        """Detect products with potential high sales."""
        product_df = calculate_moving_average(product_df)
        latest_sales = product_df['Qty Sold'].iloc[-1]
        latest_moving_avg = product_df['Moving_Avg'].iloc[-1]
        return latest_sales > threshold * latest_moving_avg

    def find_high_sales_products(data):
        """Find products with potential high sales."""
        high_sales_products = []
        product_groups = data.groupby('Product Name')
    
        for product, product_df in product_groups:
            if len(product_df) >= 3:  # Ensure enough data points for moving average
                product_df = product_df.sort_values(by='coll_date')
                if detect_high_sales(product_df):
                    high_sales_products.append(product)
                
        return high_sales_products

    def plot_top_10_high_sales_products(data, high_sales_products):
         #Display top 10 products with potential high sales in Streamlit.
        high_sales_data = data[data['Product Name'].isin(high_sales_products)]
        high_sales_qty = high_sales_data.groupby('Product Name')['Qty Sold'].sum().reset_index()
        top_10_high_sales = high_sales_qty.nlargest(10, 'Qty Sold')
    
        fig, ax = plt.subplots(figsize=(7, 8))

        # Wrap long product names for better readability
        top_10_high_sales['Product Name'] = top_10_high_sales['Product Name'].apply(lambda x: '\n'.join(textwrap.wrap(x, 60)))
        sns.barplot(x='Qty Sold', y='Product Name', data=top_10_high_sales, ax=ax, color='#0c424e')
        ax.set_title("Top 10 Products with Potential High Sales")
        ax.set_xlabel("Total Quantity Sold")
        ax.set_ylabel("Product Name")
        plt.xticks(rotation=45, ha='right')
    
        # Annotate each bar with quantity sold
        for p in ax.patches:
            width = p.get_width()
            ax.annotate(f'{int(width):,}', (width - width * 0.02, p.get_y() + p.get_height() / 2),
                        ha='right', va='center', color='white', fontsize=10, weight='bold')
        
        ax.tick_params(axis='y', labelsize=8)

        st.pyplot(fig)

    # Main execution
    high_sales_products = find_high_sales_products(df)

    # Plot and display the top 10 high-sales products
    if high_sales_products:
        st.write("### Top 10 Potential High Sales Products")
        plot_top_10_high_sales_products(df, high_sales_products)
    else:
        st.write("No products with high sales potential detected.")


#PRODUCTS WITH POSITIVE MONTH ON MONTH GROWTH (3 MONTHS)


    st.markdown(
    "<h1 style='color:grey; font-size: 17px; font-weight: bold; font-style: italic;'>Products with </span><span style='color:blue;'>Month-on-Month growth (3 Months)</h1>", 
    unsafe_allow_html=True
    )

    # Prepare the data
    df, third_last_month, last_month, current_month, last_three_months = prepare_data(df)

     # If only 1 month exists, display a message and return
    if third_last_month is None and last_month == current_month:
        st.write("Not enough data to calculate growth.")
        return

    # Filter products sold in the last three months
    products_sold_last_months = df[df['Month'].isin(last_three_months)]

    # Find common products sold across all three months
    common_products = set(products_sold_last_months[products_sold_last_months['Month'] == current_month]['Product Name']).intersection(
        set(products_sold_last_months[products_sold_last_months['Month'] == last_month]['Product Name']),
        set(products_sold_last_months[products_sold_last_months['Month'] == third_last_month]['Product Name'])
    )

    # Filter DataFrame for these common products
    common_products_df = products_sold_last_months[products_sold_last_months['Product Name'].isin(common_products)]

    # Group by Product Name and Month, and sum the quantities sold
    result = common_products_df.groupby(['Product Name', 'Month'])['Qty Sold'].sum().reset_index()

    # Pivot the data to get separate columns for each month's quantity sold
    pivot_result = result.pivot(index='Product Name', columns='Month', values='Qty Sold').reset_index()

    # Calculate growth only if enough data is available
    if third_last_month in pivot_result.columns:
        # Filter the data for positive growth in each of the last three months
        pivot_result = pivot_result[
        (pivot_result[current_month] > pivot_result[last_month]) &
        (pivot_result[last_month] > pivot_result[third_last_month])
        ]
    


        # Prepare data for the plot
        plot_data = result[result['Product Name'].isin(pivot_result['Product Name'])]

        # Sort the category sales DataFrame in descending order of Qty Sold
        plot_data = plot_data.sort_values(by='Qty Sold', ascending=True)


        plot_data['Product Name'] =plot_data['Product Name'].apply(lambda x: '\n'.join(textwrap.wrap(x, 60)))


        # Plotting the month-on-month growth
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.barplot(data=plot_data, x='Qty Sold', y='Product Name', hue='Month', ax=ax)
        ax.set_title("Month-on-Month Positive Growth (3months)", pad=15)
        ax.set_xlabel("Month", labelpad=20)
        ax.set_ylabel("Total Quantity Sold")
        plt.xticks(rotation=45)
        plt.tight_layout()
        # Rotate x-axis labels for better readability and adjust size
        plt.xticks(rotation=45, ha="right", fontsize=12)


        # Adding more space above the highest bar for better readability
        max_value = plot_data['Qty Sold'].max()  # Find the maximum value in the data
        plt.xlim(0, max_value * 1.2)  # Adjust x-axis limit to add extra space above the highest bar

        # Annotate bars with values (the quantity sold)
        for p in ax.patches:
            width = p.get_width()
            if width < 0:  # Avoid negative values if present
                width = 0
            
            # Adjust annotation position: Ensure it stays inside the bars
            ax.annotate(f'{int(width):,}', 
                        (width + 5, p.get_y() + p.get_height() / 2),  # Position slightly inside the bar
                        ha='left', va='center', color='black', fontsize=10)

        # Adjust y-axis labels' font size
        ax.tick_params(axis='y', labelsize=12)
        # Display the plot in Streamlit
        st.pyplot(fig)
    else:
        st.write("<h1 style='color:#BD7E58; font-size: 20px; font-weight: bold; font-style: italic;'>ooopss.....Not enough data to calculate growth.</h1>", 
        unsafe_allow_html=True)
        



    #CURRENT VS LAST MONTH GROWTH (2 MONTH)
    
    st.markdown(
    "<h1 style='color:grey; font-size: 17px; font-weight: bold; font-style: italic;'>Products with </span><span style='color:blue;'>Month-on-Month growth (2 Months)</h1>", 
    unsafe_allow_html=True
    )
        
    # Prepare the data (using the function)
    df, third_last_month, last_month, current_month, last_three_months = prepare_data(df)

        # If only 1 month exists, display a message and return
    if third_last_month is None and last_month == current_month:
            st.write("Not enough data to calculate growth.")
            return


        # Filter products sold in the last three months
    products_sold_last_months = df[df['Month'].isin(last_three_months)]

     # Find common products sold across all three months (if available)
    common_products = set(products_sold_last_months[products_sold_last_months['Month'] == current_month]['Product Name']).intersection(
            set(products_sold_last_months[products_sold_last_months['Month'] == last_month]['Product Name']) 
        )

    # Filter the DataFrame for these common products
    common_products_df = products_sold_last_months[products_sold_last_months['Product Name'].isin(common_products)]

    # Group by Product Name and Month, and sum the quantities sold
    result = common_products_df.groupby(['Product Name', 'Month'])['Qty Sold'].sum().reset_index()

    # Pivot the data to get separate columns for each month's quantity sold
    pivot_result = result.pivot(index='Product Name', columns='Month', values='Qty Sold').reset_index()


        
    # Filter the data to only include rows where:
    # current month sales > last month sales 
    pivot_result = pivot_result[
            (pivot_result[current_month] > pivot_result[last_month]) 
        ]
        
        
        
    pivot_result = result.pivot(index='Product Name', columns='Month', values='Qty Sold').reset_index()

    # Filter for positive growth
    pivot_result = pivot_result[pivot_result[current_month] > pivot_result[last_month]]

    # Melt the pivot result to long format for plotting
    melted_data = pivot_result.melt(id_vars=["Product Name"], value_vars=[last_month, current_month],
                                        var_name="Month", value_name="Qty Sold")
        
        


    # Plotting
    fig, ax = plt.subplots(figsize=(14, 12))  
        

    # Wrap long product names for readability
    melted_data['Product Name'] = melted_data['Product Name'].apply(lambda x: '\n'.join(textwrap.wrap(x, 60)))

    # Create a bar plot with the melted data, differentiated by month (using hue)
    sns.barplot(x="Qty Sold", y="Product Name", hue="Month", data=melted_data, ax=ax, palette="muted")

    # Adding more space above the highest bar for better readability
    max_value = melted_data['Qty Sold'].max()  # Find the maximum value in the data
    plt.xlim(0, max_value * 1.2)  # Adjust x-axis limit to add extra space above the highest bar

    # Annotate bars with values (the quantity sold)
    for p in ax.patches:
            width = p.get_width()
            if width < 0:  # Avoid negative values if present
                width = 0
            
            # Adjust annotation position: Ensure it stays inside the bars
            ax.annotate(f'{int(width):,}', 
                        (width + 5, p.get_y() + p.get_height() / 2),  # Position slightly inside the bar
                        ha='left', va='center', color='black', fontsize=12)

    # Set titles and labels with larger font size
    ax.set_title("+ve GROWTH for Current vs Last Month (2 Months)", fontsize=16,  pad=15)
    ax.set_xlabel("Quantity Sold", fontsize=14)
    ax.set_ylabel("Product Name", fontsize=14)


    
    # Rotate x-axis labels for better readability and adjust size
    plt.xticks(rotation=45, ha="right", fontsize=12)

    # Adjust y-axis labels' font size
    ax.tick_params(axis='y', labelsize=12)

    # Adjust layout to prevent clipping of labels
    plt.tight_layout()

    # Display the plot in the Streamlit app
    st.pyplot(fig)








        
