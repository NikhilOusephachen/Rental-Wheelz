# Generated by Django 5.0.1 on 2024-10-04 14:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0002_contact'),
    ]

    operations = [
        migrations.AddField(
            model_name='car',
            name='insurance_file',
            field=models.FileField(blank=True, upload_to='car/insurance_files'),
        ),
        migrations.AddField(
            model_name='car',
            name='insurance_number',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
    ]