# Generated by Django 4.2.7 on 2023-11-07 20:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'get_latest_by': 'id', 'verbose_name': 'category', 'verbose_name_plural': 'categories'},
        ),
    ]
