import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from farmer_management.models import AuditModel, Farm, PlantingRecord

# Create your models here.
class SensorDevice(AuditModel):

    class DeviceType(models.TextChoices):
        SOIL_MOISTURE = "SOIL_MOISTURE", "Soil Moisture"
        TEMPERATURE = "TEMPERATURE", "Temperature"
        HUMIDITY = "HUMIDITY", "Humidity"
        MULTI_SENSOR = "MULTI_SENSOR", "Multi-Sensor"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        MAINTENANCE = "MAINTENANCE", "Under Maintenance"

    device_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    farm = models.ForeignKey(
        Farm,
        on_delete=models.PROTECT,
        related_name="sensor_devices",
    )

    device_code = models.CharField(
        max_length=100,
        unique=True,
    )

    device_type = models.CharField(
        max_length=30,
        choices=DeviceType.choices,
    )

    installed_on = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:
        ordering = ["device_code"]

    def __str__(self):
        return f"{self.device_code} - {self.farm.farm_name}"


class SensorReading(AuditModel):

    reading_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    device = models.ForeignKey(
        SensorDevice,
        on_delete=models.PROTECT,
        related_name="readings",
    )

    recorded_at = models.DateTimeField()

    soil_moisture_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    temperature_c = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    humidity_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(soil_moisture_pct__isnull=True)
                    | (
                        models.Q(soil_moisture_pct__gte=0)
                        & models.Q(soil_moisture_pct__lte=100)
                    )
                ),
                name="sensor_soil_moisture_range",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(humidity_pct__isnull=True)
                    | (
                        models.Q(humidity_pct__gte=0)
                        & models.Q(humidity_pct__lte=100)
                    )
                ),
                name="sensor_humidity_range",
            ),
        ]

    def __str__(self):
        return f"{self.device.device_code} - {self.recorded_at}"



class WeatherRecord(AuditModel):
    class Source(models.TextChoices):
        MANUAL = "MANUAL", "Manual Entry"
        API = "API", "Weather API"
        SENSOR = "SENSOR", "Sensor"

    weather_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    farm = models.ForeignKey(
        Farm,
        on_delete=models.PROTECT,
        related_name="weather_records",
    )

    observed_at = models.DateTimeField()

    rainfall_mm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )

    temperature_c = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    humidity_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.MANUAL,
    )

    class Meta:
        ordering = ["-observed_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rainfall_mm__gte=0),
                name="weather_rainfall_nonnegative",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(humidity_pct__isnull=True)
                    | (
                        models.Q(humidity_pct__gte=0)
                        & models.Q(humidity_pct__lte=100)
                    )
                ),
                name="weather_humidity_range",
            ),
        ]

    def __str__(self):
        return f"{self.farm.farm_name} - {self.observed_at}"



class IrrigationRecord(AuditModel):

    class Status(models.TextChoices):
        PLANNED = "PLANNED", "Planned"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    irrigation_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    farm = models.ForeignKey(
        Farm,
        on_delete=models.PROTECT,
        related_name="irrigation_records",
    )

    planting = models.ForeignKey(
        PlantingRecord,
        on_delete=models.PROTECT,
        related_name="irrigation_records",
        null=True,
        blank=True,
    )

    started_at = models.DateTimeField()

    duration_minutes = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    water_volume_liters = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    method = models.CharField(max_length=100)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
    )

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(duration_minutes__gt=0),
                name="irrigation_duration_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(water_volume_liters__gte=0),
                name="irrigation_water_nonnegative",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if (
            self.farm_id
            and self.planting_id
            and self.planting.farm_id != self.farm_id
        ):
            raise ValidationError({
                "planting": (
                    "The selected planting record must belong "
                    "to the selected farm."
                )
            })

    def __str__(self):
        return f"{self.farm.farm_name} - {self.started_at}"