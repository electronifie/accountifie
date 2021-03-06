# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-17 03:34


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('street_number', models.CharField(blank=True, max_length=20)),
                ('route', models.CharField(blank=True, max_length=100)),
                ('postal_code', models.CharField(blank=True, max_length=10)),
                ('raw', models.CharField(max_length=200)),
                ('formatted', models.CharField(blank=True, max_length=200)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Addresses',
                'db_table': 'address_address',
                'ordering': ('locality', 'route', 'street_number'),
            },
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=70, unique=True)),
                ('code', models.CharField(blank=True, max_length=5)),
            ],
            options={
                'verbose_name_plural': 'Countries',
                'db_table': 'address_country',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Locality',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=165)),
            ],
            options={
                'verbose_name_plural': 'Localities',
                'db_table': 'address_locality',
                'ordering': ('state', 'name'),
            },
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=165)),
                ('code', models.CharField(blank=True, max_length=3)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='states', to='address.Country')),
            ],
            options={
                'db_table': 'address_state',
                'ordering': ('country', 'name'),
            },
        ),
        migrations.AddField(
            model_name='locality',
            name='state',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='localities', to='address.State'),
        ),
        migrations.AddField(
            model_name='address',
            name='locality',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to='address.Locality'),
        ),
        migrations.AlterUniqueTogether(
            name='state',
            unique_together=set([('name', 'country')]),
        ),
        migrations.AlterUniqueTogether(
            name='locality',
            unique_together=set([('name', 'state')]),
        ),
    ]
