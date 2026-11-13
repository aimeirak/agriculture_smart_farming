import uuid
from django.db import models
from farmer_management.models import AuditModel, Farm, PlantingRecord
from smart_farming.models import SensorReading

class FarmPrediction(AuditModel):
    class Decision(models.TextChoices):
        REQUIRED = "REQUIRED", "Irrigation recommended"
        NOT_REQUIRED = "NOT_REQUIRED", "Irrigation not currently required"
    prediction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Farm, on_delete=models.PROTECT, related_name="predictions")
    planting = models.ForeignKey(PlantingRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name="predictions")
    sensor_reading = models.ForeignKey(SensorReading, on_delete=models.SET_NULL, null=True, blank=True, related_name="predictions")
    decision = models.CharField(max_length=20, choices=Decision.choices)
    probability = models.DecimalField(max_digits=7, decimal_places=6)
    model_name = models.CharField(max_length=50)
    model_version = models.CharField(max_length=30, blank=True)
    input_snapshot = models.JSONField(default=dict)
    recommendation = models.TextField()
    predicted_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["-predicted_at"]
        indexes = [models.Index(fields=["farm", "-predicted_at"]), models.Index(fields=["decision", "-predicted_at"])]
    def __str__(self):
        return f"{self.farm} - {self.get_decision_display()} ({self.predicted_at:%Y-%m-%d %H:%M})"
