# Generated by Django 2.2.16 on 2021-07-24 14:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("todos", "0006_auto_20210418_2100"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="todo",
            options={"ordering": ("status", "name", "deadline", "activate")},
        ),
    ]
