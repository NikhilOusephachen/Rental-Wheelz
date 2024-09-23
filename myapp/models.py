from email.policy import default
from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.validators import MinValueValidator
from django.core.validators import MaxValueValidator


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


class Car(models.Model):
    car_name = models.CharField(max_length=30, default="")
    car_desc = models.CharField(max_length=300, default="")
    car_brand = models.ForeignKey(Brand, on_delete=models.CASCADE, default=1)
    car_model = models.ForeignKey(
        CarModel, on_delete=models.CASCADE, default=1)
    car_color = models.ForeignKey(
        CarColor, on_delete=models.CASCADE, default=1)
    car_fuel = models.ForeignKey(CarFuel, on_delete=models.CASCADE, default=1)
    transmission = models.ForeignKey(
        CarTransmission, on_delete=models.CASCADE, default=1)
    year = models.IntegerField()
    available = models.BooleanField(default=False)
    price = models.IntegerField(default=0)
    image = models.ImageField(upload_to="car/images", default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.car_name


class Contact(models.Model):
    message = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150, default="")
    email = models.CharField(max_length=150, default="")
    phone_number = models.CharField(max_length=15, default="")
    message = models.TextField(max_length=500, default="")

    def __str__(self):
        return self.name
