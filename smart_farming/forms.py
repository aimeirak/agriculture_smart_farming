from django import forms
from farmer_management.models import Farm, PlantingRecord
from smart_farming.models import IrrigationRecord, SensorDevice, SensorReading, WeatherRecord


class SensorDeviceForm(forms.ModelForm):

    class Meta:
        model = SensorDevice

        fields = [
            "farm",
            "device_code",
            "device_type",
            "installed_on",
            "status",
        ]

        widgets = {
            "farm": forms.Select(attrs={
                "class": "form-select",
            }),
            "device_code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. SENSOR-001",
            }),
            "device_type": forms.Select(attrs={
                "class": "form-select",
            }),
            "installed_on": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "status": forms.Select(attrs={
                "class": "form-select",
            }),
        }

        labels = {
            "farm": "Farm",
            "device_code": "Device Code",
            "device_type": "Device Type",
            "installed_on": "Installation Date",
            "status": "Device Status",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["farm"].queryset = Farm.objects.all()
        self.fields["farm"].empty_label = "Select a farm"

        self.fields["device_type"].choices = [
            ("", "Select a device type"),
            *SensorDevice.DeviceType.choices,
        ]

        # Device status has a default in the model.
        if not self.instance.pk and not self.initial.get("status"):
            self.initial["status"] = SensorDevice.Status.ACTIVE

    def clean_device_code(self):
        device_code = self.cleaned_data["device_code"].strip()

        queryset = SensorDevice.objects.filter(
            device_code__iexact=device_code
        )

        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise forms.ValidationError(
                "A sensor device with this code already exists."
            )

        return device_code

# sensor reading form

class SensorReadingForm(forms.ModelForm):
    class Meta:
        model = SensorReading
        fields = [
            "device",
            "recorded_at",
            "soil_moisture_pct",
            "temperature_c",
            "humidity_pct",
        ]

        widgets = {
            "device": forms.Select(attrs={
                "class": "form-select",
            }),
            "recorded_at": forms.DateTimeInput(attrs={
                "class": "form-control",
                "type": "datetime-local",
            }),
            "soil_moisture_pct": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. 45.50",
                "step": "0.01",
                "min": "0",
                "max": "100",
            }),
            "temperature_c": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. 26.50",
                "step": "0.01",
            }),
            "humidity_pct": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. 65.50",
                "step": "0.01",
                "min": "0",
                "max": "100",
            }),
        }

        labels = {
            "device": "Sensor Device",
            "recorded_at": "Reading Date and Time",
            "soil_moisture_pct": "Soil Moisture (%)",
            "temperature_c": "Temperature (°C)",
            "humidity_pct": "Humidity (%)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["device"].queryset = (
            SensorDevice.objects.select_related("farm").order_by("device_code")
        )
        self.fields["device"].empty_label = "Select a sensor device"

        self.fields["soil_moisture_pct"].required = False
        self.fields["temperature_c"].required = False
        self.fields["humidity_pct"].required = False

    def clean_soil_moisture_pct(self):
        value = self.cleaned_data.get("soil_moisture_pct")

        if value is not None and not (0 <= value <= 100):
            raise forms.ValidationError(
                "Soil moisture must be between 0 and 100 percent."
            )

        return value

    def clean_humidity_pct(self):
        value = self.cleaned_data.get("humidity_pct")

        if value is not None and not (0 <= value <= 100):
            raise forms.ValidationError(
                "Humidity must be between 0 and 100 percent."
            )

        return value

    def clean(self):
        cleaned_data = super().clean()

        soil_moisture = cleaned_data.get("soil_moisture_pct")
        temperature = cleaned_data.get("temperature_c")
        humidity = cleaned_data.get("humidity_pct")

        if (
            soil_moisture is None
            and temperature is None
            and humidity is None
        ):
            raise forms.ValidationError(
                "Enter at least one sensor measurement."
            )

        return cleaned_data


