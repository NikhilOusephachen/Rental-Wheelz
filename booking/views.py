import json
import hashlib
from django.shortcuts import render, redirect, get_object_or_404

from user.models import CustomUser
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
from django.http import HttpResponseForbidden
from dateutil.relativedelta import relativedelta


from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.dateparse import parse_date
from datetime import timedelta
from .models import Car, Bill
from .models import Rating


# Initialize the Razorpay client
client = razorpay.Client(
    auth=("rzp_test_i1eV0ftB0HVfyt", "QhoN8KaIJqnCGV7Vc74p0iaK"))


@login_required
def bill(request, id):
    car = get_object_or_404(Car, id=id)
    booking_type = request.GET.get('type', 'rent')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    errors = {}

    # Check availability if dates are provided
    is_available = True
    if start_date and end_date:
        is_available = car.is_available_for_period(start_date, end_date)
        print(f"Car {car.car_name} availability for {start_date} to {end_date}: {is_available}")

    if request.method == 'POST':
        is_lease = request.POST.get('booking_type') == 'lease'
        time_period = request.POST.get('months' if is_lease else 'dayss', '')
        start_date = request.POST.get('date', '')
        from_loc = request.POST.get('fl', '')
        to_loc = request.POST.get('tl', '')

        # Validate inputs
        if not time_period:
            errors['time_period'] = f"Number of {'months' if is_lease else 'days'} is required."
        else:
            try:
                time_period = int(time_period)
                if time_period < 1:
                    errors['time_period'] = f"Number of {'months' if is_lease else 'days'} must be at least 1."
                if is_lease:
                    if time_period < car.minimum_lease_months or time_period > car.maximum_lease_months:
                        errors['time_period'] = f"Lease period must be between {car.minimum_lease_months} and {car.maximum_lease_months} months."
            except ValueError:
                errors['time_period'] = f"Invalid number of {'months' if is_lease else 'days'}."

        # Additional validation logic...

        if not errors:
            # Convert start_date string to datetime
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            
            # Calculate end date based on lease or rental
            if is_lease:
                # For lease: add months
                end_date = start_date_obj + relativedelta(months=int(time_period))
            else:
                # For rental: add days
                end_date = start_date_obj + timedelta(days=int(time_period))

            bill = Bill.objects.create(
                car=car,
                user=request.user,
                is_lease=is_lease,
                no_of_days=0 if is_lease else time_period,
                no_of_months=time_period if is_lease else 0,
                pick_up_date=start_date,
                rent_end_date=end_date,
                from_loc=from_loc,
                to_loc=to_loc,
                total_rent=car.lease_price * int(time_period) if is_lease else car.price * int(time_period)
            )

            # Redirect to orders page
            return redirect('order', bill_id=bill.id)

    context = {
        'car': car,
        'errors': errors,
        'booking_type': booking_type,
        'today_date': datetime.now().date().isoformat(),
        'is_available': is_available,
        'start_date': start_date,
        'end_date': end_date
    }
    return render(request, 'bill.html', context)


