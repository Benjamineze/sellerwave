import streamlit as st
from stories import show_stories
from Amazon_dashboard import show_Amazon_dashboard
from Decision import show_Decision
import numpy as np
from google.cloud import bigquery
from rich.text import Text
import textwrap
import os
import toml
from google.oauth2 import service_account
from google.auth import default




credentials_info = st.secrets["GOOGLE_CREDENTIAL_FOR_AMAZON"]

credentials = service_account.Credentials.from_service_account_info(credentials_info)

# Initialize BigQuery Client with correct credentials
client = bigquery.Client(credentials=credentials, project=credentials.project_id)



# Define  SQL query to load data
query = """
SELECT *
FROM `amaz-project-438116.Existing_data.Sales` 
LIMIT 1000  
"""

# Load data into a DataFrame
df = client.query(query).to_dataframe()



# Add the custom bar

st.markdown(
    "<h1 style='color:grey; font-size: 24px; font-weight: bold; font-style: italic;'>Welcome to <span style='color:#BD7E58; font-size: 32px; font-weight: bold; font-style: italic;'>SellerWave</h1>", 
    unsafe_allow_html=True
)


page = st.selectbox('', ('Decision', 'Dashboard', 'Explore'))




if page == 'Dashboard':
    show_Amazon_dashboard(df)
elif page == 'Decision':
    show_Decision(df)
else:
    show_stories(df)
    


