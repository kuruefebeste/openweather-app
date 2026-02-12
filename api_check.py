import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        print(f"Missing environment variable: {name}")
        sys.exit(1)
    return value


def get_current_weather(city: str, state: str, country: str) -> dict:
    api_key = require_env("OPENWEATHER_API_KEY")

    q = ",".join([part for part in [city, state, country] if part])
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": q, "appid": api_key, "units": "metric"}

    r = requests.get(url, params=params, timeout=10)
    print("Request URL:", r.url)
    r.raise_for_status()
    return r.json()


def main() -> None:
    # Change these to test different locations
    city = "Waterville"
    state = "ME"
    country = "US"

    data = get_current_weather(city, state, country)

    print("\nSuccess! Key fields:")
    print("name:", data.get("name"))
    print("weather:", data.get("weather", [{}])[0].get("description"))
    print("temp (C):", data.get("main", {}).get("temp"))
    print("feels_like (C):", data.get("main", {}).get("feels_like"))
    print("humidity:", data.get("main", {}).get("humidity"))
    print("pressure:", data.get("main", {}).get("pressure"))
    print("wind speed (m/s):", data.get("wind", {}).get("speed"))
    print("visibility (m):", data.get("visibility"))


if __name__ == "__main__":
    main()
