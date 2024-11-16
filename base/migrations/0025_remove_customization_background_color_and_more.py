# Generated by Django 5.1.1 on 2024-11-15 13:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0024_customization'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customization',
            name='background_color',
        ),
        migrations.AddField(
            model_name='customization',
            name='background_image_id',
            field=models.CharField(default='', max_length=20),
        ),
    ]
