from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("calibration_app", "0025_communitygroup_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="forum",
            name="group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="forums",
                to="calibration_app.communitygroup",
            ),
        ),
    ]

