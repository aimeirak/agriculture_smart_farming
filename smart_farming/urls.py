
from django.urls import path,include
from smart_farming import views


urlpatterns = [
    # Sensor Device URLs

    path("sensors/",views.sensor_device_list,name="sensor_device_list",),
    path( "sensors/create/",views.sensor_device_create,name="sensor_device_create",),
    path( "sensors/<uuid:pk>/",views.sensor_device_detail,name="sensor_device_detail",),
    path( "sensors/<uuid:pk>/update/", views.sensor_device_update, name="sensor_device_update",),
    path("sensors/<uuid:pk>/delete/",views.sensor_device_delete,name="sensor_device_delete",),

     # Sensor Reading URLs
    path("sensor-readings/", views.sensor_reading_list, name="sensor_reading_list"),
    path("sensor-readings/create/", views.sensor_reading_create, name="sensor_reading_create"),
    path("sensor-readings/<uuid:pk>/", views.sensor_reading_detail, name="sensor_reading_detail"),
    path("sensor-readings/<uuid:pk>/update/", views.sensor_reading_update, name="sensor_reading_update"),
    path("sensor-readings/<uuid:pk>/delete/", views.sensor_reading_delete, name="sensor_reading_delete"),

     # Weather Record URLs
    path("weather-records/",views.weather_record_list,name="weather_record_list",),
    path("weather-records/create/",views.weather_record_create,name="weather_record_create",),
    path("weather-records/<uuid:pk>/",views.weather_record_detail,name="weather_record_detail",),
    path("weather-records/<uuid:pk>/update/", views.weather_record_update, name="weather_record_update",),
    path("weather-records/<uuid:pk>/delete/",views.weather_record_delete,name="weather_record_delete",),

    path("irrigation-records/",views.irrigation_record_list,name="irrigation_record_list",),
    path("irrigation-records/create/",views.irrigation_record_create,name="irrigation_record_create",),
    path( "irrigation-records/<uuid:pk>/",views.irrigation_record_detail,name="irrigation_record_detail",),
    path("irrigation-records/<uuid:pk>/update/",views.irrigation_record_update,name="irrigation_record_update",),
    path("irrigation-records/<uuid:pk>/delete/",views.irrigation_record_delete,name="irrigation_record_delete",),

    # Irrigation Record URLs
    path( "irrigation-records/",views.irrigation_record_list,name="irrigation_record_list",),
    path("irrigation-records/create/",views.irrigation_record_create,name="irrigation_record_create",),
    path("irrigation-records/<uuid:pk>/",views.irrigation_record_detail,name="irrigation_record_detail",),
    path("irrigation-records/<uuid:pk>/update/",views.irrigation_record_update,name="irrigation_record_update",),
    path("irrigation-records/<uuid:pk>/delete/",views.irrigation_record_delete,name="irrigation_record_delete",),
]