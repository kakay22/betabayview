# Generated by Django 5.1.1 on 2024-10-11 00:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ADMIN', '0006_chatconversation_delete_conversation'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatconversation',
            name='dislikes',
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='chatconversation',
            name='likes',
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
    ]
