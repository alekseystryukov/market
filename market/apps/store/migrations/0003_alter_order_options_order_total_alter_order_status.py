# Generated by Django 4.2.7 on 2023-11-09 20:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_product_search_vector_idx'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='order',
            options={'verbose_name': 'Замовлення', 'verbose_name_plural': 'Замовлення'},
        ),
        migrations.AddField(
            model_name='order',
            name='total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Створений'), (1, 'Підтверджений'), (2, 'Відправлений'), (3, 'Отриманий'), (4, 'Відмінений')], default=0),
        ),
    ]
