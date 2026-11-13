from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("smart_farming", "0001_initial")]
    operations = [
        migrations.AlterField(
            model_name="weatherrecord",
            name="source",
            field=models.CharField(
                choices=[("MANUAL", "Manual Entry"), ("API", "Weather API"),
                         ("SENSOR", "Sensor"), ("SIMULATED", "Simulated Data")],
                default="MANUAL", max_length=20,
            ),
        ),
    ]
