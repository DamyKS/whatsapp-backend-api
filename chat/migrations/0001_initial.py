# Generated by Django 5.0.6 on 2024-06-24 21:42

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('sent', models.BooleanField(default=False)),
                ('delivered', models.BooleanField(default=False)),
                ('read', models.BooleanField(default=False)),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Chat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chat_name', models.CharField(blank=True, max_length=30)),
                ('participants', models.ManyToManyField(related_name='participates_in', to=settings.AUTH_USER_MODEL)),
                ('messages', models.ManyToManyField(blank=True, related_name='messages', to='chat.message')),
            ],
        ),
    ]