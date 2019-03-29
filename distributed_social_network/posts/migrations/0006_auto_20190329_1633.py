# Generated by Django 2.1.7 on 2019-03-29 16:33

from django.db import migrations, models
import posts.utils


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_auto_20190327_0252'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='content_type',
            field=models.CharField(choices=[('MKD', 'text/markdown'), ('TXT', 'text/plain'), ('APP', 'application/base64'), ('PNG', 'image/png;base64'), ('JPG', 'image/jpeg;base64')], default=posts.utils.ContentType('TXT'), max_length=3),
        ),
        migrations.AlterField(
            model_name='post',
            name='content_type',
            field=models.CharField(choices=[('MKD', 'text/markdown'), ('TXT', 'text/plain'), ('APP', 'application/base64'), ('PNG', 'image/png;base64'), ('JPG', 'image/jpeg;base64')], default=posts.utils.ContentType('TXT'), max_length=3),
        ),
    ]
