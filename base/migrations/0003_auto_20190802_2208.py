# Generated by Django 2.1.10 on 2019-08-02 22:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_auto_20190802_2202'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='questionflownode',
            options={},
        ),
        migrations.AlterUniqueTogether(
            name='questionflownode',
            unique_together={('title', 'order')},
        ),
    ]
