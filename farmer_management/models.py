import uuid
from decimal import Decimal

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

class AuditModel(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created",
    )
    created_by_username = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
    created_on = models.DateTimeField(auto_now_add=True)

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updated",
    )
    updated_by_username = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Farmer(AuditModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    farmer_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Farm(AuditModel):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    farm_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    farmer = models.ForeignKey(
        Farmer,
        on_delete=models.PROTECT,
        related_name="farms",
    )
    farm_name = models.CharField(max_length=150)
    district = models.CharField(max_length=100)
    sector = models.CharField(max_length=100)
    area_hectares = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:
        ordering = ["farm_name"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(area_hectares__gt=0),
                name="farm_area_positive",
            )
        ]

    def __str__(self):
        return self.farm_name


class Crop(AuditModel):
    class Category(models.TextChoices):
        CEREAL = "CEREAL", "Cereal"
        LEGUME = "LEGUME", "Legume"
        VEGETABLE = "VEGETABLE", "Vegetable"
        FRUIT = "FRUIT", "Fruit"
        OTHER = "OTHER", "Other"

    crop_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    crop_name = models.CharField(max_length=100, unique=True)
    crop_category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["crop_name"]

    def __str__(self):
        return self.crop_name


class PlantingRecord(AuditModel):
    class Status(models.TextChoices):
        PLANNED = "PLANNED", "Planned"
        PLANTED = "PLANTED", "Planted"
        GROWING = "GROWING", "Growing"
        HARVESTED = "HARVESTED", "Harvested"
        CANCELLED = "CANCELLED", "Cancelled"

    planting_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    farm = models.ForeignKey(
        Farm,
        on_delete=models.PROTECT,
        related_name="plantings",
    )
    crop = models.ForeignKey(
        Crop,
        on_delete=models.PROTECT,
        related_name="plantings",
    )
    planting_date = models.DateField()
    expected_harvest_date = models.DateField()
    season = models.CharField(max_length=50)
    area_planted_hectares = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
    )

    class Meta:
        ordering = ["-planting_date"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(area_planted_hectares__gt=0),
                name="planting_area_positive",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        errors = {}

        if (
            self.planting_date
            and self.expected_harvest_date
            and self.expected_harvest_date < self.planting_date
        ):
            errors["expected_harvest_date"] = (
                "Expected harvest date cannot be before planting date."
            )

        if self.farm_id and self.area_planted_hectares is not None:
            if self.area_planted_hectares > self.farm.area_hectares:
                errors["area_planted_hectares"] = (
                    "Planted area cannot exceed the farm's total area."
)

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.crop} - {self.farm} ({self.planting_date})"


class AgriculturalInput(AuditModel):

    class InputType(models.TextChoices):
        SEED = "SEED", "Seed"
        FERTILIZER = "FERTILIZER", "Fertilizer"
        PESTICIDE = "PESTICIDE", "Pesticide"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    input_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    input_name = models.CharField(max_length=120)

    input_type = models.CharField(
        max_length=30,
        choices=InputType.choices,
    )

    unit_of_measure = models.CharField(max_length=30)

    description = models.TextField(
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    def __str__(self):
        return self.input_name


class PlantingInput(AuditModel):

    planting_input_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    planting = models.ForeignKey(
        PlantingRecord,
        on_delete=models.PROTECT,
        related_name="inputs_used",
    )

    agricultural_input = models.ForeignKey(
        AgriculturalInput,
        on_delete=models.PROTECT,
        related_name="planting_usages",
    )

    quantity_used = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[
            MinValueValidator(Decimal("0.001"))
        ],
    )

    application_date = models.DateField()

    notes = models.TextField(
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-application_date"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity_used__gt=0),
                name="planting_input_quantity_positive",
            )
        ]

    def __str__(self):
        return (
            f"{self.agricultural_input} - "
            f"{self.planting} ({self.quantity_used})"
        )