from fastapi import FastAPI, Request   # ✅ ADDED Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
import time
from dotenv import load_dotenv

from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

from cachetools import TTLCache
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

load_dotenv()

app = FastAPI()

# ---------- RATE LIMIT ----------
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests. Slow down."}
    )

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- ENV ----------
OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY")

# ---------- CACHE ----------
CACHE = TTLCache(maxsize=1000, ttl=600)

# ---------- DB ----------
engine = create_engine("sqlite:///history.db")
Session = sessionmaker(bind=engine)
Base = declarative_base()

class QueryLog(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True)
    city = Column(String)
    aqi = Column(Float)

Base.metadata.create_all(engine)

# ---------- AI SCORING ----------
def weighted_aqi(pm25, pm10, no2, temp, humidity):
    base = (pm25 * 0.5) + (pm10 * 0.35) + (no2 * 0.15)

    if humidity and humidity > 70:
        base *= 1.05

    if temp and temp > 35:
        base *= 1.03

    return round(base)

def get_recommendation(aqi):
    if aqi <= 50:
        return {"level": "Good"}
    elif aqi <= 150:
        return {"level": "Moderate"}
    else:
        return {"level": "Hazardous"}

# ---------- CORE FUNCTION ----------
async def fetch_data(lat, lon, city_name="Unknown"):
    cache_key = f"{round(lat,3)},{round(lon,3)}"

    if cache_key in CACHE:
        return CACHE[cache_key]

    async with httpx.AsyncClient(timeout=10.0) as client:
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_KEY}&units=metric"
        weather_res = await client.get(weather_url)

        if weather_res.status_code != 200:
            return {"error": "Weather API failed"}

        weather = weather_res.json()

        pollution_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_KEY}"
        pollution_res = await client.get(pollution_url)

        if pollution_res.status_code != 200:
            return {"error": "Pollution API failed"}

        pollution = pollution_res.json()

    p = pollution["list"][0]["components"]

    pm25 = p.get("pm2_5", 0)
    pm10 = p.get("pm10", 0)
    no2 = p.get("no2", 0)
    o3 = p.get("o3", 0)
    co = p.get("co", 0)
    so2 = p.get("so2", 0)

    temp = weather["main"]["temp"]
    humidity = weather["main"]["humidity"]

    aqi = weighted_aqi(pm25, pm10, no2, temp, humidity)

    result = {
        "city": city_name,
        "source": "live",
        "pollution": {
            "aqi": aqi,
            "pm2_5": pm25,
            "pm10": pm10,
            "no2": no2,
            "o3": o3,
            "co": co,
            "so2": so2,
        },
        "weather": {
            "temperature": temp,
            "humidity": humidity,
            "wind_speed": weather["wind"]["speed"],
        },
        "recommendation": get_recommendation(aqi),
        "meta": {
            "timestamp": time.time(),
            "fresh": True
        }
    }

    CACHE[cache_key] = result

    db = Session()
    try:
        db.add(QueryLog(city=city_name, aqi=aqi))
        db.commit()
    finally:
        db.close()

    return result

# ---------- ENDPOINTS ----------

@app.get("/")
def home():
    return {"status": "running"}

# ✅ FIXED ENDPOINT
@app.get("/air")
@limiter.limit("10/minute")
async def get_air(request: Request, city: str):   # ✅ ADDED request
    async with httpx.AsyncClient(timeout=10.0) as client:
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={OPENWEATHER_KEY}"
        geo_res = await client.get(geo_url)

        if geo_res.status_code != 200:
            return {"error": "Geocoding failed"}

        geo = geo_res.json()

    if not geo:
        return {"error": "City not found"}

    lat = geo[0]["lat"]
    lon = geo[0]["lon"]

    return await fetch_data(lat, lon, city)

# ✅ FIXED ENDPOINT
@app.get("/air/location")
@limiter.limit("10/minute")
async def get_air_location(request: Request, lat: float, lon: float):  # ✅ ADDED request
    return await fetch_data(lat, lon, "GPS Location")