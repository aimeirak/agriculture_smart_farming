import csv
import math
from datetime import timedelta
from pathlib import Path
import numpy as np
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from farmer_management.models import Farm
from smart_farming.models import SensorDevice, SensorReading, WeatherRecord

class Command(BaseCommand):
    help = "Generate simulated IoT sensor readings, simulated weather records and an ML CSV dataset."

    def add_arguments(self, parser):
        parser.add_argument("--rows", type=int, default=10000)
        parser.add_argument("--interval-minutes", type=int, default=5)
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--farm-id", default=None)
        parser.add_argument("--replace-simulated", action="store_true")

    def handle(self, *args, **opts):
        rows, interval = opts["rows"], opts["interval_minutes"]
        if rows < 100 or interval < 1:
            raise CommandError("--rows must be at least 100 and --interval-minutes must be positive.")
        farms_qs = Farm.objects.filter(status=Farm.Status.ACTIVE)
        if opts.get("farm_id"):
            farms_qs = farms_qs.filter(pk=opts["farm_id"])
        farms = list(farms_qs)
        if not farms:
            raise CommandError("No active farm found. Register an active farm first, or check the farm UUID/status.")
        rng = np.random.default_rng(opts["seed"])
        devices = {}
        for farm in farms:
            device, _ = SensorDevice.objects.get_or_create(
                device_code=f"SIM-{str(farm.pk)[:8].upper()}",
                defaults={"farm": farm, "device_type": SensorDevice.DeviceType.MULTI_SENSOR,
                          "installed_on": timezone.localdate(), "status": SensorDevice.Status.ACTIVE})
            if device.farm_id != farm.pk:
                raise CommandError(f"Simulation device code collision for farm {farm}.")
            devices[farm.pk] = device
        if opts["replace_simulated"]:
            for device in devices.values():
                SensorReading.objects.filter(device=device).delete()
                WeatherRecord.objects.filter(farm=device.farm, source=WeatherRecord.Source.SIMULATED).delete()
        now = timezone.now().replace(second=0, microsecond=0)
        start = now - timedelta(minutes=(rows - 1) * interval)
        csv_rows, readings, weather = [], [], []
        per_farm_index = {farm.pk: 0 for farm in farms}
        for i in range(rows):
            farm = farms[i % len(farms)]
            j = per_farm_index[farm.pk]
            per_farm_index[farm.pk] += 1
            timestamp = start + timedelta(minutes=j * interval)
            phase = (timestamp.hour / 24.0) * 2 * math.pi
            temp = float(np.clip(24 + 5 * math.sin(phase - 1) + rng.normal(0, 1.3), 12, 40))
            humidity = float(np.clip(72 - (temp - 24) * 1.8 + rng.normal(0, 5), 20, 100))
            rain = float(np.clip(rng.gamma(0.8, 1.8), 0, 25))
            soil = float(np.clip(48 - max(0, temp - 25) * 0.8 - (j % 120) * 0.16 + rain * 1.2 + rng.normal(0, 3), 5, 90))
            # Synthetic decision label; transparent teaching heuristic only.
            risk = (0.60 if soil < 30 else 0.0) + (0.15 if temp > 30 else 0.0) + (0.10 if humidity < 45 else 0.0) - (0.35 if rain >= 5 else 0.0)
            label = int(risk >= 0.35)
            readings.append(SensorReading(device=devices[farm.pk], recorded_at=timestamp,
                soil_moisture_pct=round(soil, 2), temperature_c=round(temp, 2), humidity_pct=round(humidity, 2)))
            if j % max(1, 1440 // interval) == 0:
                weather.append(WeatherRecord(farm=farm, observed_at=timestamp, rainfall_mm=round(rain, 2),
                    temperature_c=round(temp, 2), humidity_pct=round(humidity, 2), source=WeatherRecord.Source.SIMULATED))
            csv_rows.append([round(soil, 3), round(temp, 3), round(humidity, 3), round(rain, 3), label,
                             str(farm.pk), timestamp.isoformat(), "SIMULATED_SENSOR"])
        with transaction.atomic():
            SensorReading.objects.bulk_create(readings, batch_size=1000)
            WeatherRecord.objects.bulk_create(weather, batch_size=1000, ignore_conflicts=True)
        dataset_dir = Path(settings.BASE_DIR) / "machine_learning" / "datasets"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        dataset_path = dataset_dir / "simulated_irrigation_training.csv"
        with dataset_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["soil_moisture_pct", "temperature_c", "humidity_pct", "rainfall_24h_mm", "irrigation_required", "farm_id", "recorded_at", "data_source"])
            writer.writerows(csv_rows)
        self.stdout.write(self.style.SUCCESS(f"Generated {len(readings)} sensor readings, {len(weather)} weather records, and {dataset_path}"))
        self.stdout.write(self.style.WARNING("All generated sensor values and irrigation labels are synthetic, not measured or agronomist-validated."))
