from .models import Car, CarColor, CarModel, Brand, CarFuel
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from .models import *


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
    sort_by = request.GET.get('sort', 'price')
    color_id = request.GET.get('color', '')
    model_id = request.GET.get('model', '')
    brand_id = request.GET.get('brand', '')
    fuel_id = request.GET.get('fuel_type', '')

    cars = Car.objects.all()
    if color_id:
        cars = cars.filter(car_color_id=color_id)
    if model_id:
        cars = cars.filter(car_model_id=model_id)
    if brand_id:
        cars = cars.filter(car_brand_id=brand_id)
    if fuel_id:
        cars = cars.filter(car_fuel_id=fuel_id)

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

    colors = CarColor.objects.all()
    models = CarModel.objects.all()
    brands = Brand.objects.all()
    fuels = CarFuel.objects.all()

    return render(request, 'vehicles.html', {
        'cars': page_obj,
        'colors': colors,
        'models': models,
        'brands': brands,
        'fuels': fuels,
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
