# Generated by Django 2.1.10 on 2019-08-08 02:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0010_event_expiration_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='opted_out',
            field=models.BooleanField(default=False),
        ),
    ]