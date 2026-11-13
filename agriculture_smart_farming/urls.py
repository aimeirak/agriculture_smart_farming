"""
URL configuration for agriculture_smart_farming project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


import calendar
from urllib import request

from django.contrib import admin
from django.urls import path,include
from django.http import HttpResponse
from django.shortcuts import render

from farmer_management.models import AgriculturalInput, Crop, Farm, Farmer, PlantingInput, PlantingRecord
from smart_farming.models import IrrigationRecord, SensorDevice, SensorReading, WeatherRecord
from django.contrib.auth.decorators import login_required

from farmer_management.models import (
    Farm,
    Farmer,
    Crop,
    PlantingRecord,
    AgriculturalInput,
    PlantingInput,
)

from smart_farming.models import (
    SensorDevice,
    SensorReading,
    WeatherRecord,
    IrrigationRecord,
)
import json
from pathlib import Path

from django.db.models import Count, Sum
from django.db.models.functions import ExtractMonth
from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth import views as auth_views
from predictions.models import FarmPrediction

@login_required(login_url="/accounts/login/")
def home(request):
    today = timezone.localdate()
    current_year = today.year

    monthly_weather = {
        row["month"]: float(row["total"] or 0)
        for row in WeatherRecord.objects.filter(
            observed_at__year=current_year
        ).annotate(
            month=ExtractMonth("observed_at")
        ).values("month").annotate(
            total=Sum("rainfall_mm")
        )
    }

    monthly_irrigation = {
        row["month"]: float(row["total"] or 0)
        for row in IrrigationRecord.objects.filter(
            started_at__year=current_year,
            status=IrrigationRecord.Status.COMPLETED,
        ).annotate(
            month=ExtractMonth("started_at")
        ).values("month").annotate(
            total=Sum("water_volume_liters")
        )
    }

    month_labels = [
        calendar.month_abbr[month]
        for month in range(1, 13)
    ]

    total_plantings = PlantingRecord.objects.count()

    context = {
        "today": today,
        "current_year": current_year,

        # Dashboard cards
        "total_farms": Farm.objects.count(),
        "total_farmers": Farmer.objects.count(),
        "total_crops": Crop.objects.count(),
        "total_plantings": total_plantings,
        "total_sensor_devices": SensorDevice.objects.count(),
        "active_sensor_devices": SensorDevice.objects.filter(
            status=SensorDevice.Status.ACTIVE
        ).count(),
        "total_sensor_readings": SensorReading.objects.count(),
        "simulated_sensor_readings": SensorReading.objects.filter(device__device_code__startswith="SIM-").count(),
        "simulated_weather_records": WeatherRecord.objects.filter(source="SIMULATED").count(),
        "historical_api_weather_records": WeatherRecord.objects.filter(source=WeatherRecord.Source.API).count(),
        "total_weather_records": WeatherRecord.objects.count(),
        "total_agricultural_inputs": AgriculturalInput.objects.count(),
        "total_planting_input_usages": PlantingInput.objects.count(),

        # Existing planting and irrigation activity
        "planned_plantings": PlantingRecord.objects.filter(
            status=PlantingRecord.Status.PLANNED
        ).count(),
        "growing_plantings": PlantingRecord.objects.filter(
            status=PlantingRecord.Status.GROWING
        ).count(),
        "harvested_plantings": PlantingRecord.objects.filter(
            status=PlantingRecord.Status.HARVESTED
        ).count(),

        "total_irrigation_records": IrrigationRecord.objects.count(),
        "planned_irrigations": IrrigationRecord.objects.filter(
            status=IrrigationRecord.Status.PLANNED
        ).count(),
        "completed_irrigations": IrrigationRecord.objects.filter(
            status=IrrigationRecord.Status.COMPLETED
        ).count(),
        "cancelled_irrigations": IrrigationRecord.objects.filter(
            status=IrrigationRecord.Status.CANCELLED
        ).count(),
        "total_water_used": (
            IrrigationRecord.objects.filter(
                status=IrrigationRecord.Status.COMPLETED
            ).aggregate(total=Sum("water_volume_liters"))["total"] or 0
        ),

        # Recent activities
        "recent_plantings": PlantingRecord.objects.select_related(
            "farm", "crop"
        ).order_by("-planting_date")[:5],

        "recent_irrigations": IrrigationRecord.objects.select_related(
            "farm", "planting", "planting__crop"
        ).order_by("-started_at")[:5],

        "recent_weather": WeatherRecord.objects.select_related(
            "farm"
        ).order_by("-observed_at")[:5],

        "recent_sensor_readings": SensorReading.objects.select_related(
            "device", "device__farm"
        ).order_by("-recorded_at")[:5],

        "recent_predictions": FarmPrediction.objects.select_related("farm").all()[:5],
        "total_predictions": FarmPrediction.objects.count(),
        "irrigation_recommendations": FarmPrediction.objects.filter(decision=FarmPrediction.Decision.REQUIRED).count(),

        # Real monthly chart data
        "month_labels_json": json.dumps(month_labels),
        "rainfall_by_month_json": json.dumps([
            monthly_weather.get(month, 0)
            for month in range(1, 13)
        ]),
        "water_by_month_json": json.dumps([
            monthly_irrigation.get(month, 0)
            for month in range(1, 13)
        ]),
    }

    # AI analytics: read metrics produced by the model training command.
    model_dir = Path(__file__).resolve().parent.parent / "machine_learning" / "trained_models"
    metrics_file = model_dir / "comparison_metrics.json"
    model_metrics = {}
    if metrics_file.exists():
        try:
            model_metrics = json.loads(metrics_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            model_metrics = {}

    trained_models = model_metrics.get("models", {})
    model_order = [name for name in ("random_forest", "xgboost") if name in trained_models]
    display_names = {"random_forest": "Random Forest", "xgboost": "XGBoost"}
    context.update({
        "trained_model_count": len(model_order),
        "best_model_f1": max((trained_models[name].get("f1", 0) for name in model_order), default=None),
        "model_dataset_type": model_metrics.get("dataset", "not trained"),
        "model_training_rows": model_metrics.get("rows", 0),
        "ai_model_labels_json": json.dumps([display_names[name] for name in model_order]),
        "ai_accuracy_json": json.dumps([round(trained_models[name].get("accuracy", 0) * 100, 2) for name in model_order]),
        "ai_precision_json": json.dumps([round(trained_models[name].get("precision", 0) * 100, 2) for name in model_order]),
        "ai_recall_json": json.dumps([round(trained_models[name].get("recall", 0) * 100, 2) for name in model_order]),
        "ai_f1_json": json.dumps([round(trained_models[name].get("f1", 0) * 100, 2) for name in model_order]),
    })

    # Feature importance is taken from the trained model artifact, not hard-coded.
    feature_labels, rf_importance, xgb_importance = [], [], []
    feature_display = {
        "soil_moisture_pct": "Soil moisture",
        "temperature_c": "Temperature",
        "humidity_pct": "Humidity",
        "rainfall_24h_mm": "Rainfall (24h)",
    }
    for model_name, target in (("random_forest", rf_importance), ("xgboost", xgb_importance)):
        artifact_path = model_dir / f"{model_name}.joblib"
        if artifact_path.exists():
            try:
                import joblib
                artifact = joblib.load(artifact_path)
                model = artifact.get("model")
                importance = getattr(model, "feature_importances_", None)
                if importance is not None:
                    names = artifact.get("features", [])
                    if not feature_labels:
                        feature_labels = [feature_display.get(name, name) for name in names]
                    target.extend([round(float(value) * 100, 2) for value in importance])
            except Exception:
                target.clear()
    context["feature_labels_json"] = json.dumps(feature_labels)
    context["rf_feature_importance_json"] = json.dumps(rf_importance)
    context["xgb_feature_importance_json"] = json.dumps(xgb_importance)

    # Recent real sensor readings and stored AI predictions.
    moisture_readings = list(
        SensorReading.objects.exclude(soil_moisture_pct__isnull=True)
        .select_related("device", "device__farm").order_by("-recorded_at")[:12]
    )
    moisture_readings.reverse()
    context["moisture_labels_json"] = json.dumps([r.recorded_at.strftime("%d %b %H:%M") for r in moisture_readings])
    context["moisture_values_json"] = json.dumps([float(r.soil_moisture_pct) for r in moisture_readings])

    decision_counts = [
        FarmPrediction.objects.filter(decision=FarmPrediction.Decision.REQUIRED).count(),
        FarmPrediction.objects.filter(decision=FarmPrediction.Decision.NOT_REQUIRED).count(),
    ]
    context["ai_decision_counts_json"] = json.dumps(decision_counts)
    context["ai_required_count"] = decision_counts[0]
    context["ai_not_required_count"] = decision_counts[1]
    context["ai_recent_prediction_count"] = FarmPrediction.objects.filter(
        predicted_at__date=today
    ).count()

    # Total planted area, in hectares
    context["total_planted_area"] = (
        PlantingRecord.objects.aggregate(
            total=Sum("area_planted_hectares")
        )["total"] or 0
    )
    return render(request, "index.html", context)

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', home, name='home'),
    path("farm-management/", include("farmer_management.urls")),
    path( "smart-farming/",include("smart_farming.urls"),),
    path("predictions/", include("predictions.urls")),
    path("accounts/login/",auth_views.LoginView.as_view( template_name="registration/login.html", redirect_authenticated_user=True,), name="login",),
    path("accounts/logout/",auth_views.LogoutView.as_view(), name="logout",),
]
