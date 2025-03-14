from django.contrib import messages
from booking.models import Rating, Order
from .models import Car, CarColor, CarModel, Brand, CarFuel
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from .models import *
from django.db.models import Q,Avg
from django.contrib.auth.decorators import login_required
from user.models import CustomUser
from .models import ChatMessage
from django.http import JsonResponse
from datetime import datetime, timezone, date

def index(request):
    if request.user.is_authenticated:
        # Replace 'vehicles' with the name of your URL pattern
        return redirect('vehicles')
    return render(request, 'index.html')


def about(request):
    return render(request, 'about.html')


def vehicles(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    if hasattr(request.user, 'usertype') and request.user.usertype.name != 'customer':
        request.session.flush()
        messages.error(request, "Access denied for customers.")
        return redirect('login')
    
    # Get parameters
    sort_by = request.GET.get('sort', 'price')
    color_id = request.GET.get('color', '')
    model_id = request.GET.get('model', '')
    brand_id = request.GET.get('brand', '')
    fuel_id = request.GET.get('fuel_type', '')
    search_query = request.GET.get('search', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Initial query
    cars = Car.objects.all()
    
    # Calculate average rating
    for car in cars:
        avg_rating = car.rating_set.aggregate(Avg('rating'))['rating__avg'] or 0
        car.avg_rating = avg_rating

    # Apply filters first
    if search_query:
        cars = cars.filter(Q(car_name__icontains=search_query) | Q(car_desc__icontains=search_query))
    if color_id:
        cars = cars.filter(car_color_id=color_id)
    if model_id:
        cars = cars.filter(car_model_id=model_id)
    if brand_id:
        cars = cars.filter(car_brand_id=brand_id)
    if fuel_id:
        cars = cars.filter(car_fuel_id=fuel_id)

    # Apply sorting
    if sort_by:
        if sort_by.startswith('-'):
            sort_by = sort_by[1:]
            cars = cars.order_by(f'-{sort_by}')
        else:
            cars = cars.order_by(sort_by)

    # Convert QuerySet to list to preserve availability information
    cars_list = list(cars)

    # Check availability if dates are provided
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            if start_date < date.today():
                messages.error(request, "Start date cannot be in the past")
            elif end_date < start_date:
                messages.error(request, "End date must be after start date")
            else:
                # Check availability for each car
                for car in cars_list:
                    car.is_available_for_period = car.is_available_for_period(start_date, end_date)
                    print(f"Car {car.car_name} availability: {car.is_available_for_period}")

        except ValueError as e:
            print(f"Date parsing error: {e}")
            messages.error(request, "Invalid date format")

    # Pagination after availability check
    paginator = Paginator(cars_list, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Context
    context = {
        'cars': page_obj,
        'car_count': len(cars_list),
        'colors': CarColor.objects.all(),
        'models': CarModel.objects.all(),
        'brands': Brand.objects.all(),
        'fuels': CarFuel.objects.all(),
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
        'today_date': date.today(),
    }
    
    return render(request, 'vehicles.html', context)



def vehicles_detial(request, id):
    car = get_object_or_404(Car, id=id)
    ratings = Rating.objects.filter(car=car)
    
    # Get dates from query parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Check availability if dates are provided
    is_available = True
    if start_date and end_date:
        is_available = car.is_available_for_period(start_date, end_date)
        print(f"Car {car.car_name} availability for {start_date} to {end_date}: {is_available}")

    context = {
        'car': car,
        'reviews': ratings,
        'rating_range': range(1, 6),
        'is_available': is_available,
        'start_date': start_date,
        'end_date': end_date
    }
    
    return render(request, 'cardetails.html', context)


from django.shortcuts import render, redirect
from .models import Contact  # Make sure the Contact model is imported
from django.contrib import messages

def contact(request):
    if request.method == "POST":
        contactname = request.POST.get('contactname', '')
        contactemail = request.POST.get('contactemail', '')
        contactnumber = request.POST.get('contactnumber', '')
        contactmsg = request.POST.get('contactmsg', '')

        # Save the contact information to the database
        contact = Contact(name=contactname, email=contactemail,
                          phone_number=contactnumber, message=contactmsg)
        contact.save()

        # Add a success message
        messages.success(request, 'Your message has been submitted successfully!')

        # Redirect to the same page or a success page
        return redirect('contact')

    return render(request, 'contact.html')


@login_required
def manager_predictive_maintenance(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    context = {
        'car': car,
        'predictions': MaintenancePrediction.objects.filter(car=car).order_by('-created_at')[:5]
    }
    
    if request.method == 'POST':
        try:
            # [Previous prediction code remains the same]
            
            # After creating prediction, add it to context instead of redirecting
            context['prediction'] = maintenance_prediction
            
        except Exception as e:
            context['error'] = str(e)
            print(f"Error during prediction: {str(e)}")

    return render(request, 'manager/predictive_maintenance.html', context)


@login_required
def customer_chat(request):
    managers = CustomUser.objects.filter(usertype__name='manager')
    selected_manager_id = request.GET.get('manager_id')
    selected_manager = None
    messages = []

    if selected_manager_id:
        selected_manager = get_object_or_404(CustomUser, id=selected_manager_id, usertype__name='manager')
        messages = ChatMessage.objects.filter(
            Q(customer=request.user, manager=selected_manager) |
            Q(manager=selected_manager, customer=request.user)
        ).order_by('timestamp')
    
    if request.method == 'POST' and selected_manager:
        message = request.POST.get('message')
        if message:
            ChatMessage.objects.create(
                customer=request.user,
                manager=selected_manager,
                message=message,
                sent_by_customer=True
            )
            return redirect(f'{request.path}?manager_id={selected_manager.id}')
    
    context = {
        'managers': managers,
        'selected_manager': selected_manager,
        'messages': messages
    }
    return render(request, 'customer_chat.html', context)

@login_required
def manager_messages(request):
    if not request.user.usertype.name == 'manager':
        return redirect('home')
    
    # Get all messages for this manager to show in customer list
    all_messages = ChatMessage.objects.filter(manager=request.user).order_by('-timestamp')
    
    # Get unique customers who have chatted with this manager
    customers = CustomUser.objects.filter(
        Q(customer_messages__manager=request.user)  # Messages from customers
    ).distinct()
    
    selected_customer_id = request.GET.get('customer_id')
    selected_customer = None
    customer_chat = []

    if selected_customer_id:
        selected_customer = get_object_or_404(CustomUser, id=selected_customer_id)
        customer_chat = ChatMessage.objects.filter(
            Q(customer=selected_customer, manager=request.user) |
            Q(manager=request.user, customer=selected_customer)
        ).order_by('timestamp')
    
    if request.method == 'POST' and selected_customer:
        message = request.POST.get('message')
        if message:
            ChatMessage.objects.create(
                customer=selected_customer,
                manager=request.user,
                message=message,
                sent_by_customer=False
            )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success'})
            return redirect(f'{request.path}?customer_id={selected_customer.id}')
    
    context = {
        'all_messages': all_messages,
        'customers': customers,
        'selected_customer': selected_customer,
        'customer_chat': customer_chat
    }
    return render(request, 'manager/manager_messages.html', context)

