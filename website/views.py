from flask import Blueprint, render_template, request
import os
import requests
from datetime import datetime

main_blueprint = Blueprint("main", __name__)

@main_blueprint.route("/", methods=["GET", "POST"])
def dashboard():
    weather_data = None
    error_message = None

    current_time = None
    current_icon_url = None
    current_temp = None
    current_desc = None
    feels_like = None
    current_summary = None
    wind_speed = None
    humidity = None
    visibility = None
    pressure = None
    dew_point = None

    # Default dropdown selection
    selected_location = "Waterville,ME,US"

    # If user selects a new location
    if request.method == "POST":
        selected_location = request.form.get("location", selected_location).strip()

    # Split into components
    city, state, country = (selected_location.split(",") + ["", "", ""])[:3]
    city = city.strip()
    state = state.strip()
    country = country.strip()

    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        error_message = "API key not configured."
    elif not city or not country:
        error_message = "City and Country are required."
    else:
        try:
            # -----------------------
            # CURRENT WEATHER
            # -----------------------
            weather_url = (
                "https://api.openweathermap.org/data/2.5/weather"
                f"?q={city},{state},{country}"
                f"&appid={api_key}&units=metric"
            )

            response = requests.get(weather_url, timeout=8)

            if response.status_code != 200:
                error_message = "Unable to fetch weather data."
            else:
                weather_data = response.json()

                w = weather_data["weather"][0]
                main = weather_data["main"]

                # Icon
                icon_code = w.get("icon")
                if icon_code:
                    current_icon_url = (
                        f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
                    )

                # Description
                current_desc = w.get("main") or w.get("description", "")

                # Temperature
                temp_c = round(main.get("temp", 0))
                feels_c = round(main.get("feels_like", 0))
                current_temp = f"{temp_c}°C"
                feels_like = f"{feels_c}°"

                # Other values
                humidity = f"{main.get('humidity', 0)}%"
                pressure = f"{main.get('pressure', 0)} mb"

                vis_m = weather_data.get("visibility")
                if vis_m is not None:
                    visibility = f"{round(vis_m / 1000)} km"

                wind_ms = weather_data.get("wind", {}).get("speed")
                if wind_ms is not None:
                    wind_speed = f"{round(wind_ms * 3.6)} km/h"

                # Local time
                dt_utc = weather_data.get("dt")
                tz_offset = weather_data.get("timezone", 0)

                if dt_utc is not None:
                    local_ts = dt_utc + tz_offset
                    current_time = datetime.utcfromtimestamp(local_ts).strftime("%-I:%M %p")

                current_summary = f"It is {w.get('description', '').strip()}."

                # -----------------------
                # DEW POINT (One Call 3.0 - DAILY)
                # -----------------------
                lat = weather_data.get("coord", {}).get("lat")
                lon = weather_data.get("coord", {}).get("lon")

                if lat is not None and lon is not None:
                    onecall_url = (
                        "https://api.openweathermap.org/data/3.0/onecall"
                        f"?lat={lat}&lon={lon}"
                        f"&exclude=minutely,hourly,alerts"
                        f"&appid={api_key}&units=metric"
                    )

                    onecall_resp = requests.get(onecall_url, timeout=8)

                    if onecall_resp.status_code == 200:
                        onecall = onecall_resp.json()

                        daily = onecall.get("daily", [])
                        if daily:
                            dp = daily[0].get("dew_point")
                            if dp is not None:
                                dew_point = f"{round(dp)}°"
                    else:
                        print("ONECALL ERROR:", onecall_resp.status_code, onecall_resp.text[:200])

        except requests.RequestException:
            error_message = "Network error. Please try again."

    return render_template(
        "dashboard.html",
        weather_data=weather_data,
        error_message=error_message,
        selected_location=selected_location,
        current_time=current_time,
        current_icon_url=current_icon_url,
        current_temp=current_temp,
        current_desc=current_desc,
        feels_like=feels_like,
        current_summary=current_summary,
        wind_speed=wind_speed,
        humidity=humidity,
        visibility=visibility,
        pressure=pressure,
        dew_point=dew_point,
    )
