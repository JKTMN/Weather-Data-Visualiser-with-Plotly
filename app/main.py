from flask import Flask, render_template, request
from meteostat import Point, Daily
from datetime import datetime, timedelta
import plotly.graph_objs as go
import plotly.io as pio
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import requests
import pytz
from config import API_KEY

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


def get_city_coordinates(city):
    geolocator = Nominatim(user_agent="YourApp/1.0")
    location = geolocator.geocode(city)
    if location:
        return {'latitude': location.latitude, 'longitude': location.longitude}
    else:
        return None

def create_plot(data):
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=data.index, y=data['tavg'], mode='lines+markers', name='Average Temperature'))
    fig.add_trace(go.Scatter(x=data.index, y=data['tmin'], mode='lines+markers', name='Min Temperature'))
    fig.add_trace(go.Scatter(x=data.index, y=data['tmax'], mode='lines+markers', name='Max Temperature'))

    fig.update_layout(title='Historical Weather Data', xaxis_title='Date', yaxis_title='Temperature (°C)')

    return fig

@app.route("/", methods=["GET", "POST"])
def weather():
    if request.method == "POST":
        city = request.form["city"]
        weather_data = fetch_weather_data(city)
        if "error" in weather_data:
            return render_template("error.html", error_message=weather_data["error"])
        else:
            coordinates = get_city_coordinates(city)
            if not coordinates:
                return f"City {city} not found.", 404

            end = datetime.now()
            start = end - timedelta(days=30)

            point = Point(coordinates['latitude'], coordinates['longitude'])
            data = Daily(point, start, end)
            data = data.fetch()

            fig = create_plot(data)

            graph_html = pio.to_html(fig, full_html=False)

            return render_template("weather.html", city=city, weather_data=weather_data, graph_html=graph_html)

    return render_template("weather.html")

if __name__ == "__main__":
    app.run(debug=True)
