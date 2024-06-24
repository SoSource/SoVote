# Generated by Django 5.0.4 on 2024-06-24 17:28

import django.contrib.auth.models
import django.contrib.auth.validators
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('id', models.CharField(default='0', max_length=50, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(blank=True, null=True)),
                ('signature', models.CharField(default='0', max_length=200)),
                ('publicKey', models.CharField(default='0', max_length=200)),
                ('display_name', models.CharField(blank=True, default='0', max_length=50, null=True)),
                ('must_rename', models.BooleanField(default=False)),
                ('first_name', models.CharField(blank=True, max_length=50, null=True)),
                ('last_name', models.CharField(blank=True, max_length=50, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('slug', models.SlugField(unique=True)),
                ('appToken', models.CharField(blank=True, default='', max_length=500, null=True)),
                ('region_set_date', models.DateTimeField(blank=True, null=True)),
                ('interest_array', models.TextField(blank=True, default='[]', null=True)),
                ('follow_post_id_array', models.TextField(blank=True, default='[]', null=True)),
                ('follow_topic_array', models.TextField(blank=True, default='[]', null=True)),
                ('receiveNotifications', models.BooleanField(default=True)),
                ('isVerified', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['created'],
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Interaction',
            fields=[
                ('id', models.CharField(default='0', max_length=50, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True, null=True)),
                ('pointerId', models.CharField(default='0', max_length=50)),
                ('pointerType', models.CharField(default='0', max_length=50)),
                ('score', models.IntegerField(default=0)),
                ('match', models.IntegerField(blank=True, default=None, null=True)),
                ('shared_keywords_added', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('blockchainId', models.CharField(default='', max_length=50)),
                ('locked_to_chain', models.BooleanField(default=False)),
                ('id', models.CharField(default='0', max_length=50, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(blank=True, null=True)),
                ('publicKey', models.CharField(default='0', max_length=200)),
                ('signature', models.CharField(default='0', max_length=200)),
                ('modelVersion', models.CharField(default='v1', max_length=50)),
                ('title', models.CharField(blank=True, default='', max_length=400, null=True)),
                ('link', models.CharField(blank=True, default='', max_length=500, null=True)),
                ('new', models.BooleanField(default=True)),
                ('pointerId', models.CharField(default='', max_length=50)),
                ('pointerType', models.CharField(default='', max_length=50)),
            ],
            options={
                'ordering': ['-created', '-id'],
            },
        ),
        migrations.CreateModel(
            name='SavePost',
            fields=[
                ('id', models.CharField(default='0', max_length=50, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('publicKey', models.CharField(default='0', max_length=200)),
                ('signature', models.CharField(default='0', max_length=200)),
                ('postId', models.CharField(default='0', max_length=50)),
                ('saved', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Sonet',
            fields=[
                ('id', models.CharField(default='0', max_length=50, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(blank=True, null=True)),
                ('title', models.CharField(default='x', max_length=200)),
                ('subtitle', models.CharField(blank=True, default='', max_length=200, null=True)),
                ('LogoLink', models.CharField(default='/static/img/logo_grey.png', max_length=200)),
                ('coin_name', models.CharField(default='token', max_length=200)),
                ('coin_name_plural', models.CharField(default='tokens', max_length=200)),
                ('description', models.CharField(blank=True, default='', max_length=2000, null=True)),
                ('publicKey', models.CharField(default='0', max_length=200)),
                ('signature', models.CharField(default='0', max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('blockchainId', models.CharField(default='', max_length=50)),
                ('id', models.CharField(default='0', max_length=50, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(blank=True, null=True)),
                ('publicKey', models.CharField(default='0', max_length=200)),
                ('signature', models.CharField(default='0', max_length=200)),
                ('modelVersion', models.CharField(default='v1', max_length=50)),
                ('receiverChainId', models.CharField(default='0', max_length=50)),
                ('locked_to_chain', models.BooleanField(default=False)),
                ('SoDo_value', models.CharField(default='0', max_length=1000000)),
            ],
            options={
                'ordering': ['-created', 'id'],
            },
        ),
        migrations.CreateModel(
            name='UserPubKey',
            fields=[
                ('blockchainId', models.CharField(default='', max_length=50)),
                ('locked_to_chain', models.BooleanField(default=False)),
                ('id', models.CharField(default='0', max_length=50, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(blank=True, null=True)),
                ('publicKey', models.CharField(default='0', max_length=200)),
                ('signature', models.CharField(default='0', max_length=200)),
                ('modelVersion', models.CharField(default='v1', max_length=50)),
                ('keyType', models.CharField(default='password', max_length=50)),
            ],
            options={
                'ordering': ['-created', 'id'],
            },
        ),
        migrations.CreateModel(
            name='UserVote',
            fields=[
                ('blockchainId', models.CharField(default='', max_length=50)),
                ('locked_to_chain', models.BooleanField(default=False)),
                ('id', models.CharField(default='0', max_length=50, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(blank=True, null=True)),
                ('publicKey', models.CharField(default='0', max_length=200)),
                ('signature', models.CharField(default='0', max_length=200)),
                ('postId', models.CharField(default='0', max_length=50)),
                ('vote', models.CharField(blank=True, default='none', max_length=20, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Verification',
            fields=[
                ('blockchainId', models.CharField(default='', max_length=50)),
                ('locked_to_chain', models.BooleanField(default=False)),
                ('id', models.CharField(default='0', max_length=50, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(blank=True, null=True)),
                ('publicKey', models.CharField(default='0', max_length=200)),
                ('signature', models.CharField(default='0', max_length=200)),
                ('modelVersion', models.CharField(default='v1', max_length=50)),
                ('pointerId', models.CharField(default='0', max_length=50)),
                ('isVerified', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-created', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('blockchainId', models.CharField(default='', max_length=50)),
                ('locked_to_chain', models.BooleanField(default=False)),
                ('id', models.CharField(default='0', max_length=50, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(blank=True, null=True)),
                ('publicKey', models.CharField(default='0', max_length=200)),
                ('signature', models.CharField(default='0', max_length=200)),
                ('modelVersion', models.CharField(default='v1', max_length=50)),
                ('pointerId', models.CharField(default='0', max_length=50)),
                ('coins', models.CharField(default='0', max_length=1000000)),
            ],
            options={
                'ordering': ['-created', 'id'],
            },
        ),
    ]
