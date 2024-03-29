# Generated by Django 2.1.10 on 2019-08-02 21:58

import dirtyfields.dirtyfields
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Crew',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(max_length=40, unique=True)),
            ],
            options={
                'get_latest_by': 'created_at',
                'abstract': False,
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, null=True)),
                ('confirm_create_event', models.BooleanField(null=True)),
                ('event_structure_type', models.CharField(choices=[('STRUCTURED', 'STRUCTURED'), ('ASAP', 'ASAP')], max_length=25, null=True)),
                ('asap_event_message', models.TextField(blank=True, null=True)),
                ('number_of_players', models.IntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11), (12, 12), (13, 13), (14, 14), (15, 15)], null=True)),
                ('location', models.TextField(blank=True, null=True)),
                ('date_time', models.DateTimeField(null=True)),
                ('duration', models.CharField(max_length=25, null=True)),
                ('full_court', models.BooleanField(null=True)),
                ('cost', models.DecimalField(decimal_places=2, max_digits=8, null=True)),
                ('additional_notes', models.TextField(blank=True, null=True)),
                ('tipoff_eta', models.DurationField(editable=False, null=True)),
                ('invitations_have_sent', models.BooleanField(default=False)),
            ],
            options={
                'get_latest_by': 'created_at',
                'abstract': False,
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, null=True)),
                ('state', models.CharField(choices=[('SENT', 'SENT'), ('ACCEPTED', 'ACCEPTED'), ('MAYBE', 'MAYBE'), ('DENIED', 'DENIED'), ('ERROR', 'ERROR')], default='SENT', max_length=8)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='base.Event')),
            ],
            options={
                'get_latest_by': 'created_at',
                'abstract': False,
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='QuestionFlowNode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, null=True)),
                ('title', models.CharField(choices=[('INTRO', 'INTRO'), ('ASAP', 'ASAP'), ('STRUCTURED', 'STRUCTURED')], max_length=25)),
                ('prompt', models.CharField(max_length=250)),
                ('allowed_answers', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=250), size=None)),
                ('order', models.IntegerField()),
                ('answer_options_display', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=250), size=None)),
                ('next_flow_options', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('INTRO', 'INTRO'), ('ASAP', 'ASAP'), ('STRUCTURED', 'STRUCTURED')], max_length=25), size=None)),
                ('next', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='previous', to='base.QuestionFlowNode')),
            ],
            options={
                'get_latest_by': 'created_at',
                'abstract': False,
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='QuestionPrompt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, null=True)),
                ('active', models.BooleanField(default=True)),
                ('order_in_flow', models.IntegerField()),
                ('flow_type', models.CharField(choices=[('INTRO', 'INTRO'), ('ASAP', 'ASAP'), ('STRUCTURED', 'STRUCTURED')], max_length=15)),
                ('prompt', models.CharField(max_length=250)),
                ('answer_options_display', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=250), size=None)),
                ('event_field', models.CharField(blank=True, max_length=50, null=True)),
                ('allowed_answers', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=250), size=None)),
                ('next_flow_options', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('INTRO', 'INTRO'), ('ASAP', 'ASAP'), ('STRUCTURED', 'STRUCTURED')], max_length=25), size=None)),
                ('event', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='base.Event')),
            ],
            options={
                'get_latest_by': 'created_at',
                'abstract': False,
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='QuestionResponse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, null=True)),
                ('text', models.TextField(blank=True, null=True)),
                ('question_prompt', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='response', to='base.QuestionPrompt')),
            ],
            options={
                'get_latest_by': 'created_at',
                'abstract': False,
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, null=True)),
                ('phone_number', models.CharField(max_length=25, unique=True)),
                ('is_organizer', models.BooleanField(default=False)),
                ('name', models.CharField(blank=True, max_length=50, null=True)),
                ('creating_event', models.BooleanField(default=False)),
            ],
            options={
                'get_latest_by': 'created_at',
                'abstract': False,
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, models.Model),
        ),
        migrations.AddField(
            model_name='questionresponse',
            name='responder',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='base.UserProfile'),
        ),
        migrations.AddField(
            model_name='questionprompt',
            name='sent_to',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='base.UserProfile'),
        ),
        migrations.AddField(
            model_name='invitation',
            name='sent_to',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='base.UserProfile'),
        ),
        migrations.AddField(
            model_name='event',
            name='organizer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events_organized', to='base.UserProfile'),
        ),
        migrations.AddField(
            model_name='event',
            name='participants',
            field=models.ManyToManyField(related_name='events_participated', to='base.UserProfile'),
        ),
        migrations.AddField(
            model_name='crew',
            name='userprofiles',
            field=models.ManyToManyField(related_name='crews', to='base.UserProfile'),
        ),
    ]
