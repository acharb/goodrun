# Generated by Django 2.2.3 on 2019-09-12 19:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0011_userprofile_opted_out'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='crew_sent_to',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='events', to='base.Crew'),
        ),
    ]
