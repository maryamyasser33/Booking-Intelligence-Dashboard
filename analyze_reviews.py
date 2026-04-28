import google.generativeai as genai
import json

# 1. Configure the API
# For local testing, you can paste it directly here.
API_KEY = "AIzaSyC2EW_3f1D3TRpcOHNtY2Xms9s05WpdDOY" 
genai.configure(api_key=API_KEY)

# 2. Configure the Model
# We use Gemini 1.5 Flash as it is the fastest and cheapest for bulk text processing tasks.
# We explicitly tell it to return structured JSON data, which is crucial for saving to a database.
model = genai.GenerativeModel(
    'gemini-1.5-flash',
    generation_config={
        "response_mime_type": "application/json",
    }
)

def analyze_review_sentiment(review_text):
    """Sends a single review to Gemini and returns structured JSON analysis."""
    
    prompt = f"""
    You are an expert hospitality data analyst. Analyze the following hotel guest review.
    Extract the sentiment, the primary topic being discussed, and a brief 1-sentence summary of the core issue or praise.
    
    Output strictly in the following JSON format:
    {{
        "sentiment": "Positive" | "Negative" | "Mixed" | "Neutral",
        "primary_topic": "Cleanliness" | "Location" | "Staff" | "Value" | "Amenities" | "Noise" | "Other",
        "summary": "One sentence summary of the review"
    }}

    Review: "{review_text}"
    """
    
    try:
        response = model.generate_content(prompt)
        # Parse the JSON string returned by Gemini into a Python dictionary
        result = json.loads(response.text)
        return result
    except Exception as e:
        print(f"Error processing review: {e}")
        return None

# 3. Test the AI Pipeline with Sample Data
if __name__ == "__main__":
    print("Initializing Gemini AI Analysis...\n")
    
    # Sample reviews simulating what we will eventually scrape from Booking.com
    sample_reviews = [
        "The room was absolutely filthy. There was hair in the bathroom sink and the bedsheets smelled like smoke. Never coming back.",
        "Perfect location right next to the pyramids! The staff was incredibly helpful with booking our tours, though the wifi was a bit slow.",
        "It was okay. Just a standard room to sleep in. Nothing special, but not terrible either for the price."
    ]
    
    for i, review in enumerate(sample_reviews, 1):
        print(f"--- Analyzing Review {i} ---")
        print(f"Raw Text: {review}")
        
        analysis = analyze_review_sentiment(review)
        
        if analysis:
            print(f"Sentiment:     {analysis.get('sentiment')}")
            print(f"Primary Topic: {analysis.get('primary_topic')}")
            print(f"AI Summary:    {analysis.get('summary')}\n")