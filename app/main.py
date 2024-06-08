from flask import Flask, render_template, request
import requests
from config import API_KEY

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/weather", methods=["GET", "POST"])
def weather():
    if request.method == "POST":
        city = request.form["city"]

        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}"
            response = requests.get(url)
            data = response.json()

            temperature = data["main"]["temp"]
            humidity = data["main"]["humidity"]

            return render_template("weather.html", city=city, temperature=temperature, humidity=humidity)
        
        except requests.RequestException as e:
            error_message = f"Error fetching weather data: {e}"
            return render_template("error.html", error_message=error_message)
    
    return render_template("weather_form.html")

if __name__ == "__main__":
    app.run(debug=True)