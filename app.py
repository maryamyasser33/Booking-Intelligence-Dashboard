import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

# 1. Page Configuration
st.set_page_config(page_title="Booking Intelligence", layout="wide")

st.title("Booking.com Web Intelligence Platform")
st.markdown("Actionable market intelligence powered by Web Scraping and Generative AI.")

# 2. Load the Data
@st.cache_data 
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
    
    selected_hotel = st.sidebar.selectbox(
        "Select Competitor Hotel:", 
        options=["All Hotels"] + list(hotels_df['Hotel Name'].dropna().unique())
    )

    if selected_hotel != "All Hotels":
        display_hotels = hotels_df[hotels_df['Hotel Name'] == selected_hotel].copy()
        
        if not display_hotels.empty:
            hotel_url = display_hotels['Property URL'].values[0]
            display_reviews = reviews_df[reviews_df['Hotel URL'] == hotel_url]
        else:
            display_reviews = pd.DataFrame()
    else:
        display_hotels = hotels_df.copy()
        display_reviews = reviews_df

    # --- DASHBOARD TABS ---
    tab1, tab2, tab3, tab4 = st.tabs(["Market Overview", "AI Sentiment Analysis", "Raw Data Browser", "Structured Database"])

    # TAB 1: Market Overview 
    with tab1:
        st.subheader("Competitor Benchmarking")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Competitors Tracked", len(display_hotels))
        col2.metric("Total AI Analyzed Reviews", len(display_reviews))
        
        try:
            display_hotels['Numeric_Price'] = display_hotels['Price'].astype(str).str.extract(r'(\d+[,.]\d+|\d+)')[0].str.replace(',', '').astype(float)
            valid_prices = display_hotels['Numeric_Price'].dropna()
            if not valid_prices.empty:
                avg_price = f"EGP {valid_prices.mean():,.2f}"
            else:
                avg_price = "N/A"
        except Exception as e:
            avg_price = "N/A"
            
        col3.metric("Average Market Price", avg_price)
        st.dataframe(display_hotels[['Hotel Name', 'Price', 'Review Score']], use_container_width=True)

    # TAB 2: AI Sentiment Analysis
    with tab2:
        st.subheader("Guest Sentiment & Service Gaps")
        
        if not display_reviews.empty:
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
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

            st.markdown("### AI-Generated Review Summaries")
            for index, row in display_reviews.iterrows():
                sentiment_tag = f"[{row['Sentiment']}]"
                st.info(f"**{sentiment_tag} {row['Topic']}**: {row['AI Summary']}")
        else:
            st.info("No AI analyzed reviews available for this specific selection.")

    # TAB 3: Data Browser
    with tab3:
        st.subheader("Raw Extracted Data")
        st.markdown("The raw unstructured text converted into a semi-structured JSON/CSV format by the LLM.")
        st.dataframe(display_reviews, use_container_width=True)

    # TAB 4: Structured Database
    with tab4:
        st.subheader("Relational Database Backend (SQLite)")
        st.markdown("This tab connects directly to the `hotel_intelligence.db` file to demonstrate the physical data model and structured schema.")
        
        try:
            conn = sqlite3.connect('hotel_intelligence.db')
            
            col_db1, col_db2 = st.columns(2)
            
            with col_db1:
                st.markdown("##### 'Hotels' Table")
                hotels_sql_df = pd.read_sql_query("SELECT * FROM Hotels", conn)
                st.dataframe(hotels_sql_df, use_container_width=True)
                
            with col_db2:
                st.markdown("##### 'PriceSnapshots' Table")
                prices_sql_df = pd.read_sql_query("SELECT * FROM PriceSnapshots", conn)
                st.dataframe(prices_sql_df, use_container_width=True)

            st.markdown("##### Joined Relational View")
            st.markdown("`SELECT h.name, h.review_score, p.price, p.scrape_date FROM Hotels h JOIN PriceSnapshots p ON h.id = p.hotel_id`")
            
            joined_query = """
            SELECT h.name as Hotel_Name, h.review_score as Score, p.price as Price, p.scrape_date as Date
            FROM Hotels h
            JOIN PriceSnapshots p ON h.id = p.hotel_id
            """
            joined_sql_df = pd.read_sql_query(joined_query, conn)
            st.dataframe(joined_sql_df, use_container_width=True)

            conn.close()
            
        except Exception as e:
            st.error(f"Could not load database: {e}")
            st.info("Make sure 'hotel_intelligence.db' is in the same folder as this script.")