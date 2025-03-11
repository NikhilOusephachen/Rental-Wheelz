from django.contrib import admin
from django.utils import timezone
from .models import Bill, Order, Driver, DriverAssignment, Rating

class LeaseExpiringFilter(admin.SimpleListFilter):
    title = 'lease expiring'
    parameter_name = 'lease_expiring'

    def lookups(self, request, model_admin):
        return (
            ('7', 'Next 7 days'),
            ('30', 'Next 30 days'),
        )

    def queryset(self, request, queryset):
        if self.value():
            days = int(self.value())
            return queryset.filter(
                is_lease=True,
                bill__lease_end_date__lte=timezone.now().date() + timezone.timedelta(days=days)
            )

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'car', 'bill_type', 'duration', 'pick_up_date', 'total_rent')
    list_filter = ['is_lease']
    search_fields = ['user__username', 'car__car_name', 'from_loc', 'to_loc']
    
    def bill_type(self, obj):
        return "Lease" if obj.is_lease else "Rental"
    bill_type.short_description = "Type"
    
    def duration(self, obj):
        if obj.is_lease:
            return f"{obj.no_of_months} months"
        return f"{obj.no_of_days} days"
    duration.short_description = "Duration"

def approve_orders(modeladmin, request, queryset):
    queryset.update(is_approved=True)
approve_orders.short_description = "Approve selected orders"

def mark_as_paid(modeladmin, request, queryset):
    queryset.update(payment_status=True)
mark_as_paid.short_description = "Mark selected orders as paid"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'car', 'order_type', 'created_at', 'is_approved', 'payment_status')
    list_filter = [
        'is_approved', 
        'payment_status', 
        'is_lease',
        'created_at',
        LeaseExpiringFilter
    ]
    search_fields = ['user__username', 'car__car_name']
    actions = [approve_orders, mark_as_paid]
    
    def order_type(self, obj):
        return "Lease" if obj.is_lease else "Rental"
    order_type.short_description = "Type"

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['name', 'license_number', 'phone_number', 'is_available']
    list_filter = ['is_available']
    search_fields = ['name', 'license_number', 'phone_number']

@admin.register(DriverAssignment)
class DriverAssignmentAdmin(admin.ModelAdmin):
    list_display = ['order', 'driver', 'assigned_at']
    list_filter = ['assigned_at']
    search_fields = ['order__user__username', 'driver__name']

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'car', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'car__car_name', 'feedback')

# Admin site customization
admin.site.site_header = "Car Rental Administration"
admin.site.site_title = "Car Rental Admin Portal"
admin.site.index_title = "Welcome to Car Rental Admin Portal"
