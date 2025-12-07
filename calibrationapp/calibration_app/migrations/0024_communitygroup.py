from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calibration_app', '0023_merge_20251204_0000'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommunityGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True)),
                ('tagline', models.CharField(blank=True, max_length=255)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='communitygroup',
            name='members',
            field=models.ManyToManyField(blank=True, related_name='community_groups', to='calibration_app.profile'),
        ),
    ]