class WeatherRecordForm(forms.ModelForm):
    class Meta:
        model = WeatherRecord
        fields = [
            "farm",
            "observed_at",
            "rainfall_mm",
            "temperature_c",
            "humidity_pct",
            "source",
        ]

        widgets = {
            "farm": forms.Select(attrs={
                "class": "form-select",
            }),
            "observed_at": forms.DateTimeInput(attrs={
                "class": "form-control",
                "type": "datetime-local",
            }),
            "rainfall_mm": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. 12.50",
                "step": "0.01",
                "min": "0",
            }),
            "temperature_c": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. 25.50",
                "step": "0.01",
            }),
            "humidity_pct": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. 65.50",
                "step": "0.01",
                "min": "0",
                "max": "100",
            }),
            "source": forms.Select(attrs={
                "class": "form-select",
            }),
        }

        labels = {
            "farm": "Farm",
            "observed_at": "Observation Date and Time",
            "rainfall_mm": "Rainfall (mm)",
            "temperature_c": "Temperature (°C)",
            "humidity_pct": "Humidity (%)",
            "source": "Weather Data Source",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["farm"].queryset = Farm.objects.all().order_by(
            "farm_name"
        )
        self.fields["farm"].empty_label = "Select a farm"

        self.fields["source"].choices = [
            ("", "Select a data source"),
            *WeatherRecord.Source.choices,
        ]

    def clean_rainfall_mm(self):
        rainfall = self.cleaned_data.get("rainfall_mm")

        if rainfall is not None and rainfall < 0:
            raise forms.ValidationError(
                "Rainfall cannot be negative."
            )

        return rainfall

    def clean_humidity_pct(self):
        humidity = self.cleaned_data.get("humidity_pct")

        if humidity is not None and not (0 <= humidity <= 100):
            raise forms.ValidationError(
                "Humidity must be between 0 and 100 percent."
            )

        return humidity




class IrrigationRecordForm(forms.ModelForm):
    class Meta:
        model = IrrigationRecord
        fields = [
            "farm",
            "planting",
            "started_at",
            "duration_minutes",
            "water_volume_liters",
            "method",
            "status",
        ]

        widgets = {
            "farm": forms.Select(attrs={
                "class": "form-select",
            }),
            "planting": forms.Select(attrs={
                "class": "form-select",
            }),
            "started_at": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "duration_minutes": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1",
                "step": "1",
                "placeholder": "Enter duration in minutes",
            }),
            "water_volume_liters": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "step": "0.01",
                "placeholder": "Enter water volume in liters",
            }),
            "method": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Drip, Sprinkler, Surface",
                "maxlength": "100",
            }),
            "status": forms.Select(attrs={
                "class": "form-select",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["farm"].queryset = Farm.objects.order_by("farm_name")
        self.fields["farm"].empty_label = "Select a farm"

        self.fields["planting"].queryset = (
            PlantingRecord.objects
            .select_related("farm", "crop")
            .order_by("-planting_date")
        )
        self.fields["planting"].required = False
        self.fields["planting"].empty_label = "No specific planting"

        self.fields["started_at"].input_formats = [
            "%Y-%m-%dT%H:%M",
            "%Y-%m-%d %H:%M:%S",
        ]

        self.fields["method"].label = "Irrigation Method"
        self.fields["duration_minutes"].label = "Duration (minutes)"
        self.fields["water_volume_liters"].label = "Water Volume (liters)"

    def clean_duration_minutes(self):
        duration = self.cleaned_data.get("duration_minutes")

        if duration is not None and duration < 1:
            raise forms.ValidationError(
                "Duration must be at least 1 minute."
            )

        return duration

    def clean_water_volume_liters(self):
        volume = self.cleaned_data.get("water_volume_liters")

        if volume is not None and volume < 0:
            raise forms.ValidationError(
                "Water volume cannot be negative."
            )

        return volume

    def clean(self):
        cleaned_data = super().clean()

        farm = cleaned_data.get("farm")
        planting = cleaned_data.get("planting")

        if farm and planting and planting.farm_id != farm.pk:
            self.add_error(
                "planting",
                "The selected planting record must belong to the selected farm.",
            )

        return cleaned_data