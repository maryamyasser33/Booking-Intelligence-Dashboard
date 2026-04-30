import pandas as pd
import sqlite3
import re

# 1. Load the raw data from your crawler
print("Loading raw CSV...")
df = pd.read_csv('booking_cairo_data.csv')

# 2. Clean the 'Price' column (e.g., converts "EGP 2,500" -> 2500.0)
def clean_price(price_str):
    if pd.isna(price_str) or price_str == "N/A":
        return None
    # Regex to extract only digits from the string
    numbers = re.findall(r'\d+', str(price_str).replace(',', ''))
    if numbers:
        return float(numbers[0])
    return None

df['Clean_Price'] = df['Price'].apply(clean_price)

# 3. Clean the 'Review Score' column (e.g., extracts 8.5 from "Scored 8.5")
def clean_score(score_str):
    if pd.isna(score_str) or score_str == "N/A":
        return None
    # Regex to extract numbers with a decimal point
    match = re.search(r'\d+\.\d+', str(score_str))
    if match:
        return float(match.group())
    # Fallback for whole numbers
    numbers = re.findall(r'\d+', str(score_str))
    if numbers:
        return float(numbers[0])
    return None

df['Clean_Score'] = df['Review Score'].apply(clean_score)

print("\nData cleaned! Preview:")
print(df[['Hotel Name', 'Clean_Price', 'Clean_Score']].head())

# 4. Database Architecture Setup
print("\nSetting up database architecture...")
conn = sqlite3.connect('hotel_intelligence.db')
cursor = conn.cursor()

# Create structured tables matching our conceptual entities
cursor.execute('''
CREATE TABLE IF NOT EXISTS Hotels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    review_score REAL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS PriceSnapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hotel_id INTEGER,
    price REAL,
    scrape_date DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (hotel_id) REFERENCES Hotels (id)
)
''')

# 5. Insert the cleaned data into the relational tables
for index, row in df.iterrows():
    if pd.isna(row['Hotel Name']) or row['Hotel Name'] == "N/A":
        continue
        
    # Insert hotel (IGNORE if it already exists to avoid duplicates on future scrapes)
    cursor.execute('''
    INSERT OR IGNORE INTO Hotels (name, review_score) VALUES (?, ?)
    ''', (row['Hotel Name'], row['Clean_Score']))
    
    # Retrieve the assigned hotel_id
    cursor.execute('SELECT id FROM Hotels WHERE name = ?', (row['Hotel Name'],))
    hotel_id = cursor.fetchone()[0]
    
    # Insert the daily price snapshot
    if pd.notna(row['Clean_Price']):
        cursor.execute('''
        INSERT INTO PriceSnapshots (hotel_id, price) VALUES (?, ?)
        ''', (hotel_id, row['Clean_Price']))

conn.commit()
conn.close()

print("\nSuccess! Cleaned data has been mapped and saved to hotel_intelligence.db")