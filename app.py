import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="Booking Intelligence", page_icon="🏨", layout="wide")

st.title("🏨 Booking.com Web Intelligence Platform")
st.markdown("Actionable market intelligence powered by Web Scraping and Generative AI.")

# 2. Load the Data
@st.cache_data # This keeps the app fast by caching the data
def load_data():
    try:
        hotels_df = pd.read_csv("booking_cairo_data_with_urls.csv")
        reviews_df = pd.read_csv("hotel_analyzed_reviews.csv")
        return hotels_df, reviews_df
    except FileNotFoundError:
        st.error("Data files not found. Ensure your CSVs are in the same folder as this script.")
        return pd.DataFrame(), pd.DataFrame()

hotels_df, reviews_df = load_data()

if not hotels_df.empty and not reviews_df.empty:
    
    # --- SIDEBAR: Filters ---
    st.sidebar.header("Market Filters")
    
    # Create a clean list of hotels that actually have reviews scraped
    hotels_with_reviews = reviews_df['Hotel URL'].unique()
    
    # Filter the main dataframe to only show these specific hotels to keep the demo clean
    filtered_hotels_df = hotels_df[hotels_df['Property URL'].isin(hotels_with_reviews)]
    
    selected_hotel = st.sidebar.selectbox(
        "Select Competitor Hotel:", 
        options=["All Hotels"] + list(filtered_hotels_df['Hotel Name'].unique())
    )

    # Apply the filter based on user selection
    if selected_hotel != "All Hotels":
        # Find the URL for the selected hotel
        hotel_url = filtered_hotels_df[filtered_hotels_df['Hotel Name'] == selected_hotel]['Property URL'].values[0]
        display_reviews = reviews_df[reviews_df['Hotel URL'] == hotel_url]
    else:
        display_reviews = reviews_df

    # --- DASHBOARD TABS ---
    tab1, tab2, tab3 = st.tabs(["📊 Market Overview", "🧠 AI Sentiment Analysis", "🗄️ Raw Data Browser"])

    # TAB 1: Market Overview (Pricing & Scores)
    with tab1:
        st.subheader("Competitor Benchmarking")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Competitors Tracked", len(filtered_hotels_df))
        col2.metric("Total AI Analyzed Reviews", len(display_reviews))
        
        # Clean the price column for charting (assuming it looks like "EGP 5,000")
        try:
            filtered_hotels_df['Numeric_Price'] = filtered_hotels_df['Price'].str.extract(r'(\d+[,.]\d+|\d+)')[0].str.replace(',', '').astype(float)
            avg_price = f"EGP {filtered_hotels_df['Numeric_Price'].mean():.2f}"
        except:
            avg_price = "N/A"
            
        col3.metric("Average Market Price", avg_price)

        st.dataframe(filtered_hotels_df[['Hotel Name', 'Price', 'Review Score']], use_container_width=True)

    # TAB 2: AI Sentiment Analysis
    with tab2:
        st.subheader("Guest Sentiment & Service Gaps")
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Pie Chart: Overall Sentiment
            sentiment_counts = display_reviews['Sentiment'].value_counts().reset_index()
            sentiment_counts.columns = ['Sentiment', 'Count']
            
            fig_pie = px.pie(
                sentiment_counts, 
                names='Sentiment', 
                values='Count', 
                title="Overall Guest Sentiment",
                color='Sentiment',
                color_discrete_map={
                    'Positive': '#2ecc71',
                    'Negative': '#e74c3c',
                    'Mixed': '#f1c40f',
                    'Neutral': '#95a5a6'
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_chart2:
            # Bar Chart: Topics Discussed
            topic_counts = display_reviews['Topic'].value_counts().reset_index()
            topic_counts.columns = ['Topic', 'Count']
            
            fig_bar = px.bar(
                topic_counts, 
                x='Topic', 
                y='Count', 
                title="Primary Topics Discussed (Service Gaps)",
                color='Topic'
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # Show the AI Summaries below the charts
        st.markdown("### 🤖 AI-Generated Review Summaries")
        for index, row in display_reviews.iterrows():
            emoji = "🟢" if row['Sentiment'] == 'Positive' else "🔴" if row['Sentiment'] == 'Negative' else "🟡"
            st.info(f"{emoji} **{row['Topic']}**: {row['AI Summary']}")

    # TAB 3: Data Browser
    with tab3:
        st.subheader("Raw Extracted Data")
        st.markdown("The raw unstructured text converted into a structured database.")
        st.dataframe(display_reviews, use_container_width=True)