import google.generativeai as genai
import pandas as pd
import json
import time

# 1. Configure Gemini API
API_KEY = "AIzaSyC2EW_3f1D3TRpcOHNtY2Xms9s05WpdDOY" # <--- PASTE YOUR KEY HERE
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel(
    'gemini-2.5-flash',
    generation_config={"response_mime_type": "application/json"}
)

def analyze_review(review_text):
    # We explicitly tell the AI to ignore metadata in the prompt
    prompt = f"""
    You are an expert hospitality data analyst. Analyze this hotel guest review text. 
    Ignore any metadata like guest names, countries, dates, or room types. Focus only on the guest's actual experience.
    
    Extract the sentiment, the primary topic, and a brief 1-sentence summary.
    
    Output strictly in this JSON format:
    {{
        "sentiment": "Positive" | "Negative" | "Mixed" | "Neutral",
        "primary_topic": "Cleanliness" | "Location" | "Staff" | "Value" | "Amenities" | "Noise" | "Other",
        "summary": "One sentence summary of the review"
    }}

    Review: "{review_text}"
    """
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"API Error: {e}")
        return None

if __name__ == "__main__":
    print("Loading raw reviews...")
    try:
        df = pd.read_csv("hotel_raw_reviews.csv")
    except FileNotFoundError:
        print("Error: Could not find hotel_raw_reviews.csv")
        exit()

    analyzed_data = []
    
    print(f"Found {len(df)} reviews to process. Sending to Gemini AI...")

    for index, row in df.iterrows():
        print(f"Processing review {index + 1}/{len(df)}...")
        
        # Send text to AI
        analysis = analyze_review(row['Review Text'])
        
        if analysis:
            # Combine the original data with the AI's insights
            analyzed_data.append({
                "Hotel URL": row['Hotel URL'],
                "Original Text": row['Review Text'],
                "Sentiment": analysis.get('sentiment', 'Unknown'),
                "Topic": analysis.get('primary_topic', 'Unknown'),
                "AI Summary": analysis.get('summary', 'No summary generated')
            })
            
        # Add a 2-second delay to avoid hitting free-tier API rate limits
        time.sleep(2) 

    # Save the final, structured dataset
    if analyzed_data:
        final_df = pd.DataFrame(analyzed_data)
        final_df.to_csv("hotel_analyzed_reviews.csv", index=False, encoding='utf-8')
        print("\nSUCCESS! All reviews analyzed.")
        print(final_df[['Sentiment', 'Topic']].head())
    else:
        print("\nFailed to process reviews.")