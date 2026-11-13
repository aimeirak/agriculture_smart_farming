from django.urls import path
from . import views

urlpatterns = [
    path("", views.prediction_list, name="prediction_list"),
    path("sensor-reading/<uuid:reading_id>/run/", views.predict_latest_reading, name="predict_latest_reading"),
    path("api/sensor-readings/", views.ingest_sensor_reading, name="ingest_sensor_reading"),
    path("api/open-meteo/", views.fetch_open_meteo, name="fetch_open_meteo"),
]
