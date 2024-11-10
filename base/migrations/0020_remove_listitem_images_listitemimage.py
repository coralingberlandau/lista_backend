# Generated by Django 5.1.1 on 2024-11-08 09:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0019_alter_grouplist_list_item_alter_grouplist_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='listitem',
            name='images',
        ),
        migrations.CreateModel(
            name='ListItemImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='list_item_images/')),
                ('list_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='base.listitem')),
            ],
        ),
    ]
