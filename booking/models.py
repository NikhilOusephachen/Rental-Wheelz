from django.db import models
from myapp.models import Car
from django.conf import settings


class Bill(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    no_of_days = models.PositiveIntegerField(default=0)
    pick_up_date = models.DateField()
    from_loc = models.CharField(max_length=500)
    to_loc = models.CharField(max_length=500)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    total_rent = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    rent_end_date = models.DateField(null=True, blank=True)
    is_lease = models.BooleanField(default=False)
    no_of_months = models.PositiveIntegerField(default=0)
    lease_start_date = models.DateField(null=True, blank=True)
    lease_end_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.car and (self.no_of_days or self.no_of_months):
            if self.is_lease:
                self.total_rent = self.car.lease_price * self.no_of_months
            else:
                self.total_rent = self.car.price * self.no_of_days
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Bill for {self.car} by {self.user} from {self.from_loc} to {self.to_loc} for {self.no_of_days} days"
    


class Order(models.Model):
    is_approved = models.BooleanField(default=False)
    payment_status = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    address = models.CharField(max_length=500, default="")
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    driving_license = models.ImageField(upload_to='license_image/')
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_assigned = models.BooleanField(default=False)
    is_lease = models.BooleanField(default=False)
    lease_terms_accepted = models.BooleanField(default=False)
    advance_paid = models.BooleanField(default=False)
    remaining_months = models.IntegerField(default=0)
    next_payment_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Order for {self.car} by {self.user} from {self.bill}"

class Rating(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="rating")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)  # Rating from 1 to 5
    feedback = models.TextField(blank=True, default="")  # Optional feedback
    created_at = models.DateTimeField(auto_now_add = True)
    def __str__(self):
        return f"Rating: {self.rating} for {self.car} by {self.user}"

    class Meta:
        unique_together = ['order', 'user']  


class Driver(models.Model):
    name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class DriverAssignment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Driver {self.driver.name} assigned to Order #{self.order.id}"