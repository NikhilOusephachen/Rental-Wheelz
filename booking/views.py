from django.shortcuts import render, redirect, get_object_or_404
from .models import Order, Bill
from django.contrib import messages
from myapp.models import Car
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from datetime import datetime, timedelta


@login_required
def bill(request, id):
    car = get_object_or_404(Car, id=id)

    if request.method == 'POST':
        no_of_days = request.POST.get('dayss', '')
        pick_up_date = request.POST.get('date', '')
        from_loc = request.POST.get('fl', '')
        to_loc = request.POST.get('tl', '')
        if not no_of_days or not pick_up_date:
            return HttpResponse("Error: Missing required fields", status=400)
        try:
            # Convert no_of_days to integer
            no_of_days = int(no_of_days)
        except ValueError:
            return HttpResponse("Error: Invalid number of days", status=400)

        try:
            # Convert pick_up_date to a date object
            pick_up_date = datetime.strptime(
                pick_up_date, '%Y-%m-%d').date()
        except ValueError:
            return HttpResponse("Error: Invalid date format", status=400)

        # Calculate rent_end_date
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
    return render(request, 'bill.html', {'car': car})

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
