# Generated by Django 2.2.16 on 2020-10-12 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0014_auto_20201012_2046'),
    ]

    operations = [
        migrations.AddField(
            model_name='goal',
            name='progress',
            field=models.PositiveSmallIntegerField(blank=True, default=0),
        ),
    ]
