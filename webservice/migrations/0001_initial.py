# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import webservice.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Execution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('application_hadoop_id', models.CharField(default=webservice.models.generate_uuid, unique=True, max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=webservice.models.generate_uuid, max_length=100)),
                ('status', models.CharField(default=b'created', max_length=100)),
                ('command', models.TextField(default=b'', blank=True)),
                ('callback_url', models.TextField(default=b'', blank=True)),
                ('user', models.CharField(default=b'cc', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Token',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('token', models.CharField(default=webservice.models.generate_uuid, max_length=100)),
                ('user_id', models.IntegerField()),
                ('username', models.TextField(default=b'root', blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='execution',
            name='job',
            field=models.ForeignKey(to='webservice.Job'),
        ),
    ]
