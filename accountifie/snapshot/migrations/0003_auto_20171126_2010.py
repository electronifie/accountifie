# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-11-27 01:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('snapshot', '0002_auto_20160414_1820'),
    ]

    operations = [
        migrations.AlterField(
            model_name='glsnapshot',
            name='snapped_at',
            field=models.DateTimeField(help_text='Local NY time'),
        ),
    ]
