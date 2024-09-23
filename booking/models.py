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

    def save(self, *args, **kwargs):
        if self.car and self.no_of_days:
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

    def __str__(self):
        return f"Order for {self.car} by {self.user} from {self.bill}"
