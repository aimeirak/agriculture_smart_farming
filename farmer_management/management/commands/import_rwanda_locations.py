import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from farmer_management.models import District, Sector


class Command(BaseCommand):
    help = "Import Rwanda districts and sectors from JSON files"

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-dir",
            type=str,
            default=None,
            help="Optional path to the folder containing the JSON files",
        )

    def handle(self, *args, **options):
        # Project root: directory containing manage.py
        BASE_DIR = Path(__file__).resolve().parents[3]

        data_dir = (
            Path(options["data_dir"]).resolve()
            if options["data_dir"]
            else BASE_DIR / "data"
        )

        district_file = data_dir / "all-district.json"
        sector_file = data_dir / "all-sector.json"

        # Verify that both files exist
        if not district_file.is_file() or not sector_file.is_file():
            raise CommandError(
                f"JSON files not found in: {data_dir}\n"
                f"District file: {district_file}\n"
                f"Sector file: {sector_file}\n"
                "Ensure both JSON files exist in the data folder."
            )

        # Load JSON files
        try:
            with district_file.open(encoding="utf-8") as file:
                districts_data = json.load(file)

            with sector_file.open(encoding="utf-8") as file:
                sectors_data = json.load(file)

        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(
                f"Could not read location files: {exc}"
            ) from exc

        if not isinstance(districts_data, list) or not isinstance(
            sectors_data, list
        ):
            raise CommandError(
                "Both JSON files must contain lists of records."
            )

        try:
            with transaction.atomic():
                districts_by_source_id = {}

                # Import districts
                for item in districts_data:
                    district_name = item["name"]["en"].strip()
                    source_id = item["id"]

                    if not district_name:
                        raise CommandError(
                            f"Empty district name for ID {source_id}"
                        )

                    district, _ = District.objects.get_or_create(
                        name=district_name
                    )

                    districts_by_source_id[source_id] = district

                imported_sectors = 0

                # Import sectors and associate each with its district
                for item in sectors_data:
                    sector_name = item["name"]["en"].strip()
                    parent = item.get("parent") or {}
                    parent_id = parent.get("id")

                    # Handle IDs represented as strings or numbers
                    district = districts_by_source_id.get(parent_id)

                    if district is None:
                        district = districts_by_source_id.get(
                            str(parent_id)
                        )

                    if district is None:
                        raise CommandError(
                            f"District not found for sector "
                            f"{sector_name!r}; parent ID: {parent_id!r}"
                        )

                    Sector.objects.get_or_create(
                        district=district,
                        name=sector_name,
                    )

                    imported_sectors += 1

        except (KeyError, TypeError, AttributeError) as exc:
            raise CommandError(
                f"Unexpected JSON structure in location files: {exc}"
            ) from exc

        self.stdout.write(
            self.style.SUCCESS(
                "Import completed successfully.\n"
                f"Districts in database: {District.objects.count()}\n"
                f"Sectors processed: {imported_sectors}\n"
                f"Total sectors in database: {Sector.objects.count()}"
            )
        )