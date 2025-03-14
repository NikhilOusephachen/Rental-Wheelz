# Generated by Django 5.0.1 on 2025-02-10 04:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0010_maintenanceprediction'),
    ]

    operations = [
        migrations.RenameField(
            model_name='maintenanceprediction',
            old_name='prediction_date',
            new_name='created_at',
        ),
        migrations.AddField(
            model_name='maintenanceprediction',
            name='accident_history',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='maintenanceprediction',
            name='engine_size',
            field=models.FloatField(default=2000),
        ),
        migrations.AddField(
            model_name='maintenanceprediction',
            name='fuel_efficiency',
            field=models.FloatField(default=15.0),
        ),
        migrations.AddField(
            model_name='maintenanceprediction',
            name='prediction_probability',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='maintenanceprediction',
            name='reported_issues',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='maintenanceprediction',
            name='service_history',
            field=models.IntegerField(default=6),
        ),
        migrations.AddField(
            model_name='maintenanceprediction',
            name='vehicle_age',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='maintenanceprediction',
            name='battery_status',
            field=models.CharField(choices=[('Good', 'Good'), ('Poor', 'Poor')], default='Good', max_length=20),
        ),
        migrations.AlterField(
            model_name='maintenanceprediction',
            name='brake_condition',
            field=models.CharField(choices=[('Good', 'Good'), ('New', 'New'), ('Worn Out', 'Worn Out')], default='Good', max_length=20),
        ),
        migrations.AlterField(
            model_name='maintenanceprediction',
            name='days_since_last_service',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='maintenanceprediction',
            name='fuel_type',
            field=models.CharField(choices=[('Petrol', 'Petrol'), ('Diesel', 'Diesel')], default='Petrol', max_length=20),
        ),
        migrations.AlterField(
            model_name='maintenanceprediction',
            name='insurance_premium',
            field=models.FloatField(default=1000),
        ),
        migrations.AlterField(
            model_name='maintenanceprediction',
            name='maintenance_history',
            field=models.CharField(choices=[('Good', 'Good'), ('Average', 'Average'), ('Poor', 'Poor')], default='Good', max_length=20),
        ),
        migrations.AlterField(
            model_name='maintenanceprediction',
            name='mileage',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='maintenanceprediction',
            name='odometer_reading',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='maintenanceprediction',
            name='owner_type',
            field=models.CharField(choices=[('First', 'First'), ('Second', 'Second'), ('Third', 'Third')], default='First', max_length=20),
        ),
        migrations.AlterField(
            model_name='maintenanceprediction',
            name='prediction_result',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='maintenanceprediction',
            name='tire_condition',
            field=models.CharField(choices=[('Good', 'Good'), ('New', 'New'), ('Worn Out', 'Worn Out')], default='Good', max_length=20),
        ),
        migrations.AlterField(
            model_name='maintenanceprediction',
            name='transmission_type',
            field=models.CharField(choices=[('Automatic', 'Automatic'), ('Manual', 'Manual')], default='Automatic', max_length=20),
        ),
        migrations.AlterField(
            model_name='maintenanceprediction',
            name='vehicle_model',
            field=models.CharField(choices=[('SUV', 'SUV'), ('Truck', 'Truck'), ('Van', 'Van'), ('Car', 'Car'), ('Motorcycle', 'Motorcycle'), ('Bus', 'Bus')], default='Car', max_length=20),
        ),
    ]
