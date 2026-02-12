from flask import Blueprint, render_template, request
import os
import requests

main_blueprint = Blueprint("main", __name__)


@main_blueprint.route("/", methods=["GET", "POST"])
def dashboard():
    weather_data = None
    error_message = None

    if request.method == "POST":
        city = request.form.get("city", "").strip()
        state = request.form.get("state", "").strip()
        country = request.form.get("country", "").strip()

        if not city or not country:
            error_message = "City and Country are required."
        else:
            api_key = os.getenv("OPENWEATHER_API_KEY")

            if not api_key:
                error_message = "API key not configured."
            else:
                try:
                    url = (
                        "https://api.openweathermap.org/data/2.5/weather"
                        f"?q={city},{state},{country}"
                        f"&appid={api_key}&units=metric"
                    )

                    response = requests.get(url, timeout=5)

                    if response.status_code == 200:
                        weather_data = response.json()
                    else:
                        error_message = (
                            "Unable to fetch weather data. Please check your inputs."
                        )

                except requests.RequestException:
                    error_message = "Network error. Please try again."

    return render_template(
        "dashboard.html",
        weather_data=weather_data,
        error_message=error_message,
    )
