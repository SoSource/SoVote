# Generated by Django 5.0.4 on 2024-06-26 22:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sonet',
            name='LogoLink',
            field=models.CharField(default='/static/img/default_logo.png', max_length=200),
        ),
    ]
