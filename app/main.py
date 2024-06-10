from datetime import datetime
from flask import Flask, render_template, request
import requests
from config import API_KEY
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
import pytz

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


def epoch_to_local(epoch, city):
    geolocator = Nominatim(user_agent="city_timezone_converter")
    location = geolocator.geocode(city)
    latitude, longitude = location.latitude, location.longitude

    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lat=latitude, lng=longitude)
    if timezone_str is None:
        raise ValueError("Unable to determine timezone for the city.")
    
    timezone = pytz.timezone(timezone_str)
    local_datetime = datetime.fromtimestamp(epoch, timezone)

    return local_datetime.date(), local_datetime.time()


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


        sunrise_epoch = data["sys"]["sunrise"]
        sunset_epoch = data["sys"]["sunset"]
        current_datetime = data["dt"]
        


        sunrise_date, sunrise_time = epoch_to_local(epoch=sunrise_epoch, city=city)
        sunrise_date, sunset_time = epoch_to_local(epoch=sunset_epoch, city=city)
        current_date, current_time = epoch_to_local(epoch=current_datetime, city=city)

        return {
            "city": city,
            "temperature": temperature,
            "description": description,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "sunrise": sunrise_time.strftime('%H:%M'),
            "sunset": sunset_time.strftime('%H:%M'),
            "current_time": current_time.strftime('%H:%M'),
            "current_date": current_date.strftime('%d/%m/%Y'),
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