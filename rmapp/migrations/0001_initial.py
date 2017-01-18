# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Cluster',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=b'', max_length=100, blank=True)),
                ('uuid', models.CharField(default=uuid.uuid4, max_length=100)),
                ('private_key', models.TextField(default=b'', max_length=1000, blank=True)),
                ('public_key', models.TextField(default=b'', max_length=1000, blank=True)),
                ('status', models.CharField(default=b'IDLE', max_length=100, blank=True)),
                ('hints', models.CharField(default=b'{}', max_length=100, blank=True)),
                ('credential', models.CharField(default=b'', max_length=100, blank=True)),
                ('targeted_slaves_count', models.IntegerField(default=0)),
                ('current_slaves_count', models.IntegerField(default=0)),
                ('the_new_user', models.CharField(default=b'{}', max_length=250)),
                ('appliance', models.CharField(max_length=100)),
                ('appliance_impl', models.CharField(max_length=100, blank=True)),
                ('common_appliance_impl', models.CharField(max_length=100, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Credential',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('site_name', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=100)),
                ('credentials', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=b'', max_length=100, blank=True)),
                ('is_master', models.BooleanField(default=False)),
                ('instance_id', models.CharField(default=b'', max_length=100, blank=True)),
                ('instance_ip', models.CharField(default=b'', max_length=100, blank=True)),
                ('cluster', models.ForeignKey(to='rmapp.Cluster')),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('user', models.OneToOneField(related_name='profile', primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('rsa_key', models.TextField(default=b'', max_length=1024, blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='credential',
            name='user',
            field=models.ForeignKey(related_name='credentials', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='cluster',
            name='user',
            field=models.ForeignKey(related_name='clusters', to=settings.AUTH_USER_MODEL),
        ),
    ]
