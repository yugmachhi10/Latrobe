import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

# sample dataset
data = pd.DataFrame({
    "pm25": [20,50,80,120,200],
    "temp": [25,30,28,35,40],
    "humidity": [40,60,50,70,80],
    "aqi": [30,70,110,180,300]
})

X = data[["pm25","temp","humidity"]]
y = data["aqi"]

model = LinearRegression()
model.fit(X,y)

joblib.dump(model,"model.pkl")
print("Model trained ✅")