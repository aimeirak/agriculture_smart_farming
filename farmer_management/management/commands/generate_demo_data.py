import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from farmer_management.models import (
    District, Sector, Farmer, Farm, Crop, PlantingRecord,
    AgriculturalInput, PlantingInput,
)
from smart_farming.models import (
    SensorDevice, SensorReading, WeatherRecord, IrrigationRecord,
)
from predictions.models import FarmPrediction


class Command(BaseCommand):
    help = "Generate realistic demonstration data for all Agriculture Smart Farming tables."

    def add_arguments(self, parser):
        parser.add_argument("--readings-per-device", type=int, default=120)
        parser.add_argument("--weather-days", type=int, default=90)
        parser.add_argument("--predictions", type=int, default=100)
        parser.add_argument("--seed", type=int, default=2026)

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(options["seed"])
        now = timezone.now()
        today = timezone.localdate()

        self.stdout.write(self.style.NOTICE("Creating reference and farm data..."))

        district_names = {
            "Kayonza": ["Mukarange", "Rukara", "Kabare"],
            "Bugesera": ["Nyamata", "Rilima", "Mayange"],
            "Rwamagana": [" Kigabiro", "Muhazi", "Gishari"],
            "Gasabo": ["Kimironko", "Kacyiru", "Rusororo"],
        }
        districts = {}
        sectors = {}
        for district_name, sector_names in district_names.items():
            district, _ = District.objects.get_or_create(name=district_name)
            districts[district_name] = district
            for sector_name in sector_names:
                sector_name = sector_name.strip()
                sector, _ = Sector.objects.get_or_create(
                    district=district, name=sector_name
                )
                sectors[(district_name, sector_name)] = sector

        farmer_names = [
            ("Jean", "Ndayisaba"), ("Marie", "Uwase"),
            ("Eric", "Habimana"), ("Aline", "Mukamana"),
            ("Patrick", "Niyonzima"), ("Grace", "Umutoni"),
            ("David", "Mugisha"), ("Beatha", "Iradukunda"),
            ("Emmanuel", "Nsengimana"), ("Diane", "Nyirahabimana"),
            ("Samuel", "Bizimana"), ("Claudine", "Mukeshimana"),
        ]
        farmers = []
        for i, (first, last) in enumerate(farmer_names, start=1):
            farmer, _ = Farmer.objects.get_or_create(
                phone=f"+250788100{i:03d}",
                defaults={
                    "first_name": first, "last_name": last,
                    "email": f"farmer{i}@example.com",
                    "status": Farmer.Status.ACTIVE,
                    "created_by_username": "demo-seed",
                    "updated_by_username": "demo-seed",
                },
            )
            farmers.append(farmer)

        farm_specs = [
            ("Kayonza Farm", "Kayonza", "Mukarange", 12.5),
            ("Rukara Green Farm", "Kayonza", "Rukara", 8.0),
            ("Bugesera Sunrise Farm", "Bugesera", "Nyamata", 15.0),
            ("Rilima Model Farm", "Bugesera", "Rilima", 6.5),
            ("Rwamagana Valley Farm", "Rwamagana", "Kigabiro", 10.0),
            ("Muhazi Smart Farm", "Rwamagana", "Muhazi", 7.5),
            ("Kimironko Demo Farm", "Gasabo", "Kimironko", 4.0),
            ("Rusororo Agro Farm", "Gasabo", "Rusororo", 9.0),
        ]
        farms = []
        for i, (name, district_name, sector_name, area) in enumerate(farm_specs):
            farm, _ = Farm.objects.get_or_create(
                farm_name=name,
                defaults={
                    "farmer": farmers[i % len(farmers)],
                    "district": districts[district_name],
                    "sector": sectors[(district_name, sector_name)],
                    "area_hectares": Decimal(str(area)),
                    "status": Farm.Status.ACTIVE,
                    "created_by_username": "demo-seed",
                    "updated_by_username": "demo-seed",
                },
            )
            farms.append(farm)

        crop_specs = [
            ("Maize", Crop.Category.CEREAL),
            ("Beans", Crop.Category.LEGUME),
            ("Rice", Crop.Category.CEREAL),
            ("Tomatoes", Crop.Category.VEGETABLE),
            ("Irish Potatoes", Crop.Category.OTHER),
            ("Cassava", Crop.Category.OTHER),
            ("Sorghum", Crop.Category.CEREAL),
            ("Soybeans", Crop.Category.LEGUME),
            ("Onions", Crop.Category.VEGETABLE),
            ("Bananas", Crop.Category.FRUIT),
        ]
        crops = []
        for name, category in crop_specs:
            crop, _ = Crop.objects.get_or_create(
                crop_name=name,
                defaults={
                    "crop_category": category,
                    "description": f"Demonstration crop record for {name}.",
                    "is_active": True,
                    "created_by_username": "demo-seed",
                    "updated_by_username": "demo-seed",
                },
            )
            crops.append(crop)

        input_specs = [
            ("Maize Hybrid Seed", AgriculturalInput.InputType.SEED, "kg"),
            ("Bean Seed", AgriculturalInput.InputType.SEED, "kg"),
            ("NPK 17-17-17", AgriculturalInput.InputType.FERTILIZER, "kg"),
            ("Urea", AgriculturalInput.InputType.FERTILIZER, "kg"),
            ("Compost Manure", AgriculturalInput.InputType.FERTILIZER, "kg"),
            ("DAP Fertilizer", AgriculturalInput.InputType.FERTILIZER, "kg"),
            ("Tomato Fungicide", AgriculturalInput.InputType.PESTICIDE, "litre"),
            ("Neem-based Pesticide", AgriculturalInput.InputType.PESTICIDE, "litre"),
            ("Herbicide", AgriculturalInput.InputType.PESTICIDE, "litre"),
            ("Drip Irrigation Kit", AgriculturalInput.InputType.OTHER, "piece"),
            ("Mulching Material", AgriculturalInput.InputType.OTHER, "bundle"),
            ("Rice Seed", AgriculturalInput.InputType.SEED, "kg"),
        ]
        agri_inputs = []
        for name, input_type, unit in input_specs:
            obj, _ = AgriculturalInput.objects.get_or_create(
                input_name=name,
                defaults={
                    "input_type": input_type, "unit_of_measure": unit,
                    "description": f"Sample inventory item: {name}.",
                    "status": AgriculturalInput.Status.ACTIVE,
                    "created_by_username": "demo-seed",
                    "updated_by_username": "demo-seed",
                },
            )
            agri_inputs.append(obj)

        self.stdout.write(self.style.NOTICE("Creating planting and input-usage records..."))
        plantings = []
        for i, farm in enumerate(farms):
            for j in range(3):
                crop = crops[(i + j * 2) % len(crops)]
                planted = today - timedelta(days=35 + (i * 9) + j * 17)
                expected = planted + timedelta(days=90 + (j * 15))
                area = min(
                    Decimal(str(round(float(farm.area_hectares) * random.uniform(.15, .35), 2))),
                    farm.area_hectares,
                )
                status = [
                    PlantingRecord.Status.GROWING,
                    PlantingRecord.Status.PLANTED,
                    PlantingRecord.Status.PLANNED,
                ][j]
                planting, _ = PlantingRecord.objects.get_or_create(
                    farm=farm, crop=crop, planting_date=planted,
                    defaults={
                        "expected_harvest_date": expected,
                        "season": "2026 Season A",
                        "area_planted_hectares": area,
                        "planted_area": area,
                        "quantity_planted": Decimal(str(random.randint(80, 450))),
                        "quantity_unit": "kg",
                        "notes": "Generated demonstration planting record.",
                        "status": status,
                        "created_by_username": "demo-seed",
                        "updated_by_username": "demo-seed",
                    },
                )
                plantings.append(planting)

        for planting in plantings:
            for input_obj in random.sample(agri_inputs, k=2):
                PlantingInput.objects.get_or_create(
                    planting=planting,
                    agricultural_input=input_obj,
                    application_date=planting.planting_date + timedelta(days=random.randint(3, 20)),
                    defaults={
                        "quantity_used": Decimal(str(round(random.uniform(2, 35), 3))),
                        "notes": "Sample application generated for demonstration.",
                        "created_by_username": "demo-seed",
                        "updated_by_username": "demo-seed",
                    },
                )

        self.stdout.write(self.style.NOTICE("Creating devices, sensor readings and weather..."))
        devices = []
        device_types = [
            SensorDevice.DeviceType.MULTI_SENSOR,
            SensorDevice.DeviceType.SOIL_MOISTURE,
        ]
        for i, farm in enumerate(farms):
            for j, device_type in enumerate(device_types):
                device, _ = SensorDevice.objects.get_or_create(
                    device_code=f"SIM-{farm.farm_id.hex[:8].upper()}-{j+1}",
                    defaults={
                        "farm": farm,
                        "device_type": device_type,
                        "installed_on": today - timedelta(days=120 + i * 5),
                        "status": SensorDevice.Status.ACTIVE,
                        "created_by_username": "demo-seed",
                        "updated_by_username": "demo-seed",
                    },
                )
                devices.append(device)

        readings_per_device = max(0, options["readings_per_device"])
        for device in devices:
            existing = SensorReading.objects.filter(device=device).count()
            for n in range(existing, readings_per_device):
                recorded = now - timedelta(minutes=30 * (readings_per_device - n))
                moisture = max(8.0, min(78.0, random.gauss(38, 13)))
                temperature = random.gauss(25, 3.5)
                humidity = max(25.0, min(95.0, random.gauss(67, 12)))
                SensorReading.objects.create(
                    device=device,
                    recorded_at=recorded,
                    soil_moisture_pct=Decimal(f"{moisture:.2f}"),
                    temperature_c=Decimal(f"{temperature:.2f}"),
                    humidity_pct=Decimal(f"{humidity:.2f}"),
                    created_by_username="demo-seed",
                    updated_by_username="demo-seed",
                )

        weather_days = max(0, options["weather_days"])
        for farm in farms:
            existing_dates = set(
                WeatherRecord.objects.filter(farm=farm)
                .values_list("observed_at__date", flat=True)
            )
            for day_offset in range(weather_days):
                observed_day = today - timedelta(days=day_offset)
                if observed_day in existing_dates:
                    continue
                seasonal_rain = random.random()
                rainfall = random.uniform(0, 18) if seasonal_rain < .28 else random.uniform(0, 1.5)
                WeatherRecord.objects.create(
                    farm=farm,
                    observed_at=timezone.make_aware(datetime.combine(observed_day, time(12, 0))),
                    rainfall_mm=Decimal(f"{rainfall:.2f}"),
                    temperature_c=Decimal(f"{random.uniform(19, 32):.2f}"),
                    humidity_pct=Decimal(f"{random.uniform(42, 88):.2f}"),
                    source=WeatherRecord.Source.SIMULATED,
                    created_by_username="demo-seed",
                    updated_by_username="demo-seed",
                )

        self.stdout.write(self.style.NOTICE("Creating irrigation history and AI predictions..."))
        irrigation_methods = ["Drip", "Sprinkler", "Manual hose", "Furrow"]
        for farm in farms:
            farm_plantings = [p for p in plantings if p.farm_id == farm.pk]
            for i in range(8):
                started = now - timedelta(days=i * 4 + random.randint(0, 3), hours=random.randint(1, 12))
                planting = random.choice(farm_plantings) if farm_plantings else None
                IrrigationRecord.objects.get_or_create(
                    farm=farm, started_at=started,
                    defaults={
                        "planting": planting,
                        "duration_minutes": random.randint(20, 100),
                        "water_volume_liters": Decimal(f"{random.uniform(150, 1800):.2f}"),
                        "method": random.choice(irrigation_methods),
                        "status": random.choice([
                            IrrigationRecord.Status.COMPLETED,
                            IrrigationRecord.Status.COMPLETED,
                            IrrigationRecord.Status.PLANNED,
                            IrrigationRecord.Status.CANCELLED,
                        ]),
                        "created_by_username": "demo-seed",
                        "updated_by_username": "demo-seed",
                    },
                )

        latest_readings = list(
            SensorReading.objects.select_related("device", "device__farm")
            .order_by("-recorded_at")[:max(options["predictions"], 0)]
        )
        for reading in latest_readings:
            farm = reading.device.farm
            planting = next((p for p in plantings if p.farm_id == farm.pk), None)
            moisture = float(reading.soil_moisture_pct or 0)
            required = moisture < 30
            decision = (
                FarmPrediction.Decision.REQUIRED if required
                else FarmPrediction.Decision.NOT_REQUIRED
            )
            recommendation = (
                f"Irrigation recommended. Soil moisture is {moisture:.1f}%. "
                "Check the crop and apply water according to field conditions."
                if required else
                f"Irrigation is not currently required. Soil moisture is {moisture:.1f}%. "
                "Continue monitoring the field."
            )
            FarmPrediction.objects.get_or_create(
                sensor_reading=reading,
                model_name="demo-rule-baseline",
                defaults={
                    "farm": farm,
                    "planting": planting,
                    "decision": decision,
                    "probability": Decimal(f"{min(.99, max(.01, (40-moisture)/40 if required else moisture/100)):.6f}"),
                    "model_version": "demo-1.0",
                    "input_snapshot": {
                        "soil_moisture_pct": moisture,
                        "temperature_c": float(reading.temperature_c or 0),
                        "humidity_pct": float(reading.humidity_pct or 0),
                        "data_origin": "SIMULATED",
                    },
                    "recommendation": recommendation,
                    "created_by_username": "demo-seed",
                    "updated_by_username": "demo-seed",
                },
            )

        self.stdout.write(self.style.SUCCESS("Demo data generation completed."))
        for model in [
            District, Sector, Farmer, Farm, Crop, PlantingRecord,
            AgriculturalInput, PlantingInput, SensorDevice, SensorReading,
            WeatherRecord, IrrigationRecord, FarmPrediction,
        ]:
            self.stdout.write(f"  {model.__name__}: {model.objects.count()}")
        self.stdout.write(self.style.WARNING(
            "Note: these are simulated demonstration records, not real farm observations or validated AI predictions."
        ))
