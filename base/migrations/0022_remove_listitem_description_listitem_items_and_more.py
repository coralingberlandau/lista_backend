# Generated by Django 5.1.1 on 2024-11-10 08:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0021_alter_listitemimage_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='listitem',
            name='description',
        ),
        migrations.AddField(
            model_name='listitem',
            name='items',
            field=models.TextField(default='No items'),
        ),
        migrations.AlterField(
            model_name='listitem',
            name='title',
            field=models.CharField(default='No items', max_length=255),
        ),
    ]