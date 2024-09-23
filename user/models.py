from django.db import models
from django.contrib.auth.models import AbstractUser

class UserType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    usertype = models.ForeignKey(UserType, on_delete=models.CASCADE, related_name='users',null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    image = models.ImageField(upload_to="car/images", default="")


    def __str__(self):
        return self.username

