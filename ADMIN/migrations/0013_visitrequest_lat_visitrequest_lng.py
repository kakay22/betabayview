# Generated by Django 5.1.1 on 2024-11-01 06:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ADMIN', '0012_propertymodel_property_property_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='visitrequest',
            name='lat',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='visitrequest',
            name='lng',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
    ]