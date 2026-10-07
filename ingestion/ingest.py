import json
import os
from datetime import datetime, timezone

import boto3
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["OPENWEATHER_API_KEY"]
API_URL = "https://api.openweathermap.org/data/2.5/weather"
BUCKET = "weather-bronze"
CITIES = ["Sao Paulo", "New York", "Tokyo", "Belo Horizonte", "Macapá", "Santiago", "Brasilia"]

s3 = boto3.client(
    "s3", 
    endpoint_url="http://localhost:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1",    
)

def fetch_weather_data(city: str) -> dict:
    response = requests.get(
        API_URL,
        params={"q": city, "appid": API_KEY, "units": "metric"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()

def main() -> None:
    now = datetime.now(timezone.utc)
    for city in CITIES:
        data = fetch_weather_data(city)
        slug = city.lower().replace(" ", "_")
        key = f"openweathermap/date={now:%Y-%m-%d}/{slug}_{now:%H%M%S}.json"
        s3.put_object(Bucket=BUCKET, Key=key, Body=json.dumps(data).encode("utf-8"))
        print(f"saved s3://{BUCKET}/{key}")

if __name__ == "__main__":
    main()