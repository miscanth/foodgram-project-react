# Generated by Django 3.2.3 on 2023-07-16 15:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_user_is_subscribed'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='is_subscribed',
        ),
    ]
