# Generated by Django 4.2.16 on 2024-10-28 05:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("story", "0004_auto_20210602_1656"),
    ]

    operations = [
        migrations.AlterField(
            model_name="story",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]
