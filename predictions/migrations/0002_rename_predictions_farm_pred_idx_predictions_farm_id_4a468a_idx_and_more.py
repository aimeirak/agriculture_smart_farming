
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("predictions", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RenameIndex(
                    model_name="farmprediction",
                    old_name="predictions_farm_pred_idx",
                    new_name="predictions_farm_id_4a468a_idx",
                ),
                migrations.RenameIndex(
                    model_name="farmprediction",
                    old_name="predictions_decision_idx",
                    new_name="predictions_decisio_9c14c3_idx",
                ),
            ],
        ),
    ]
