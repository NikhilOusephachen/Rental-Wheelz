from django.contrib import admin
from .models import Bill, Order, Driver, DriverAssignment
from .models import Rating

admin.site.register(Bill)
admin.site.register(Order)
admin.site.register(Driver)
admin.site.register(DriverAssignment)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'car', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'car__car_name')
