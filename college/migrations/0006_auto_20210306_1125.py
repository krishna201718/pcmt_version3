# Generated by Django 3.0.7 on 2021-03-06 05:55

import college.models
import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('college', '0005_auto_20210305_1608'),
    ]

    operations = [
        migrations.RenameField(
            model_name='result',
            old_name='marks',
            new_name='ca_marks1',
        ),
        migrations.AddField(
            model_name='result',
            name='ca_marks2',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='result',
            name='ca_marks3',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='result',
            name='ca_marks4',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='admission',
            name='admit_card',
            field=models.ImageField(blank=True, max_length=255, null=True, upload_to=college.models.Admission.admit_card),
        ),
        migrations.AlterField(
            model_name='admission',
            name='rank_card',
            field=models.ImageField(blank=True, max_length=255, null=True, upload_to=college.models.Admission.rank_card),
        ),
        migrations.AlterField(
            model_name='question',
            name='exam_end_time',
            field=models.DateTimeField(default=datetime.datetime(2021, 3, 6, 11, 25, 39, 625288)),
        ),
        migrations.AlterField(
            model_name='question',
            name='exam_start_time',
            field=models.DateTimeField(default=datetime.datetime(2021, 3, 6, 11, 25, 39, 625288)),
        ),
        migrations.AlterField(
            model_name='student',
            name='admit_card',
            field=models.ImageField(blank=True, max_length=255, null=True, upload_to=college.models.Student.admit_card),
        ),
        migrations.AlterField(
            model_name='student',
            name='rank_card',
            field=models.ImageField(blank=True, max_length=255, null=True, upload_to=college.models.Student.rank_card),
        ),
    ]
