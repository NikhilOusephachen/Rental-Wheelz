import hashlib
from django.shortcuts import render, redirect, get_object_or_404
from .models import Driver, DriverAssignment, Order, Bill
from django.db.models import Q
from django.contrib import messages
from myapp.models import Car
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from datetime import timedelta
import razorpay
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime



from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.dateparse import parse_date
from datetime import timedelta
from .models import Car, Bill


# Initialize the Razorpay client
client = razorpay.Client(auth=("rzp_test_i1eV0ftB0HVfyt", "QhoN8KaIJqnCGV7Vc74p0iaK"))



@login_required
def bill(request, id):
    car = get_object_or_404(Car, id=id)
    errors = {}

    if request.method == 'POST':
        no_of_days = request.POST.get('dayss', '')
        pick_up_date = request.POST.get('date', '')
        from_loc = request.POST.get('fl', '')
        to_loc = request.POST.get('tl', '')

        # Validate input for Number of Days
        if not no_of_days:
            errors['no_of_days'] = "Number of days is required."
        else:
            try:
                no_of_days = int(no_of_days)
                if no_of_days < 1:
                    errors['no_of_days'] = "Number of days must be at least 1."
            except ValueError:
                errors['no_of_days'] = "Invalid number of days."

        # Validate input for Pick-up Date
        if not pick_up_date:
            errors['pick_up_date'] = "Pick-up date is required."
        else:
            try:
                pick_up_date = parse_date(pick_up_date)
                if not pick_up_date:
                    raise ValueError
            except ValueError:
                errors['pick_up_date'] = "Invalid date format. Use YYYY-MM-DD."

        # Validate input for From Location (only letters allowed)
        if not from_loc:
            errors['from_loc'] = "From Location is required."
        elif not from_loc.isalpha():
            errors['from_loc'] = "From Location should only contain letters."

        # Validate input for To Location (only letters allowed)
        if not to_loc:
            errors['to_loc'] = "To Location is required."
        elif not to_loc.isalpha():
            errors['to_loc'] = "To Location should only contain letters."

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
def real_bill(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    current_date = datetime.now().strftime("%d-%m-%Y")
    context = {
        'order': order,
    }
    return render(request, 'realbill.html',{'order': order, 'current_date': current_date})


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
        return redirect(reverse('make_payment', kwargs={'amount': int(bill.total_rent)}))
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
    try:
        driver = DriverAssignment.objects.get(order=order)
    except DriverAssignment.DoesNotExist:
        driver = None  # No driver assigned
    if request.method == 'POST':
        # Update the is_assigned field to True 
        order.is_assigned = True
        order.save()

        # Add a success message that will be displayed in the template
        messages.success(request, 'A manager will assign a driver soon.')
        return redirect('order_detail', id=id)
    return render(request, 'order_detail.html', {'order': order, 'driver': driver})


@login_required
def manager_order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    available_drivers = Driver.objects.filter(is_available=True)
    if request.method == 'POST':
        driver_id = request.POST.get('driver_id')
        if driver_id:
            driver = get_object_or_404(Driver, id=driver_id)

            # Create a new DriverAssignment and set the driver
            DriverAssignment.objects.create(order=order, driver=driver)

            # Mark the order as assigned
            order.is_assigned = True
            order.save()

            # Update the driver availability if needed
            driver.is_available = False
            driver.save()

            messages.success(request, f"Driver {
                             driver.name} has been assigned to the order.")
        return redirect('manager_order_details', order_id=order.id)
    return render(request, 'manager/managercarorderdetails.html', {'order': order, 'available_drivers': available_drivers})


@login_required
def manager_car_drivers(request):
    query = request.GET.get('q')  # Get the search query from the URL
    if query:
        # Use Q objects to allow searching in multiple fields
        drivers = Driver.objects.filter(
            Q(name__icontains=query) |
            # Assuming CarBrand has a `name` field
            Q(license_number__icontains=query) |
            Q(phone_number__icontains=query)
        )
    else:
        drivers = Driver.objects.all()
    return render(request, 'manager/manager_drivers.html', {'drivers': drivers})


def manager_driver_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        license_number = request.POST.get('license_number')
        phone_number = request.POST.get('phone_number')
        is_available = request.POST.get('is_available') == 'on'

        # Create and save the new driver
        new_driver = Driver(name=name, license_number=license_number,
                            phone_number=phone_number, is_available=is_available)
        new_driver.save()

        messages.success(request, 'Driver added successfully!')
        # Redirect to a view that lists all drivers
        return redirect('manager_car_drivers')
    return render(request, 'manager/manager_driver_add.html')


@login_required
def manager_driver_edit(request, driver_id):
    driver = get_object_or_404(Driver, id=driver_id)
    if request.method == 'POST':
        # Get data from the form and update driver instance
        driver.name = request.POST.get('name')
        driver.license_number = request.POST.get('license_number')
        driver.phone_number = request.POST.get('phone_number')
        driver.is_available = 'is_available' in request.POST  # Checkbox

        # Save the updated driver
        driver.save()

        # Display success message and redirect
        messages.success(request, 'Driver information updated successfully.')
        return redirect('manager_car_drivers')
    return render(request, 'manager/manager_driver_edit.html', {'driver': driver})


@login_required
def manager_car_driver_delete(request, driver_id):
    if request.method == "POST":
        driver = get_object_or_404(Driver, id=driver_id)
        driver_name = driver.name
        driver.delete()
        messages.success(request, f"The Driver '{
                         driver_name}' has been successfully deleted.")
    return redirect('manager_car_drivers')

@login_required
def make_payment(request, amount):
    if request.method == 'POST':
        # Create an order
        order_data = {
            "amount": int(amount) * 100,  # Amount in paise
            "currency": "INR",
            "receipt": "receipt#1",
            "payment_capture": 1  # Auto capture the payment
        }
        
        try:
            order = client.order.create(data=order_data)
            return JsonResponse({
                'order_id': order['id'],
                'amount': order['amount'],
                'currency': order['currency'],
                'status': 'success'
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return render(request, 'payment.html', {'amount': amount})

@login_required
def payment_success(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        payment_id = data.get('payment_id')
        order_id = data.get('order_id')
        signature = data.get('signature')

        # Here, you can verify the payment signature or perform other necessary steps.
        # Example: verify the signature (optional)
        # Note: Razorpay provides a utility function to verify the signature using `razorpay_client.utility.verify_payment_signature()`

        # For simplicity, assuming payment is successful
        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'failure'}, status=400)

import json

# @csrf_exempt
# @login_required
# def verify_payment(request):
#     if request.method == 'POST':
#         response = request.POST
#         razorpay_order_id = response.get('razorpay_order_id')
#         razorpay_payment_id = response.get('razorpay_payment_id')
#         razorpay_signature = response.get('razorpay_signature')
    

#         # Verify the payment signature
#         generated_signature = f"{razorpay_order_id}|{razorpay_payment_id}"
#         expected_signature = hashlib.sha256(generated_signature.encode()).hexdigest()

#         if expected_signature == razorpay_signature:
#             # Payment is verified
#             # You can update your order status in the database here
#             return JsonResponse({'status': 'Payment verified'})
        
#         return JsonResponse({'status': 'Payment verification failed'}, status=400)

#     return JsonResponse({'status': 'Invalid request'}, status=400)