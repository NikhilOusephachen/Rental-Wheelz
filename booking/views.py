from django.shortcuts import render, redirect, get_object_or_404
from .models import Order, Bill
from django.contrib import messages
from myapp.models import Car
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from datetime import datetime, timedelta


from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.dateparse import parse_date
from datetime import timedelta
from .models import Car, Bill

@login_required
def bill(request, id):
    car = get_object_or_404(Car, id=id)
    errors = {}

    if request.method == 'POST':
        no_of_days = request.POST.get('dayss', '')
        pick_up_date = request.POST.get('date', '')
        from_loc = request.POST.get('fl', '')
        to_loc = request.POST.get('tl', '')

        # Validate input
        if not no_of_days:
            errors['no_of_days'] = "Number of days is required."
        else:
            try:
                no_of_days = int(no_of_days)
            except ValueError:
                errors['no_of_days'] = "Invalid number of days."

        if not pick_up_date:
            errors['pick_up_date'] = "Pick-up date is required."
        else:
            try:
                pick_up_date = parse_date(pick_up_date)
                if not pick_up_date:
                    raise ValueError
            except ValueError:
                errors['pick_up_date'] = "Invalid date format. Use YYYY-MM-DD."

        # If there are no errors, proceed with the bill creation
        if not errors:
            rent_end_date = pick_up_date + timedelta(days=no_of_days)
            bill = Bill(
                car=car,
                no_of_days=no_of_days,
                pick_up_date=pick_up_date,
                from_loc=from_loc,
                to_loc=to_loc,
                user=request.user,
                rent_end_date=rent_end_date
            )
            bill.save()
            return redirect(reverse('order', kwargs={'bill_id': bill.id}))
    
    return render(request, 'bill.html', {'car': car, 'errors': errors})


@login_required
def order(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    if request.method == "POST":
        address = request.POST.get('address', '')
        driving_license = request.POST.get('driving_license', '')
        order = Order(user=bill.user, address=address, car=bill.car,
                      driving_license=driving_license, bill=bill)
        order.save()
        messages.success(request, 'Order is placed successfully.')
        return redirect('home')
    else:
        print("error")
        return render(request, 'orders.html', {'bill': bill})

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'order_list.html', {'orders': orders})

@login_required
def order_detail(request, id):
    order = get_object_or_404(Order, id=id)
    return render(request, 'order_detail.html', {'order': order})