@login_required
def real_bill(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    current_date = datetime.now().strftime("%d-%m-%Y")
    context = {
        'order': order,
    }
    return render(request, 'realbill.html', {'order': order, 'current_date': current_date})


@login_required
def order(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id)
    
    # Calculate payment amount based on whether it's lease or rental
    if bill.is_lease:
        # For lease: Only charge first month's rent as advance
        order_amount = int(bill.car.lease_price * 100)  # Convert to paise
    else:
        # For rental: Charge full amount
        order_amount = int(bill.total_rent * 100)
    
    # Create Razorpay order
    razorpay_order = client.order.create({
        "amount": order_amount,
        "currency": "INR",
        "payment_capture": "1",
        "notes": {
            "is_lease": str(bill.is_lease),
            "total_months": str(bill.no_of_months) if bill.is_lease else "0"
        }
    })

    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        address = request.POST.get('address')  # Get address from form

        try:
            # Verify payment signature
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': razorpay_signature
            })

            # Create order with appropriate payment details
            order = Order.objects.create(
                user=request.user,
                car=bill.car,
                bill=bill,
                is_lease=bill.is_lease,
                payment_status=True,
                advance_paid=True if bill.is_lease else False,
                remaining_months=bill.no_of_months - 1 if bill.is_lease else 0,
                address=address  # Save the address here
            )

            messages.success(request, 'First month payment successful!' if bill.is_lease else 'Payment successful!')
            return redirect('vehicles')

        except Exception as e:
            messages.error(request, f'Payment failed: {str(e)}')
            return redirect('view_order')

    context = {
        'bill': bill,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_key': "rzp_test_i1eV0ftB0HVfyt",
        'amount': order_amount,
        'is_lease': bill.is_lease,
        'monthly_amount': bill.car.lease_price if bill.is_lease else None,
        'total_months': bill.no_of_months if bill.is_lease else None
    }
    
    return render(request, 'orders.html', context)


@login_required
def order_list(request):
    # Fetch all orders for the logged-in user
    orders = Order.objects.filter(user=request.user)

    if request.method == "POST":
        # Handle payment verification and status update
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        order_id = request.POST.get('order_id')
        bill_id = request.POST.get('bill_id')

        if razorpay_payment_id:
            try:
                # Verify the payment signature to ensure the payment is valid
                params_dict = {
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature
                }
                client.utility.verify_payment_signature(params_dict)

                # Update the order payment status
                order = get_object_or_404(Order, id=order_id)
                order.payment_status = True
                order.save()

                messages.success(
                    request, 'Payment successful and order has been updated.')
            except razorpay.errors.SignatureVerificationError:
                messages.error(
                    request, 'Payment verification failed. Please try again.')
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")

        # Redirect to the order list after processing the payment
        return redirect('view_order')

    # Razorpay Order Creation (for unpaid orders)
    # Select the first unpaid order (for simplicity)
    unpaid_order = orders.filter(payment_status=False).first()
    if unpaid_order:
        bill = unpaid_order.bill

        # Create a new Razorpay order if there's an unpaid order
        razorpay_order = client.order.create({
            "amount": int(bill.total_rent * 100),  # Amount in paise
            "currency": "INR",
            "payment_capture": "1"
        })

        context = {
            'orders': orders,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key': "rzp_test_i1eV0ftB0HVfyt",
            'amount_in_paise': int(bill.total_rent * 100),
            'bill': bill
        }
    else:
        # If no unpaid orders, just render the orders
        context = {
            'orders': orders,
        }

    return render(request, 'order_list.html', context)


@login_required
def order_detail(request, id):
    order = get_object_or_404(Order, id=id)
    existing_rating = None
    
    # Check for assigned driver
    try:
        driver = DriverAssignment.objects.get(order=order)
    except DriverAssignment.DoesNotExist:
        driver = None

    if request.method == "POST" and not order.is_lease:
        if not order.is_assigned:
            # Mark for manager assignment instead of direct driver assignment
            order.is_assigned = True
            order.save()
            messages.success(request, "A manager will assign a driver soon.")
        return redirect('order_detail', id=id)

    # Get existing rating
    existing_rating = Rating.objects.filter(order=order, user=request.user).first()

    context = {
        'order': order,
        'driver': driver,
        'existing_rating': existing_rating
    }
    return render(request, 'order_detail.html', context)


