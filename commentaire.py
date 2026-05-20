import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
VIDEO_ID = "ClF55GE7zPI"
URL = "https://www.googleapis.com/youtube/v3/commentThreads"

def get_comments(video_id, api_key, max_results=50):
    comments = []
    page_token = None

    while True:
        params = {
            "part": "snippet",
            "videoId": video_id,
            "key": api_key,
            "maxResults": max_results,
            "pageToken": page_token
        }
        
        response = requests.get(URL, params=params)
        data = response.json()

        for item in data.get("items", []):
            comment = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "author": comment["authorDisplayName"],
                "text": comment["textDisplay"],
                "likeCount": comment["likeCount"],
                "publishedAt": comment["publishedAt"]
            })

        # Pagination
        page_token = data.get("nextPageToken")
        if not page_token:
            break

    return comments

# Exemple d’utilisation
comments = get_comments(VIDEO_ID, API_KEY)
print(f"Nombre de commentaires récupérés : {len(comments)}")
print(comments[:5])  # affiche les 5 premiers
