from django.core.management.base import BaseCommand, CommandError
from smart_farming.models import SensorReading
from predictions.services import predict_irrigation


class Command(BaseCommand):
    help = "Generate and save predictions for recent sensor readings using a deployed model."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)
        parser.add_argument("--model", choices=["random_forest", "xgboost"], default="xgboost")

    def handle(self, *args, **opts):
        readings = (
            SensorReading.objects.select_related("device", "device__farm")
            .filter(soil_moisture_pct__isnull=False)
            .order_by("-recorded_at")[:opts["limit"]]
        )
        count = 0
        skipped = 0
        for reading in readings:
            if reading.predictions.filter(model_name=opts["model"]).exists():
                skipped += 1
                continue
            try:
                result = predict_irrigation(reading, opts["model"])
                self.stdout.write(
                    f"{result.farm}: {result.get_decision_display()} "
                    f"({float(result.probability):.1%}) [{result.model_name}]"
                )
                count += 1
            except (FileNotFoundError, ValueError) as exc:
                raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(
            f"Created {count} prediction(s); skipped {skipped} already-predicted reading(s)."
        ))
