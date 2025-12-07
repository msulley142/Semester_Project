from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("calibration_app", "0024_communitygroup"),
    ]

    operations = [
        migrations.AddField(
            model_name="communitygroup",
            name="category",
            field=models.CharField(choices=[("General", "General"), ("Habit", "Habit"), ("Skill", "Skill"), ("Goal", "Goal")], default="General", max_length=20),
        ),
    ]
