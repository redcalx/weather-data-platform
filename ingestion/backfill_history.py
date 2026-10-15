import argparse
import csv
import json
import os
import time
from datetime import date, datetime, timedelta

import boto3
import requests
from botocore.exceptions import ClientError

API_URL = "https://archive-api.open-meteo.com/v1/archive"
BUCKET = "weather-bronze"
START_YEAR = 1991
DAILY = ",".join([
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "apparent_temperature_mean",
])
CITIES_FILE = os.path.join(os.path.dirname(__file__), "cities.csv")

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name="us-east-1",
)

def already_saved(key: str) -> bool:
    try:
        s3.head_object(Bucket=BUCKET, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
            return False
        raise

# Defines a set of HTTP status codes that are considered retryable for API requests
RETRYABLE_STATUS = {500, 502, 503, 504}

def fetch_year(lat: float, lon: float, year: int, end_date: date) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date(year, 1, 1).isoformat(),
        "end_date": min(date(year, 12, 31), end_date).isoformat(),
        "daily": DAILY,
        "timezone": "auto",
    }
    for attempt in range(1, 6):
        wait = 20 * attempt
        try:
            response = requests.get(API_URL, params=params, timeout=(10, 60))
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as error:
            print(f"network problem ({type(error).__name__}), waiting {wait}s (attempt {attempt}/5)")
            time.sleep(wait)
            continue
        
        # Error handling for HTTP 429 Too Many Requests
        if response.status_code == 429:
            reason = response.text[:200]
            print(f"HTTP 429: {reason}")
            
            if "minutely" in reason.lower():
                time.sleep(65)
                continue
            
            if "hourly" in reason.lower():
                now = datetime.now()
                next_hour = (now + timedelta(hours=1)).replace(
                    minute=1, second=0, microsecond=0
                )
                wait = (next_hour - now).total_seconds()
                print(f"Hourly limit exceeded: sleeping until {next_hour:%H:%M} ({wait / 60:.0f} min)")
                time.sleep(wait)
                continue
            
            if "daily" in reason.lower():
                raise RuntimeError(
                    "Daily API limit reached. Run the script again later; "
                    "it resumes where it stopped."
                )

            raise RuntimeError(f"HTTP 429 rate limit; limit type unclear: {reason}")
            
        if response.status_code in RETRYABLE_STATUS:
            print(f"HTTP {response.status_code}, waiting {wait}s (attempt {attempt}/5)")
            time.sleep(wait)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError("giving up after 5 attempts, run the script again later")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uf", help="only this state (e.g. SP, RJ, MG)")
    args = parser.parse_args()
    
    end_date = date.today() - timedelta(days=7)
    
    with open(CITIES_FILE, encoding="utf-8") as file:
        cities = list(csv.DictReader(file))
    if args.uf:
        cities = [c for c in cities if c["uf"] == args.uf.upper()]
                  
    for city in cities:
        for year in range(START_YEAR, end_date.year + 1):
            key = f"open-meteo/archive/uf={city['uf']}/year={year}/data.json"
            is_current_year = year == end_date.year
            if already_saved(key) and not is_current_year:
                continue
            data = fetch_year(float(city["latitude"]), float(city["longitude"]), year, end_date)
            body = json.dumps(data).encode("utf-8")
            s3.put_object(Bucket=BUCKET, Key=key, Body=body)
            print(f"saved {key}")
            time.sleep(0.3)

if __name__ == "__main__":
    main()                