# Generated by Django 5.0.4 on 2024-11-30 15:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="is_paid",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="order",
            name="reference",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]