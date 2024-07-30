import streamlit as st
import pandas as pd
import gzip

# Function to read and preprocess the data
def load_data():
    def read_csv_gzip(file_path):
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            return pd.read_csv(f, sep='|')
    
    df2023 = read_csv_gzip('STIP_Survey.csv.gz')
    df2017 = read_csv_gzip('STIP_Survey-2017.csv.gz')
    df2019 = read_csv_gzip('STIP_Survey-2019.csv.gz')
    df2021 = read_csv_gzip('STIP_Survey-2021.csv.gz')
    
    for df in [df2023, df2017, df2019, df2021]:
        df['InitiativeID_numeric'] = df['InitiativeID'].apply(lambda url: url.split('/')[-1])
    
    df2023['year_source'] = 2023
    df2017['year_source'] = 2017
    df2019['year_source'] = 2019
    df2021['year_source'] = 2021
    
    df_combined = pd.concat([df2023, df2017, df2019, df2021])
    return df_combined

# Function to filter data based on user's choice
def filter_data(df_combined, option):
    if option == 'Gather unique policy initiatives':
        df_combined = df_combined.sort_values('year_source', ascending=False).drop_duplicates('InitiativeID_numeric')
    elif option == 'Gather policy initiatives with multiple instruments':
        df_combined = df_combined.sort_values(by='year_source', ascending=False)
        is_2023 = df_combined['year_source'] == 2023
        df_combined = df_combined[is_2023 | ~df_combined.duplicated(subset='InitiativeID_numeric', keep='first')]
    
    df_combined['status'] = df_combined['year_source'].apply(lambda x: 'ongoing' if x == 2023 else 'past')
    df_combined.reset_index(drop=True, inplace=True)
    return df_combined

# Function to add keyword presence columns
def add_keyword_columns(df, keyword):
    df['Keyword_appears_Title'] = df['NameEnglish'].str.contains(keyword, case=False, na=False)
    df['Keyword_appears_ShortDescription'] = df['ShortDescription'].str.contains(keyword, case=False, na=False)
    df['Keyword_appears_Background'] = df['Background'].str.contains(keyword, case=False, na=False)
    objectives_cols = ['Objectives1', 'Objectives2', 'Objectives3', 'Objectives4', 'Objectives5', 'Objectives6']
    df['Keyword_appears_Objectives'] = df[objectives_cols].apply(lambda row: row.str.contains(keyword, case=False, na=False).any(), axis=1)
    return df

# Load data
df_combined = load_data()

# Streamlit app
st.title("STIP Survey Data Filter")
st.write("Filter policy initiatives based on unique initiatives or multiple instruments, and search by keyword.")

# User input for filtering option
option = st.selectbox("Choose an option", ["Gather unique policy initiatives", "Gather policy initiatives with multiple instruments"])

# User input for keyword
keyword = st.text_input("Enter the keyword to filter policies", "").strip().lower()

if st.button("Filter Data"):
    if keyword:
        df_combined = filter_data(df_combined, option)
        df_combined = add_keyword_columns(df_combined, keyword)
        filtered_df = df_combined[
            df_combined['Keyword_appears_Title'] |
            df_combined['Keyword_appears_ShortDescription'] |
            df_combined['Keyword_appears_Background'] |
            df_combined['Keyword_appears_Objectives']
        ]
        
        columns_to_move = ['InitiativeID_numeric', 'year_source', 'status', 'Keyword_appears_Title', 'Keyword_appears_ShortDescription', 'Keyword_appears_Objectives', 'Keyword_appears_Background']
        remaining_columns = [col for col in filtered_df.columns if col not in columns_to_move]
        new_column_order = columns_to_move + remaining_columns
        filtered_df = filtered_df[new_column_order]
        
        st.write(f"Filtered dataframe for keyword '{keyword}' created successfully!")
        st.dataframe(filtered_df)
        
        csv = filtered_df.to_csv(index=False, sep='|', encoding='utf-8')
        st.download_button(label="Download CSV", data=csv, file_name=f'STIP_Survey_filtered_{keyword}.csv', mime='text/csv')

        excel = filtered_df.to_excel(index=False)
        st.download_button(label="Download Excel", data=excel, file_name=f'STIP_Survey_filtered_{keyword}.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        st.error("Please enter a keyword to filter policies.")
