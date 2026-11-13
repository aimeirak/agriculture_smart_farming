import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("farmer_management", "0004_plantingrecord_notes_plantingrecord_planted_area_and_more"),
        ("smart_farming", "0002_weatherrecord_simulated_source"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FarmPrediction",
            fields=[
                ("created_by_username", models.CharField(blank=True, max_length=100, null=True)),
                ("created_on", models.DateTimeField(auto_now_add=True)),
                ("updated_by_username", models.CharField(blank=True, max_length=100, null=True)),
                ("updated_on", models.DateTimeField(auto_now=True)),
                ("prediction_id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("decision", models.CharField(choices=[("REQUIRED", "Irrigation recommended"), ("NOT_REQUIRED", "Irrigation not currently required")], max_length=20)),
                ("probability", models.DecimalField(decimal_places=6, max_digits=7)),
                ("model_name", models.CharField(max_length=50)),
                ("model_version", models.CharField(blank=True, max_length=30)),
                ("input_snapshot", models.JSONField(default=dict)),
                ("recommendation", models.TextField()),
                ("predicted_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_created", to=settings.AUTH_USER_MODEL)),
                ("farm", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="predictions", to="farmer_management.farm")),
                ("planting", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="predictions", to="farmer_management.plantingrecord")),
                ("sensor_reading", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="predictions", to="smart_farming.sensorreading")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(app_label)s_%(class)s_updated", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-predicted_at"]},
        ),
        migrations.AddIndex(
            model_name="farmprediction",
            index=models.Index(fields=["farm", "-predicted_at"], name="predictions_farm_pred_idx"),
        ),
        migrations.AddIndex(
            model_name="farmprediction",
            index=models.Index(fields=["decision", "-predicted_at"], name="predictions_decision_idx"),
        ),
    ]
