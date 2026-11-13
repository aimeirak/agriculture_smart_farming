
import json
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from farmer_management.models import Farm
from smart_farming.models import WeatherRecord, WeatherApiLog


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


class Command(BaseCommand):

    help = (
        "Retrieve hourly weather observations from Open-Meteo "
        "and save them for a farm."
    )

    def add_arguments(self, parser):

        parser.add_argument(
            "--farm-id",
            required=True,
            help="UUID of the farm."
        )

        parser.add_argument(
            "--latitude",
            required=True,
            type=float,
            help="Farm latitude."
        )

        parser.add_argument(
            "--longitude",
            required=True,
            type=float,
            help="Farm longitude."
        )

        parser.add_argument(
            "--hours",
            type=int,
            default=24,
            help="Number of past hours to retrieve. Default: 24."
        )

    def handle(self, *args, **options):

        farm = Farm.objects.filter(
            pk=options["farm_id"]
        ).first()

        if farm is None:
            raise CommandError("Farm not found.")

        latitude = options["latitude"]
        longitude = options["longitude"]
        hours = options["hours"]

        if not (-90 <= latitude <= 90):
            raise CommandError("Invalid latitude.")

        if not (-180 <= longitude <= 180):
            raise CommandError("Invalid longitude.")

        if hours < 1 or hours > 168:
            raise CommandError(
                "Hours must be between 1 and 168."
            )

        query = urlencode({
            "latitude": latitude,
            "longitude": longitude,
            "hourly": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "precipitation"
            ),
            "past_days": 7,
            "forecast_days": 1,
            "timezone": "UTC",
        })

        url = f"{OPEN_METEO_URL}?{query}"

        api_log = WeatherApiLog.objects.create(
            farm=farm,
            endpoint=url,
            status=WeatherApiLog.Status.RUNNING
        )

        try:

            request = Request(
                url,
                headers={
                    "User-Agent": "AgricultureSmartFarming/1.0",
                    "Accept": "application/json"
                }
            )

            with urlopen(request, timeout=30) as response:

                if response.status != 200:
                    raise CommandError(
                        f"Open-Meteo returned HTTP {response.status}."
                    )

                payload = json.loads(
                    response.read().decode("utf-8")
                )

            if payload.get("error"):
                raise CommandError(
                    payload.get(
                        "reason",
                        "Open-Meteo returned an API error."
                    )
                )

            hourly = payload.get("hourly", {})

            times = hourly.get("time", [])
            temperatures = hourly.get("temperature_2m", [])
            humidities = hourly.get("relative_humidity_2m", [])
            rainfalls = hourly.get("precipitation", [])

            if not times:
                raise CommandError(
                    "Open-Meteo returned no hourly weather data."
                )

            now = timezone.now()
            cutoff = now - timedelta(hours=hours)

            processed = 0

            with transaction.atomic():

                for index, time_text in enumerate(times):

                    observed_at = datetime.fromisoformat(time_text)

                    if timezone.is_naive(observed_at):
                        observed_at = observed_at.replace(
                            tzinfo=dt_timezone.utc
                        )

                    if observed_at < cutoff or observed_at > now:
                        continue

                    temperature = (
                        temperatures[index]
                        if index < len(temperatures)
                        else None
                    )

                    humidity = (
                        humidities[index]
                        if index < len(humidities)
                        else None
                    )

                    rainfall = (
                        rainfalls[index]
                        if index < len(rainfalls)
                        else None
                    )

                    if temperature is None or humidity is None:
                        continue

                    try:
                        temperature = Decimal(str(temperature))
                        humidity = Decimal(str(humidity))
                        rainfall = (
                            Decimal(str(rainfall))
                            if rainfall is not None
                            else Decimal("0")
                        )
                    except (InvalidOperation, ValueError):
                        continue

                    WeatherRecord.objects.update_or_create(
                        farm=farm,
                        observed_at=observed_at,
                        source=WeatherRecord.Source.API,
                        defaults={
                            "temperature_c": temperature,
                            "humidity_pct": humidity,
                            "rainfall_mm": rainfall,
                            "created_by_username": "open-meteo-api",
                            "updated_by_username": "open-meteo-api",
                        }
                    )

                    processed += 1

            api_log.status = WeatherApiLog.Status.SUCCESS
            api_log.records_processed = processed
            api_log.completed_at = timezone.now()
            api_log.error_message = ""
            api_log.save(
                update_fields=[
                    "status",
                    "records_processed",
                    "completed_at",
                    "error_message"
                ]
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully retrieved weather data for "
                    f"{farm.farm_name}. "
                    f"Records processed: {processed}"
                )
            )

        except Exception as exc:

            api_log.status = WeatherApiLog.Status.FAILED
            api_log.completed_at = timezone.now()
            api_log.error_message = str(exc)
            api_log.save(
                update_fields=[
                    "status",
                    "completed_at",
                    "error_message"
                ]
            )

            raise CommandError(
                f"Weather retrieval failed for {farm.farm_name}: {exc}"
            ) from exc
