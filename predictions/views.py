import hmac
import os
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal, InvalidOperation

import requests
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from farmer_management.models import Farm
from smart_farming.models import SensorDevice, SensorReading, WeatherRecord
from .models import FarmPrediction
from .services import predict_irrigation


@login_required
def prediction_list(request):
    items = FarmPrediction.objects.select_related(
        "farm", "sensor_reading", "sensor_reading__device"
    ).all()[:200]
    return render(request, "predictions/prediction_list.html", {"predictions": items})


@login_required
@require_POST
def predict_latest_reading(request, reading_id):
    reading = SensorReading.objects.select_related(
        "device", "device__farm"
    ).filter(pk=reading_id).first()
    if reading is None:
        return JsonResponse({"error": "Sensor reading not found."}, status=404)

    model_name = request.POST.get("model", "xgboost")
    if model_name not in {"random_forest", "xgboost"}:
        return JsonResponse({"error": "Unsupported model."}, status=400)
    try:
        result = predict_irrigation(reading, model_name)
    except (FileNotFoundError, ValueError) as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse({
        "prediction_id": str(result.pk),
        "farm": result.farm.farm_name,
        "decision": result.get_decision_display(),
        "probability": float(result.probability),
        "model": result.model_name,
        "recommendation": result.recommendation,
    })


@csrf_exempt
@require_POST
def ingest_sensor_reading(request):
    """Receive an IoT reading as JSON and immediately run the deployed model."""
    configured_key = os.environ.get("SENSOR_INGEST_API_KEY", "")
    supplied_key = request.headers.get("X-API-Key", "")
    if not configured_key or not hmac.compare_digest(configured_key, supplied_key):
        return JsonResponse({"error": "A valid X-API-Key is required."}, status=401)

    try:
        import json
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return JsonResponse({"error": "Request body must be valid JSON."}, status=400)

    device_code = payload.get("device_code")
    if not device_code:
        return JsonResponse({"error": "device_code is required."}, status=400)
    device = SensorDevice.objects.select_related("farm").filter(
        device_code=device_code, status=SensorDevice.Status.ACTIVE
    ).first()
    if device is None:
        return JsonResponse({"error": "Active sensor device not found."}, status=404)

    try:
        recorded_text = payload.get("recorded_at")
        recorded_at = (
            datetime.fromisoformat(recorded_text.replace("Z", "+00:00"))
            if recorded_text else timezone.now()
        )
        if timezone.is_naive(recorded_at):
            recorded_at = timezone.make_aware(recorded_at, dt_timezone.utc)

        def optional_decimal(key):
            value = payload.get(key)
            return None if value in (None, "") else Decimal(str(value))

        moisture = optional_decimal("soil_moisture_pct")
        temperature = optional_decimal("temperature_c")
        humidity = optional_decimal("humidity_pct")
        for label, value in (("soil_moisture_pct", moisture), ("humidity_pct", humidity)):
            if value is not None and not Decimal("0") <= value <= Decimal("100"):
                return JsonResponse({"error": f"{label} must be between 0 and 100."}, status=400)
    except (ValueError, TypeError, InvalidOperation):
        return JsonResponse({"error": "Invalid sensor value or recorded_at timestamp."}, status=400)

    reading = SensorReading.objects.create(
        device=device,
        recorded_at=recorded_at,
        soil_moisture_pct=moisture,
        temperature_c=temperature,
        humidity_pct=humidity,
        created_by_username="sensor-api",
        updated_by_username="sensor-api",
    )

    model_name = payload.get("model", "xgboost")
    if model_name not in {"random_forest", "xgboost"}:
        return JsonResponse({"error": "model must be random_forest or xgboost."}, status=400)

    try:
        prediction = predict_irrigation(reading, model_name)
    except FileNotFoundError as exc:
        return JsonResponse({
            "message": "Sensor reading stored, but no trained model is deployed yet.",
            "reading_id": str(reading.pk),
            "model_error": str(exc),
        }, status=202)
    except ValueError as exc:
        return JsonResponse({
            "message": "Sensor reading stored, but prediction could not be made.",
            "reading_id": str(reading.pk),
            "prediction_error": str(exc),
        }, status=422)

    return JsonResponse({
        "message": "Sensor reading stored and prediction generated.",
        "reading_id": str(reading.pk),
        "farm": device.farm.farm_name,
        "decision": prediction.get_decision_display(),
        "probability": float(prediction.probability),
        "model": prediction.model_name,
        "recommendation": prediction.recommendation,
        "prediction_id": str(prediction.pk),
    }, status=201)


@login_required
@require_POST
def fetch_open_meteo(request):
    """Fetch the latest 24 hours of hourly weather from Open-Meteo and persist it."""
    farm_id = request.POST.get("farm_id")
    try:
        latitude = float(request.POST.get("latitude"))
        longitude = float(request.POST.get("longitude"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Valid latitude and longitude are required."}, status=400)

    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return JsonResponse({"error": "Coordinates are outside valid ranges."}, status=400)

    farm = Farm.objects.filter(pk=farm_id).first()
    if farm is None:
        return JsonResponse({"error": "Farm not found."}, status=404)

    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "hourly": "temperature_2m,relative_humidity_2m,precipitation",
                "past_days": 1,
                "forecast_days": 1,
                "timezone": "UTC",
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        hourly = payload.get("hourly", {})
        times = hourly.get("time", [])
        if not times:
            return JsonResponse({"error": "Open-Meteo returned no hourly observations."}, status=502)

        temperatures = hourly.get("temperature_2m", [])
        humidities = hourly.get("relative_humidity_2m", [])
        rainfall_values = hourly.get("precipitation", [])
        cutoff = timezone.now() - timedelta(hours=24)
        imported = 0
        for index, time_text in enumerate(times):
            observed_at = datetime.fromisoformat(time_text)
            if timezone.is_naive(observed_at):
                observed_at = timezone.make_aware(observed_at, dt_timezone.utc)
            if observed_at < cutoff or observed_at > timezone.now():
                continue

            temperature = temperatures[index] if index < len(temperatures) else None
            humidity = humidities[index] if index < len(humidities) else None
            rainfall = rainfall_values[index] if index < len(rainfall_values) else 0
            WeatherRecord.objects.update_or_create(
                farm=farm,
                observed_at=observed_at,
                source=WeatherRecord.Source.API,
                defaults={
                    "temperature_c": temperature,
                    "humidity_pct": humidity,
                    "rainfall_mm": rainfall or 0,
                    "created_by_username": "open-meteo-api",
                    "updated_by_username": "open-meteo-api",
                },
            )
            imported += 1
    except requests.RequestException as exc:
        return JsonResponse({"error": f"Open-Meteo request failed: {exc}"}, status=502)
    except (KeyError, TypeError, ValueError) as exc:
        return JsonResponse({"error": f"Could not process Open-Meteo response: {exc}"}, status=502)

    return JsonResponse({
        "message": "Hourly weather observations imported from Open-Meteo.",
        "farm": farm.farm_name,
        "observations_saved_or_updated": imported,
        "source": WeatherRecord.Source.API,
        "rainfall_window": "Last 24 hours",
    })
