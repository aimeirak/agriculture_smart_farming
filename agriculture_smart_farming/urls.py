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

from django.db.models import Count, Sum
from django.db.models.functions import ExtractMonth
from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth import views as auth_views

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
    path("accounts/login/",auth_views.LoginView.as_view( template_name="registration/login.html", redirect_authenticated_user=True,), name="login",),
    path("accounts/logout/",auth_views.LogoutView.as_view(), name="logout",),
]
