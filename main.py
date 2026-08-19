import random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_pollution_level(data):
    pm25 = data["PM2.5"]

    if pm25 > 120:
        return "Hazardous 🔴"
    elif pm25 > 60:
        return "Moderate 🟡"
    else:
        return "Good 🟢"



def get_data(city):
    api_key = "8ecdab9cc2e1720cd3ec9980373c7a6e"

    coords = {
        "delhi": (28.61, 77.23),
        "pune": (18.52, 73.85)
    }

    lat, lon = coords[city.lower()]

    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"

    response = requests.get(url)
    data = response.json()

    print("API RESPONSE:", data)  # 🔥 DEBUG

    # ✅ SAFETY CHECK
    """if "list" not in data:
        if city.lower() == "delhi":
            return {
                "PM2.5": 180,
                "PM10": 250,
                "NO2": 90,
                "temp": 32,
                "humidity": 40
            }
        elif city.lower() == "pune":
            return {
                "PM2.5": 70,
                "PM10": 110,
                "NO2": 40,
                "temp": 28,
                "humidity": 60
            }"""
    
    pollution = data["list"][0]["components"]

    print(data)

    return {
        "PM2.5": pollution["pm2_5"],
        "PM10": pollution["pm10"],
        "NO2": pollution["no2"],
        "temp": 30,
        "humidity": 50
    }

def get_recommendation(city, data):
    level = get_pollution_level(data)

    result = {
        "level": level,
        "plants": [],
        "foods": [],
        "actions": []
    }

    # 🔴 HIGH POLLUTION (Delhi-like)
    if level == "Hazardous 🔴":
        result["plants"] = [
            "Snake Plant", "Areca Palm", "Spider Plant", "Rubber Plant"
        ]

        result["foods"] = [
            "Apple", "Orange", "Spinach", "Turmeric", "Ginger"
        ]

        result["actions"] = [
            "Avoid outdoor activities",
            "Wear mask outside",
            "Use air-purifying plants",
            "Eat anti-inflammatory foods"
        ]

    # 🟡 MODERATE POLLUTION (Pune-like)
    elif level == "Moderate 🟡":
        result["plants"] = [
            "Aloe Vera", "Peace Lily", "Anthurium"
        ]

        result["foods"] = [
            "Carrot", "Tomato", "Beetroot", "Papaya"
        ]

        result["actions"] = [
            "Limit long outdoor exposure",
            "Stay hydrated",
            "Maintain indoor plants"
        ]

    # 🟢 LOW POLLUTION
    else:
        result["plants"] = [
            "Tulsi", "Croton"
        ]

        result["foods"] = [
            "Banana", "Mango", "Coconut water"
        ]

        result["actions"] = [
            "Maintain healthy lifestyle",
            "Regular exercise outdoors"
        ]

    return result

@app.get("/air")
def get_air_data(city: str = "delhi"):
    data = get_data(city)
    recommendation = get_recommendation(city, data)

    return {
        "city": city,
        "data": data,
        "recommendation": recommendation
    }