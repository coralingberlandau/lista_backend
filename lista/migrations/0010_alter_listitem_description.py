# Generated by Django 5.1.1 on 2024-10-27 13:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lista', '0009_listitem_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listitem',
            name='description',
            field=models.JSONField(default=list),
        ),
    ]
