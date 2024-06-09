from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, request
import requests
from config import API_KEY

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

def fetch_weather_data(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()

        temperature = data["main"]["temp"]
        description = data["weather"][0]["description"]
        wind_speed = data["wind"]["speed"]
        wind_direction = data["wind"]["deg"]
        icon = data["weather"][0]["icon"]

        timezone_offset = data["timezone"]

        sunrise_unix = data["sys"]["sunrise"]
        sunset_unix = data["sys"]["sunset"]
        current_unix = data["dt"]

        sunrise_local = (datetime.utcfromtimestamp(sunrise_unix) + timedelta(seconds=timezone_offset)).strftime('%H:%M')
        sunset_local = (datetime.utcfromtimestamp(sunset_unix) + timedelta(seconds=timezone_offset)).strftime('%H:%M')

        current_local = (datetime.utcfromtimestamp(current_unix) + timedelta(seconds=timezone_offset)).strftime('%H:%M')
        current_date = (datetime.utcfromtimestamp(current_unix) + timedelta(seconds=timezone_offset)).strftime('%d-%m-%y')

        return {
            "city": city,
            "temperature": temperature,
            "description": description,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "sunrise": sunrise_local,
            "sunset": sunset_local,
            "current_time": current_local,
            "current_date": current_date,
            "icon": icon
        }

    except requests.RequestException as e:
        error_message = f"Error fetching weather data: {e}"
        return {"error": error_message}

@app.route("/")
def home():
    return render_template("weather.html")

@app.route("/weather", methods=["GET", "POST"])
def weather():
    if request.method == "POST":
        city = request.form["city"]
        weather_data = fetch_weather_data(city)
        if "error" in weather_data:
            return render_template("error.html", error_message=weather_data["error"])
        else:
            return render_template("weather.html", **weather_data)

    return render_template("weather.html")

if __name__ == "__main__":
    app.run(debug=True)