# Generated by Django 2.1.10 on 2019-08-02 22:24

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_auto_20190802_2208'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questionflownode',
            name='next_flow_options',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, choices=[('INTRO', 'INTRO'), ('ASAP', 'ASAP'), ('STRUCTURED', 'STRUCTURED')], max_length=25, null=True), null=True, size=None),
        ),
    ]
