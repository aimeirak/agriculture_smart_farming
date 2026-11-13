from django.contrib import admin
from .models import FarmPrediction
@admin.register(FarmPrediction)
class FarmPredictionAdmin(admin.ModelAdmin):
    list_display = ("farm", "decision", "probability", "model_name", "predicted_at")
    list_filter = ("decision", "model_name", "predicted_at")
    search_fields = ("farm__farm_name", "recommendation")
    readonly_fields = ("prediction_id", "input_snapshot", "predicted_at")
