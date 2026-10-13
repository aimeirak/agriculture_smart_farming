from django.contrib import admin

from .models import AgriculturalInput, Farmer, Farm, Crop, PlantingRecord,PlantingInput

# Register your models here.

@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "phone",
        "email",
        "status",
    )
    search_fields = ("first_name", "last_name", "phone", "email")
    list_filter = ("status",)

@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = (
        "farm_name",
        "farmer",
        "district",
        "sector",
        "area_hectares",
        "status",
    )

search_fields = ("farm_name", "farmer__first_name", "farmer__last_name")
list_filter = ("district", "status")

@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = (
        "crop_id",
        "crop_name",
        "crop_category",
        "is_active",
    )

    search_fields = ("crop_name",)

    list_filter = ("crop_category", "is_active")


    @admin.register(PlantingRecord)
    class PlantingRecordAdmin(admin.ModelAdmin):
        list_display = (
        "planting_id",
        "farm",
        "crop",
        "planting_date",
        "expected_harvest_date",
        "season",
        "area_planted_hectares",
        "status",
    )
        list_filter = (
        "status",
        "season",
        "planting_date",
        "expected_harvest_date",
        )

        search_fields = (
        "planting_id",
        "farm__name",
        "crop__name",
        "season",
        )

@admin.register(AgriculturalInput)
class AgriculturalInputAdmin(admin.ModelAdmin):
    list_display = (
        "input_id",
        "input_name",
        "input_type",
        "unit_of_measure",
        "status",
    )

    search_fields = ("input_name",)

    list_filter = ("input_type", "status")
@admin.register(PlantingInput)
class PlantingInputAdmin(admin.ModelAdmin):
    list_display = (
        "planting",
        "agricultural_input",
        "quantity_used",
        "application_date",
    )
    list_filter = ("application_date",)
    search_fields = (
        "agricultural_input__input_name",
        "planting__farm__farm_name",
    )