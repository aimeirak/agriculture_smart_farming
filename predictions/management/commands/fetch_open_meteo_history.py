import json
from datetime import datetime, timezone as dt_timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from farmer_management.models import Farm
from smart_farming.models import WeatherRecord


class Command(BaseCommand):
    help = "Import historical hourly weather observations from Open-Meteo into WeatherRecord."

    def add_arguments(self, parser):
        parser.add_argument("--farm-id", required=True)
        parser.add_argument("--latitude", required=True, type=float)
        parser.add_argument("--longitude", required=True, type=float)
        parser.add_argument("--start-date", required=True, help="YYYY-MM-DD")
        parser.add_argument("--end-date", required=True, help="YYYY-MM-DD")

    def handle(self, *args, **opts):
        farm = Farm.objects.filter(pk=opts["farm_id"]).first()
        if not farm:
            raise CommandError("Farm not found.")
        lat, lon = opts["latitude"], opts["longitude"]
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise CommandError("Invalid latitude or longitude.")
        try:
            start = datetime.strptime(opts["start_date"], "%Y-%m-%d").date()
            end = datetime.strptime(opts["end_date"], "%Y-%m-%d").date()
        except ValueError as exc:
            raise CommandError("Dates must use YYYY-MM-DD format.") from exc
        if end < start:
            raise CommandError("end-date must be on or after start-date.")

        params = urlencode({
            "latitude": lat, "longitude": lon,
            "start_date": start.isoformat(), "end_date": end.isoformat(),
            "hourly": "temperature_2m,relative_humidity_2m,precipitation",
            "timezone": "UTC",
        })
        url = "https://archive-api.open-meteo.com/v1/archive?" + params
        request = Request(url, headers={"User-Agent": "AgricultureSmartFarming/1.0"})
        try:
            with urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise CommandError(f"Open-Meteo historical request failed: {exc}") from exc

        hourly = payload.get("hourly", {})
        times = hourly.get("time", [])
        if not times:
            raise CommandError("Open-Meteo returned no hourly observations for this period/location.")
        temps = hourly.get("temperature_2m", [])
        humidities = hourly.get("relative_humidity_2m", [])
        rainfalls = hourly.get("precipitation", [])
        existing_times = set(WeatherRecord.objects.filter(
            farm=farm, source=WeatherRecord.Source.API,
            observed_at__date__gte=start, observed_at__date__lte=end,
        ).values_list("observed_at", flat=True))
        records = []
        for index, time_text in enumerate(times):
            observed = datetime.fromisoformat(time_text)
            if timezone.is_naive(observed):
                observed = observed.replace(tzinfo=dt_timezone.utc)
            if observed in existing_times:
                continue
            records.append(WeatherRecord(
                farm=farm, observed_at=observed,
                temperature_c=temps[index] if index < len(temps) else None,
                humidity_pct=humidities[index] if index < len(humidities) else None,
                rainfall_mm=rainfalls[index] if index < len(rainfalls) and rainfalls[index] is not None else 0,
                source=WeatherRecord.Source.API,
            ))
        WeatherRecord.objects.bulk_create(records, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(
            f"Imported {len(records)} new historical hourly weather records for {farm.farm_name}; "
            f"skipped {len(times) - len(records)} timestamps already present."
        ))
