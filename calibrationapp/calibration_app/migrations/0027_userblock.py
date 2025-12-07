from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("calibration_app", "0026_forum_group"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserBlock",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "blocked",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="blocked_by",
                        to="auth.user",
                    ),
                ),
                (
                    "blocker",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="blocks_made",
                        to="auth.user",
                    ),
                ),
            ],
            options={
                "unique_together": {("blocker", "blocked")},
            },
        ),
        migrations.AddIndex(
            model_name="userblock",
            index=models.Index(fields=["blocker", "blocked"], name="calibratio_blocker_dd4c85_idx"),
        ),
    ]

