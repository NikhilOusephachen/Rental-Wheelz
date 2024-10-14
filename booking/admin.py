from django.contrib import admin
from .models import Bill, Order, Driver, DriverAssignment

admin.site.register(Bill)
admin.site.register(Order)
admin.site.register(Driver)
admin.site.register(DriverAssignment)


