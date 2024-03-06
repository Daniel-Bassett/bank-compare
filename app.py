import pandas as pd
import plotly_express as px
import streamlit as st
from streamlit_option_menu import option_menu
from st_files_connection import FilesConnection

# Create connection object and retrieve file contents.
# Specify input format is a csv and to cache the result for 600 seconds.
conn = st.connection('gcs', type=FilesConnection)
branches_df = conn.read("crispybacon-bucket/bank-compare/branches.csv", input_format="csv", ttl=600)
reviews_df = conn.read("crispybacon-bucket/bank-compare/reviews.csv", input_format="csv", ttl=600)

@st.cache_data
def load_data(filepath):
    return pd.read_csv(filepath)


# branches_df = load_data('processed_data/branches.csv')
# reviews_df = load_data('processed_data/reviews.csv')
merged_df = pd.merge(reviews_df, branches_df, left_on='branch_id', right_on='branch_id')[['branch_id', 'stars', 'review_x', 'bank', 'address', 'metro', 'year']]
merged_df = merged_df.rename(columns={'review_x': 'reviews'})


# create sidebar menu with options
selected = option_menu(
    menu_title=None,
    menu_icon='cast',
    default_index=0,
    options=['Overall', 'Branch Report'],
    orientation='horizontal',
    icons=['bank', 'clipboard-data'],
    styles= {'container': {
                'font-size': '12px'
    }}
)

if selected == 'Overall':
    metro_options = ['All'] + sorted(list(merged_df['metro'].unique()))
    metro = st.selectbox('Choose Metro', options=metro_options, index=0)

    # bar chart
    if metro != 'All':
        ratings_compare = merged_df.query(f'metro == "{metro}"').groupby(['bank'])['stars'].mean().sort_values(ascending=False)
    else:
        ratings_compare = merged_df.groupby('bank')['stars'].mean().sort_values(ascending=False)
    fig = px.bar(
        data_frame=ratings_compare,
        title=f'Average Ratings - {metro}'
    )
    fig.update_layout(
        yaxis_title="stars", 
        yaxis=dict(range=[0, 5]),
        title_x=0.4,
        showlegend=False,
        dragmode=False
        )
    st.plotly_chart(fig, use_container_width=True)


    # pie chart
    if metro == 'All':
        n_branches = branches_df.groupby('bank', as_index=False).size().sort_values(by='bank')
    else:
        metro_filter = branches_df['metro'] == metro
        n_branches = branches_df[metro_filter].groupby('bank', as_index=False).size().sort_values(by='bank')

    n_branches = n_branches.rename(columns={'size': 'n_branches'})
    
    fig = px.pie(n_branches, values='n_branches', names='bank', title=f'Market Share - {metro}')
    fig.update_layout(
        title_x=0.4,
        dragmode=False,
        # margin=dict(t=50, b=50, l=200, r=50)
        )
    st.plotly_chart(fig, use_container_width=True)




if selected == 'Branch Report':

    merged_df = pd.merge(reviews_df, branches_df, left_on='branch_id', right_on='branch_id')
    branches_filtered = branches_df.copy()

    # bank filter
    bank_options = branches_filtered['bank'].unique()
    bank = st.selectbox('Choose Bank', options=bank_options)
    bank_filter = branches_filtered['bank'] == bank
    branches_filtered = branches_filtered[bank_filter]

    # address filter
    address_options = sorted(list(branches_filtered['address'].unique()))
    address = st.selectbox('Choose Address', options=address_options)
    address_filter = branches_filtered['address'] == address
    branches_filtered = branches_filtered[address_filter]

    # write report
    if len(branches_filtered) == 1:
        id_filter = reviews_df['branch_id'] == branches_filtered.branch_id.values[0]

        branch_ratings = merged_df[id_filter][['stars', 'year']]
        branch_ratings = branch_ratings.groupby('year')['stars'].mean()
        
        fig = px.line(
            data_frame=branch_ratings, title='Average Rating'
        )
        fig.update_layout(
            yaxis_title="stars", 
            yaxis=dict(range=[0, 5]),
            title_x=0.4,
            showlegend=True,
            dragmode=False
            )
        st.plotly_chart(fig, use_container_width=True)

        st.write(branches_filtered['analysis'].values[0])

        with st.expander('See Reviews...'):
            for index, row in reviews_df[id_filter].dropna().iterrows():
                st.write(row['review'])