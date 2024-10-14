from django.contrib import messages
from .models import Car, CarColor, CarModel, Brand, CarFuel
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from .models import *
from django.db.models import Q


def index(request):
    if request.user.is_authenticated:
        # Replace 'vehicles' with the name of your URL pattern
        return redirect('vehicles')
    return render(request, 'index.html')


def about(request):
    return render(request, 'about.html')


from django.db.models import Q  # Import Q for complex lookups

def vehicles(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    # If the user is authenticated, check the user type
    if hasattr(request.user, 'usertype') and request.user.usertype.name != 'customer':
        request.session.flush()
        messages.error(request, "Access denied for customers.")
        return redirect('login')
    
    # Get sort, filter, and search parameters from the request
    sort_by = request.GET.get('sort', 'price')
    color_id = request.GET.get('color', '')
    model_id = request.GET.get('model', '')
    brand_id = request.GET.get('brand', '')
    fuel_id = request.GET.get('fuel_type', '')
    search_query = request.GET.get('search', '')  # Get the search term

    # Initial query to get all cars
    cars = Car.objects.all()

    # Filter by search term if provided
    if search_query:
        cars = cars.filter(
        Q(car_name__icontains=search_query) |  # Search by car name
        Q(car_desc__icontains=search_query)    # Search by car description
        )

    # Apply filters
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

    # Pagination
    page_number = request.GET.get('page', 1)
    paginator = Paginator(cars, 10)
    page_obj = paginator.get_page(page_number)

    # Fetching filter options
    colors = CarColor.objects.all()
    models = CarModel.objects.all()
    brands = Brand.objects.all()
    fuels = CarFuel.objects.all()
    car_count = cars.count()

    # Render the response
    return render(request, 'vehicles.html', {
        'cars': page_obj,
        'car_count': car_count,
        'colors': colors,
        'models': models,
        'brands': brands,
        'fuels': fuels,
        'search_query': search_query,  # Pass search query to the template for preserving search term
    })



def vehicles_detial(request, id):
    car = get_object_or_404(Car, id=id)
    params = {'car': car}
    return render(request, 'cardetails.html', params)


def contact(request):
    if request.method == "POST":
        contactname = request.POST.get('contactname', '')
        contactemail = request.POST.get('contactemail', '')
        contactnumber = request.POST.get('contactnumber', '')
        contactmsg = request.POST.get('contactmsg', '')
        contact = Contact(name=contactname, email=contactemail,
                          phone_number=contactnumber, message=contactmsg)
        contact.save()
    return render(request, 'contact.html ')
