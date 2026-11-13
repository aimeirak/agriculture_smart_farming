from decimal import Decimal
from datetime import timedelta
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from smart_farming.models import WeatherRecord
from .models import FarmPrediction

FEATURES = [
    "soil_moisture_pct",
    "temperature_c",
    "humidity_pct",
    "rainfall_24h_mm",
]


@lru_cache(maxsize=2)
def load_model(model_name, modified_time):
    """Load a trained model once per process; mtime invalidates cache after retraining."""
    if model_name not in {"random_forest", "xgboost"}:
        raise ValueError("Unsupported model name.")
    model_path = (
        Path(settings.BASE_DIR)
        / "machine_learning"
        / "trained_models"
        / f"{model_name}.joblib"
    )
    if not model_path.exists():
        raise FileNotFoundError(
            f"Trained model not found: {model_path}. "
            "Run generate_training_data and train_irrigation first."
        )
    return joblib.load(model_path)


def get_model_artifact(model_name):
    path = (
        Path(settings.BASE_DIR)
        / "machine_learning"
        / "trained_models"
        / f"{model_name}.joblib"
    )
    if not path.exists():
        raise FileNotFoundError(
            f"Trained model not found: {path}. "
            "Run python manage.py train_irrigation first."
        )
    return load_model(model_name, path.stat().st_mtime_ns)


def build_features(reading):
    if reading.soil_moisture_pct is None:
        raise ValueError("The sensor reading must include soil moisture.")

    farm = reading.device.farm
    end_time = reading.recorded_at
    start_time = end_time - timedelta(hours=24)

    rainfall = WeatherRecord.objects.filter(
        farm=farm,
        observed_at__gte=start_time,
        observed_at__lte=end_time,
    ).aggregate(total=Sum("rainfall_mm"))["total"] or 0

    latest_weather = (
        WeatherRecord.objects.filter(farm=farm, observed_at__lte=end_time)
        .order_by("-observed_at")
        .first()
    )

    temperature = reading.temperature_c
    humidity = reading.humidity_pct
    if latest_weather:
        temperature = temperature if temperature is not None else latest_weather.temperature_c
        humidity = humidity if humidity is not None else latest_weather.humidity_pct

    return {
        "soil_moisture_pct": float(reading.soil_moisture_pct),
        "temperature_c": float(temperature if temperature is not None else 25.0),
        "humidity_pct": float(humidity if humidity is not None else 60.0),
        "rainfall_24h_mm": float(rainfall),
    }


def predict_irrigation(reading, model_name="random_forest"):
    artifact = get_model_artifact(model_name)
    values = build_features(reading)
    feature_names = artifact.get("features", FEATURES)
    missing = [name for name in feature_names if name not in values]
    if missing:
        raise ValueError(f"Model expects unsupported features: {', '.join(missing)}")

    frame = pd.DataFrame([[values[name] for name in feature_names]], columns=feature_names)
    model = artifact["model"]
    predicted_class = int(model.predict(frame)[0])

    probability = 0.0
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(frame)[0]
        classes = list(model.classes_)
        probability = float(probabilities[classes.index(1)]) if 1 in classes else 0.0

    decision = (
        FarmPrediction.Decision.REQUIRED
        if predicted_class == 1
        else FarmPrediction.Decision.NOT_REQUIRED
    )
    if decision == FarmPrediction.Decision.REQUIRED:
        advice = (
            "The model indicates irrigation may be required. Check the crop growth stage, "
            "soil condition and local guidance before applying water."
        )
    else:
        advice = (
            "The model does not currently recommend irrigation. Continue monitoring "
            "soil moisture and recent rainfall."
        )

    return FarmPrediction.objects.create(
        farm=reading.device.farm,
        sensor_reading=reading,
        decision=decision,
        probability=Decimal(str(round(probability, 6))),
        model_name=model_name,
        model_version=str(artifact.get("version", "1.0")),
        input_snapshot={
            **values,
            "data_origin": "SENSOR_READING_PLUS_WEATHER_RECORDS",
        },
        recommendation=advice,
    )
