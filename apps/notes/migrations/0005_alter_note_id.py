# Generated by Django 4.2.16 on 2024-10-28 05:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notes", "0004_auto_20210418_2102"),
    ]

    operations = [
        migrations.AlterField(
            model_name="note",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]
