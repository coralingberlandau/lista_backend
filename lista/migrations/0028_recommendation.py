# Generated by Django 5.1.1 on 2024-11-18 15:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lista', '0027_userface'),
    ]

    operations = [
        migrations.CreateModel(
            name='Recommendation',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                 primary_key=True, serialize=False, verbose_name='ID')),
                ('recommended_items', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('list_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                 related_name='recommendations', to='lista.listitem')),
            ],
        ),
    ]
