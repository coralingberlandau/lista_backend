# Generated by Django 5.1.1 on 2024-10-06 11:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lista', '0003_remove_documentshare_document_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='List',
            new_name='ListItem',
        ),
        migrations.RenameField(
            model_name='grouplist',
            old_name='list',
            new_name='list_item',
        ),
    ]