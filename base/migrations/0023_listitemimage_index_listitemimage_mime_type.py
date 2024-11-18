# Generated by Django 5.1.1 on 2024-11-12 19:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0022_remove_listitem_description_listitem_items_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='listitemimage',
            name='index',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='listitemimage',
            name='mime_type',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]