@login_required
def manager_order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    available_drivers = Driver.objects.filter(is_available=True)
    
    # Only process driver assignment for rental orders (not lease orders)
    if request.method == 'POST' and not order.is_lease:
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

            messages.success(request, f"Driver {driver.name} has been assigned to the order.")
        return redirect('manager_order_details', order_id=order.id)
    
    context = {
        'order': order, 
        'available_drivers': available_drivers
    }
    return render(request, 'manager/managercarorderdetails.html', context)


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
        name = request.POST.get('name', '')
        license_number = request.POST.get('license_number', '')
        phone_number = request.POST.get('phone_number', '')
        is_available = request.POST.get('is_available') == 'on'
        
        # Initialize context with form data
        context = {
            'name': name,
            'license_number': license_number,
            'phone_number': phone_number,
            'is_available': is_available,
            'errors': {}
        }
        
        is_valid = True
        
        # Name validation
        if not name or name.isspace():
            context['errors']['name'] = 'Name is required'
            is_valid = False
        elif not all(char.isalpha() or char.isspace() for char in name.strip()):
            context['errors']['name'] = 'Name should only contain letters and spaces'
            is_valid = False
        elif len(name.strip()) < 3:
            context['errors']['name'] = 'Name should be at least 3 characters long'
            is_valid = False
            
        # License number validation
        if not license_number or license_number.isspace():
            context['errors']['license_number'] = 'License number is required'
            is_valid = False
        elif len(license_number.strip()) < 8 or len(license_number.strip()) > 15:
            context['errors']['license_number'] = 'License number should be between 8 and 15 characters'
            is_valid = False
        elif Driver.objects.filter(license_number=license_number.strip()).exists():
            context['errors']['license_number'] = 'This license number is already registered'
            is_valid = False
            
        # Phone number validation
        if not phone_number or phone_number.isspace():
            context['errors']['phone_number'] = 'Phone number is required'
            is_valid = False
        elif not phone_number.strip().isdigit():
            context['errors']['phone_number'] = 'Phone number should only contain digits'
            is_valid = False
        elif len(phone_number.strip()) != 10:
            context['errors']['phone_number'] = 'Phone number should be exactly 10 digits'
            is_valid = False
        elif Driver.objects.filter(phone_number=phone_number.strip()).exists():
            context['errors']['phone_number'] = 'This phone number is already registered'
            is_valid = False

        if not is_valid:
            messages.error(request, 'Please correct the errors below.')
            return render(request, 'manager/manager_driver_add.html', context)

        try:
            # Create and save the new driver if validation passes
            new_driver = Driver(
                name=name.strip(),
                license_number=license_number.strip(),
                phone_number=phone_number.strip(),
                is_available=is_available
            )
            new_driver.save()
            messages.success(request, 'Driver added successfully!')
            return redirect('manager_car_drivers')
        except Exception as e:
            messages.error(request, f'Error adding driver: {str(e)}')
            return render(request, 'manager/manager_driver_add.html', context)

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
        messages.success(request, f"The Driver '{driver_name}' has been successfully deleted.")
    return redirect('manager_car_drivers')

@login_required
def create_rating(request, car_id, order_id):
    car = get_object_or_404(Car, id=car_id)
    ordered = get_object_or_404(Order, id=order_id, user=request.user)

    # Check if the user has placed an order for this car
    has_ordered = Order.objects.filter(user=request.user, car=car).exists()
    if not has_ordered:
        return HttpResponseForbidden("You cannot rate this car because you haven't rented it.")

    # Check if a rating already exists for this order and user
    existing_rating = Rating.objects.filter(order=ordered, user=request.user).first()

    if request.method == "POST":
        rating_value = request.POST.get("rating")
        feedback_text = request.POST.get("feedback")

        # Validate the rating value
        if rating_value and 1 <= int(rating_value) <= 5:
            if existing_rating:
                # Update the existing rating
                existing_rating.rating = rating_value
                existing_rating.feedback = feedback_text
                existing_rating.save()
                messages.success(request, "Your rating has been updated successfully.")
            else:
                # Create a new rating
                Rating.objects.create(
                    order=ordered,
                    user=request.user,
                    car=car,
                    rating=rating_value,
                    feedback=feedback_text,
                )
                messages.success(request, "Your rating has been submitted successfully.")

            return redirect("order_detail", id=order_id)  # Redirect to the order details page

    context = {
        "car": car,
        "existing_rating": existing_rating,
    }
    return render(request, "create_rating.html", context)


