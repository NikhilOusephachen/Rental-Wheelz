from email.policy import default
from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.validators import MinValueValidator
from django.core.validators import MaxValueValidator
from django.conf import settings
from datetime import datetime


class Brand(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class CarModel(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    model_name = models.CharField(max_length=100)

    def __str__(self):
        return self.model_name


class CarFuel(models.Model):
    fuel = models.CharField(max_length=100)

    def __str__(self):
        return self.fuel


class CarTransmission(models.Model):
    transmission = models.CharField(max_length=100)

    def __str__(self):
        return self.transmission


class CarBodyType(models.Model):
    body_type = models.CharField(max_length=100)

    def __str__(self):
        return self.body_type


class CarColor(models.Model):
    color = models.CharField(max_length=100)

    def __str__(self):
        return self.color


class CarLocation(models.Model):
    car = models.OneToOneField("Car", on_delete=models.CASCADE, related_name="location")
    latitude = models.FloatField()
    longitude = models.FloatField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"Location for {self.car.car_name} at ({self.latitude}, {self.longitude})"
        )


class CarTracking(models.Model):
    car = models.OneToOneField("Car", on_delete=models.CASCADE, related_name="tracking")
    is_enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"Tracking for {self.car.car_name} is {'enabled' if self.is_enabled else 'disabled'}"


class Car(models.Model):
    car_name = models.CharField(max_length=30, default="")
    car_desc = models.CharField(max_length=300, default="")
    car_brand = models.ForeignKey(Brand, on_delete=models.CASCADE, default=1)
    car_model = models.ForeignKey(CarModel, on_delete=models.CASCADE, default=1)
    car_color = models.ForeignKey(CarColor, on_delete=models.CASCADE, default=1)
    car_fuel = models.ForeignKey(CarFuel, on_delete=models.CASCADE, default=1)
    transmission = models.ForeignKey(
        CarTransmission, on_delete=models.CASCADE, default=1
    )
    year = models.IntegerField()
    available = models.BooleanField(default=False)
    price = models.IntegerField(default=0)
    image = models.ImageField(upload_to="car/images", default="")
    image_360 = models.ImageField(upload_to="car/images_360", null=True, blank=True, 
                                help_text="Upload a 360-degree equirectangular image")
    insurance_number = models.CharField(max_length=50, default="", blank=True)
    insurance_file = models.FileField(upload_to="car/insurance_files", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_available_for_lease = models.BooleanField(default=False)
    lease_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    minimum_lease_months = models.PositiveIntegerField(default=1)
    maximum_lease_months = models.PositiveIntegerField(default=12)

    def __str__(self):
        return self.car_name

    def is_available_for_period(self, start_date, end_date):
        """Check if car is available for a specific period"""
        from booking.models import Order
        
        # Convert strings to dates if necessary
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # First check if there's any approved lease order for this car
        lease_exists = Order.objects.filter(
            car=self,
            is_approved=True,
            bill__is_lease=True
        ).exists()

        # If there's an approved lease, car is not available for any dates
        if lease_exists:
            return False

        # If no lease, check for rental date conflicts
        rental_conflicts = Order.objects.filter(
            car=self,
            is_approved=True,
            bill__is_lease=False,
            bill__pick_up_date__lte=end_date,
            bill__rent_end_date__gte=start_date
        ).exists()

        return not rental_conflicts


class Contact(models.Model):
    message = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150, default="")
    email = models.CharField(max_length=150, default="")
    phone_number = models.CharField(max_length=15, default="")
    message = models.TextField(max_length=500, default="")

    def __str__(self):
        return self.name


class MaintenancePrediction(models.Model):
    car = models.ForeignKey('Car', on_delete=models.CASCADE)
    mileage = models.FloatField(validators=[MinValueValidator(0)])
    odometer_reading = models.FloatField(validators=[MinValueValidator(0)])
    insurance_premium = models.FloatField(default=1000)
    days_since_last_service = models.IntegerField(validators=[MinValueValidator(0)])
    engine_size = models.FloatField(validators=[MinValueValidator(0)])
    fuel_efficiency = models.FloatField(default=15.0)
    vehicle_age = models.IntegerField(default=0)
    service_history = models.IntegerField(validators=[MinValueValidator(0)])
    accident_history = models.IntegerField(default=0)
    reported_issues = models.IntegerField(default=0)
    maintenance_history = models.CharField(
        max_length=20,
        choices=[('Good', 'Good'), ('Average', 'Average'), ('Poor', 'Poor')],
        default='Good'
    )
    battery_status = models.CharField(
        max_length=20, 
        choices=[('Good', 'Good'), ('Poor', 'Poor')],
        default='Good'
    )
    fuel_type = models.CharField(
        max_length=20,
        choices=[('Petrol', 'Petrol'), ('Diesel', 'Diesel')],
        default='Petrol'
    )
    transmission_type = models.CharField(
        max_length=20,
        choices=[('Automatic', 'Automatic'), ('Manual', 'Manual')],
        default='Automatic'
    )
    vehicle_model = models.CharField(
        max_length=20,
        choices=[
            ('SUV', 'SUV'), ('Truck', 'Truck'), ('Van', 'Van'),
            ('Car', 'Car'), ('Motorcycle', 'Motorcycle'), ('Bus', 'Bus')
        ],
        default='Car'
    )
    owner_type = models.CharField(
        max_length=20, 
        choices=[('First', 'First'), ('Second', 'Second'), ('Third', 'Third')],
        default='First'
    )
    tire_condition = models.CharField(
        max_length=20,
        choices=[('Good', 'Good'), ('New', 'New'), ('Worn Out', 'Worn Out')],
        default='Good'
    )
    brake_condition = models.CharField(
        max_length=20,
        choices=[('Good', 'Good'), ('New', 'New'), ('Worn Out', 'Worn Out')],
        default='Good'
    )
    prediction_result = models.BooleanField(default=False)
    prediction_probability = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.car.car_name} - {self.created_at.date()}"

    class Meta:
        ordering = ['-created_at']

class ChatMessage(models.Model):
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='customer_messages', on_delete=models.CASCADE)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='manager_messages', on_delete=models.CASCADE)
    message = models.TextField()
    sent_by_customer = models.BooleanField(default=True)  # True if sent by customer, False if by manager
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        sender = self.customer if self.sent_by_customer else self.manager
        receiver = self.manager if self.sent_by_customer else self.customer
        return f"{sender} to {receiver}: {self.message[:50]}"
