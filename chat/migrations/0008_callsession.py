# Generated by Django 5.0.6 on 2024-12-02 18:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0007_alter_message_image'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CallSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('call_type', models.CharField(choices=[('voice', 'Voice Call'), ('video', 'Video Call')], max_length=10)),
                ('status', models.CharField(choices=[('initiated', 'Initiated'), ('connecting', 'Connecting'), ('active', 'Active'), ('ended', 'Ended')], default='initiated', max_length=20)),
                ('start_time', models.DateTimeField(auto_now_add=True)),
                ('end_time', models.DateTimeField(blank=True, null=True)),
                ('duration', models.DurationField(blank=True, null=True)),
                ('initiator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='initiated_calls', to=settings.AUTH_USER_MODEL)),
                ('participants', models.ManyToManyField(related_name='call_sessions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]