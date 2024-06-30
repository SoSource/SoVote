# Generated by Django 5.0.4 on 2024-06-30 19:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blockchain', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='block',
            name='automated',
        ),
        migrations.RemoveField(
            model_name='block',
            name='script',
        ),
        migrations.RemoveField(
            model_name='validator',
            name='pointerId',
        ),
        migrations.RemoveField(
            model_name='validator',
            name='pointerType',
        ),
        migrations.AddField(
            model_name='block',
            name='Blockchain_obj',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='blockchain.blockchain'),
        ),
        migrations.AddField(
            model_name='block',
            name='blockchainType',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AddField(
            model_name='validator',
            name='blockchainId',
            field=models.CharField(default='0', max_length=50),
        ),
        migrations.AddField(
            model_name='validator',
            name='blockchainType',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AddField(
            model_name='validator',
            name='data',
            field=models.TextField(blank=True, default='[]', null=True),
        ),
    ]