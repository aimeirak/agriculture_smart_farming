import csv
from pathlib import Path
import numpy as np
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

FEATURES = ["soil_moisture_pct", "temperature_c", "humidity_pct", "rainfall_24h_mm"]

class Command(BaseCommand):
    help = "Generate a synthetic irrigation training CSV for ML pipeline testing."

    def add_arguments(self, parser):
        parser.add_argument("--rows", type=int, default=10000)
        parser.add_argument("--seed", type=int, default=42)

    def handle(self, *args, **opts):
        rows, seed = opts["rows"], opts["seed"]
        if rows < 500:
            raise CommandError("Use at least 500 rows.")
        rng = np.random.default_rng(seed)
        soil = rng.uniform(8, 90, rows)
        temp = rng.uniform(12, 40, rows)
        humidity = rng.uniform(20, 100, rows)
        rainfall = np.clip(rng.gamma(1.4, 3.0, rows), 0, 35)
        # Explicit synthetic teaching rule, not agronomic ground truth.
        risk = (soil < 30).astype(float) * 0.58 + (temp > 30).astype(float) * 0.12
        risk += (humidity < 45).astype(float) * 0.10 - (rainfall >= 5).astype(float) * 0.32
        risk += rng.normal(0, 0.08, rows)
        labels = (risk > 0.35).astype(int)
        target = Path(settings.BASE_DIR) / "machine_learning" / "datasets"
        target.mkdir(parents=True, exist_ok=True)
        output = target / "simulated_irrigation_training.csv"
        with output.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(FEATURES + ["irrigation_required", "data_source"])
            for values in zip(soil, temp, humidity, rainfall, labels):
                writer.writerow([round(float(v), 3) for v in values[:4]] + [int(values[4]), "SYNTHETIC_RULE_LABEL"])
        self.stdout.write(self.style.SUCCESS(f"Created {rows} rows: {output}"))
        self.stdout.write(self.style.WARNING("Synthetic labels are for software testing only, not validated farming advice."))
