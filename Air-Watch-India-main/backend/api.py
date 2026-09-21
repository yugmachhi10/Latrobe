from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import joblib
import numpy as np

app = Flask(__name__)
CORS(app)

# 🔑 API KEYS
AQI_KEY = "YOUR_WAQI_KEY"
WEATHER_KEY = "YOUR_OPENWEATHER_KEY"

# 🔥 LOAD AI MODEL
try:
    model = joblib.load("model.pkl")
except:
    model = None


# 🔥 MAIN API
@app.route("/live", methods=["GET"])
def live_data():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    try:
        # AQI API
        aqi_url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={AQI_KEY}"
        aqi_res = requests.get(aqi_url).json()

        aqi = aqi_res["data"]["aqi"]
        pm25 = aqi_res["data"]["iaqi"].get("pm25", {}).get("v", 0)

        # WEATHER API
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_KEY}&units=metric"
        weather = requests.get(weather_url).json()

        temp = weather["main"]["temp"]
        humidity = weather["main"]["humidity"]
        wind = weather["wind"]["speed"]

        # 🔥 AI PREDICTION
        if model:
            pred = model.predict([[pm25, temp, humidity]])[0]
        else:
            pred = pm25 + 10  # fallback

        return jsonify({
            "aqi": aqi,
            "pm25": pm25,
            "temp": temp,
            "humidity": humidity,
            "wind": wind,
            "prediction": round(pred,2)
        })

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)