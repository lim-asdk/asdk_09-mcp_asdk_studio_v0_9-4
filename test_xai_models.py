import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("XAI_API_KEY")

url = "https://api.x.ai/v1/models"
headers = {
    "Authorization": f"Bearer {api_key}"
}

try:
    response = requests.get(url, headers=headers)
    with open("xai_models.json", "w") as f:
        json.dump(response.json(), f, indent=2)
    print("Models saved to xai_models.json")
except Exception as e:
    print(f"Error: {e}")
