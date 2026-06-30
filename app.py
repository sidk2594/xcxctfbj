import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- Page Config ---
st.set_page_config(page_title="FinTech Pipeline Analytics", layout="wide", page_icon="📈")

# --- Data Ingestion & Engineering ---
@st.cache_data
def load_data():
    df = pd.read_excel('p2p_lending_dataset.xlsx')
    # Feature Engineering
    df['Loan_to_Income_Ratio'] = df['Loan_Amount_Requested'] / df['Annual_Income']
    bins = [17, 25, 35, 45, 55, 65, 120]
    labels = ['18-25', '26-35', '36-45', '46-55', '56-65', '65+']
    df['Age_Group'] = pd.cut(df['Applicant_Age'], bins=bins, labels=labels)
    
    # Bucketing Credit Scores
    score_bins = [0, 580, 670, 740, 800, 850]
    score_labels = ['Poor', 'Fair', 'Good', 'Very Good', 'Exceptional']
    df['Credit_Tier'] = pd.cut(df['Credit_Score_Estimate'], bins=score_bins, labels=score_labels)
    return df

try:
    df = load_data()
except Exception as e:
    st.error("Dataset not found. Please run the data generation cell first.")
    st.stop()

# --- Sidebar Navigation ---
st.sidebar.title("🛠 Navigation")
module = st.sidebar.radio("Go to:", ["📊 Executive Overview", "🔄 Pipeline Analysis", "👥 Risk Demographics"])

st.sidebar.divider()
st.sidebar.subheader("Filters")
channels = st.sidebar.multiselect("Acquisition Channels", options=df['Acquisition_Channel'].unique(), default=df['Acquisition_Channel'].unique())

# Filter Data
mask = df['Acquisition_Channel'].isin(channels)
df_filtered = df[mask]

# --- Modules ---
if module == "📊 Executive Overview":
    st.title("📊 Executive Pipeline Overview")
    
    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    total_leads = len(df_filtered)
    funded_leads = len(df_filtered[df_filtered['Lead_Status'] == 'Funded'])
    conv_rate = (funded_leads / total_leads * 100) if total_leads > 0 else 0
    avg_time = df_filtered['Conversion_Time_Days'].mean()
    
    c1.metric("Total Leads", f"{total_leads:,}")
    c2.metric("Funded Leads", f"{funded_leads:,}")
    c3.metric("Pipeline Conversion", f"{conv_rate:.1f}%")
    c4.metric("Avg Conversion Time", f"{avg_time:.1f} Days")

    st.divider()
    
    # Funnel Chart
    st.subheader("Lead Status Funnel")
    funnel_data = df_filtered['Lead_Status'].value_counts().reindex(['New', 'Contacted', 'Application Started', 'Approved', 'Funded', 'Rejected']).reset_index()
    fig_funnel = px.funnel(funnel_data, x='count', y='Lead_Status', title="Conversion Drop-off")
    st.plotly_chart(fig_funnel, use_container_width=True)

elif module == "🔄 Pipeline Analysis":
    st.title("🔄 Flow Analysis")
    
    # Sankey Diagram Logic
    st.subheader("Acquisition to Status Flow")
    all_nodes = list(df_filtered['Acquisition_Channel'].unique()) + list(df_filtered['Lead_Status'].unique())
    nodes_map = {name: i for i, name in enumerate(all_nodes)}
    
    links = df_filtered.groupby(['Acquisition_Channel', 'Lead_Status']).size().reset_index(name='value')
    links['source'] = links['Acquisition_Channel'].map(nodes_map)
    links['target'] = links['Lead_Status'].map(nodes_map)
    
    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5), label=all_nodes),
        link=dict(source=links['source'], target=links['target'], value=links['value'])
    )])
    st.plotly_chart(fig_sankey, use_container_width=True)

elif module == "👥 Risk Demographics":
    st.title("👥 Risk & Demographics")
    
    # Treemap
    st.subheader("Lead Volume by Tier and Age")
    fig_tree = px.treemap(df_filtered, path=['Credit_Tier', 'Age_Group'], 
                          values='Loan_Amount_Requested', 
                          color='Loan_to_Income_Ratio', 
                          color_continuous_scale='RdYlGn_r')
    st.plotly_chart(fig_tree, use_container_width=True)

# --- Insights ---
st.divider()
with st.container():
    st.subheader("💡 Key Insights")
    best_channel = df_filtered[df_filtered['Lead_Status'] == 'Funded']['Acquisition_Channel'].value_counts().idxmax()
    highest_risk = df_filtered.groupby('Age_Group')['Loan_to_Income_Ratio'].mean().idxmax()
    
    st.markdown(f"""
    * **Top Channel:** The `{best_channel}` channel currently drives the highest volume of funded loans.
    * **Risk Alert:** The `{highest_risk}` age bracket shows the highest average Loan-to-Income ratio.
    * **Efficiency:** Current average conversion velocity is `{df_filtered['Conversion_Time_Days'].mean():.1f}` days.
    """)
