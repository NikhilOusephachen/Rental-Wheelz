from django.contrib import admin
from .models import Brand, CarModel, CarBodyType, CarColor, CarFuel, CarTransmission, Car, CarTracking, CarLocation

admin.site.register(Car)
admin.site.register(Brand)
admin.site.register(CarModel)
admin.site.register(CarBodyType)
admin.site.register(CarColor)
admin.site.register(CarFuel)
admin.site.register(CarTransmission)
admin.site.register(CarTracking)
admin.site.register(CarLocation)
