from django.contrib import admin

# Register your models here.


from .models import (SensorDevice,SensorReading,WeatherRecord,IrrigationRecord,)

@admin.register(SensorDevice)
class SensorDeviceAdmin(admin.ModelAdmin):
    list_display = (
        "device_code",
        "farm",
        "device_type",
        "installed_on",
        "status",
    )
    search_fields = ("device_code", "farm__farm_name")
    list_filter = ("device_type", "status")

@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = (
        "device",
        "recorded_at",
        "soil_moisture_pct",
        "temperature_c",
        "humidity_pct",
        "received_at",
    )
    search_fields = ("device__device_code",)
    list_filter = ("recorded_at",)


@admin.register(WeatherRecord)
class WeatherRecordAdmin(admin.ModelAdmin):
    list_display = (
        "farm",
        "observed_at",
        "rainfall_mm",
        "temperature_c",
        "humidity_pct",
        "source",
    )
    search_fields = ("farm__farm_name",)
    list_filter = ("source", "observed_at") 


@admin.register(IrrigationRecord)
class IrrigationRecordAdmin(admin.ModelAdmin):
    list_display = (
        "farm",
        "planting",
        "started_at",
        "duration_minutes",
        "water_volume_liters",
        "status",
    )
    search_fields = ("farm__farm_name", "method")
    list_filter = ("status", "started_at")