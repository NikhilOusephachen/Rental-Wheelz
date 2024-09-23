from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login
from django.contrib import messages
from booking.models import Order
from myapp.forms import CarBrandForm, CarColorForm, CarForm, CarModelForm
from django.db.models import Q
from myapp.models import Brand, Car, CarColor, CarModel
from user.models import UserType
from .forms import CustomUserCreationForm, ProfileUpdateForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views.generic import UpdateView


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # Fetch the customer usertype
            try:
                user_type = "Customer"
                customer_type = UserType.objects.get(name=user_type.lower())
            except UserType.DoesNotExist:
                messages.error(request, 'Customer user type does not exist.')
                # Redirect to registration page if UserType not found
                return redirect('register')

            # Set usertype to Customer
            user.usertype = customer_type

            # Now save the user
            user.save()

            messages.success(request, 'Registration successful.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'login.html'
    success_url = reverse_lazy('vehicles')

    # overiding dispatch method will handle all http menthods
    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            # Redirect to the vehicles page if the user is already logged in
            return redirect('vehicles')
        return super().dispatch(request, *args, **kwargs)


def logout_view(request):
    request.session.flush()
    return redirect('/')


@login_required
def profile(request):
    user = request.user

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('vehicles')
    else:
        form = ProfileUpdateForm(instance=user)

    return render(request, 'registration/profile.html', {
        'form': form,
    })


def manager_app(request):
    if request.method == "POST":
        # Get username and password from the form
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username)
        print(password)
        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.usertype.name == 'manager':  # Assuming 'user_type' is part of your user model
                # Log the user in
                login(request, user)
                # Redirect to manager dashboard after successful login
                return redirect('manager_dashboard')
            else:
                # Show error if the user is not a manager
                messages.error(
                    request, 'You are not authorized to access this page.')
                return redirect('manager_app')  # Redirect to the login page
        else:
            # Show error if authentication fails
            messages.error(request, 'Invalid username or password.')
            return redirect('manager_app')  # Redirect to the login page

    return render(request, 'manager/managerlogin.html')


@login_required
def manager_dashboard(request):
    order = Order.objects.all()
    order_count = order.count()
    car_count = Car.objects.all().count()
    recent_orders = order.order_by('-created_at')[:5]
    non_approved_order = order.filter(is_approved=False).count()
    return render(request, 'manager/managerdashbord.html', {'orders': order, 'order_count': order_count, 'car_count': car_count, 'recent_orders': recent_orders, 'approved_count': non_approved_order})


@login_required
def manager_car_management(request):
    query = request.GET.get('q')  # Get the search query from the URL
    if query:
        # Use Q objects to allow searching in multiple fields
        cars = Car.objects.filter(
            Q(car_name__icontains=query) |
            # Assuming CarBrand has a `name` field
            Q(car_brand__name__icontains=query) |
            Q(year__icontains=query)
        )
    else:
        cars = Car.objects.all()

    return render(request, 'manager/managercarmanagement.html', {'cars': cars, 'query': query})


@login_required
def manager_car_view(request, id):
    car = get_object_or_404(Car, id=id)
    return render(request, 'manager/managercarview.html', {'car': car})


@login_required
def manager_car_add(request):
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        print(form.errors)
        if form.is_valid():
            print("hi")
            form.save()
            messages.success(request, "Car added successfully!")
            # Redirect to the dashboard
            return redirect('manager_car_management')
    else:
        form = CarForm()
    return render(request, 'manager/add_car.html', {'form': form})


class ManagerCarEdit(UpdateView):
    model = Car
    form_class = CarForm
    template_name = 'manager/managercaredit.html'
    # Redirect after successfully updating
    success_url = reverse_lazy('manager_car_management')

    def form_valid(self, form):
        messages.success(self.request, 'Car details updated successfully!')
        return super().form_valid(form)


def car_delete(request, car_id):
    if request.method == "POST":
        car = get_object_or_404(Car, id=car_id)
        car_name = car.car_name
        car.delete()
        messages.success(request, f"The car '{
                         car_name}' has been successfully deleted.")
    return redirect('manager_car_management')


@login_required
def manager_order_management(request):
    query = request.GET.get('q')
    orders = Order.objects.all()  # Default: get all orders

    if query:
        # Perform search across relevant fields
        orders = orders.filter(
            Q(id__icontains=query) |  # Search by order ID
            # Search by car name (assuming ForeignKey)
            Q(car__car_name__icontains=query) |
            # Search by customer  first name
            Q(user__username__icontains=query)
        )

    return render(request, 'manager/managerordermanagement.html', {'orders': orders, 'query': query})


@login_required
def manager_edit(request, id):
    # Fetch the order associated with the given car
    order = get_object_or_404(Order, id=id)

    # Toggle the approval status
    order.is_approved = not order.is_approved
    order.save()

    # Toggle the car avaiablity status
    car = Car.objects.get(id=order.car.id)
    car.available = not car.available
    car.save()

    # Add a success message
    if order.is_approved:
        messages.success(request, "Order has been approved.")
    else:
        messages.warning(request, "Order has been disapproved.")

    # Redirect to the dashboard or any other relevant page
    return redirect('manager_order_management')


@login_required
def manager_car_brand(request):
    query = request.GET.get('q')
    brands = Brand.objects.all()  # Default: get all orders

    if query:
        # Perform search across relevant fields
        brands = brands.filter(
            Q(id__icontains=query) |  # Search by order ID
            # Search by car name (assuming ForeignKey)
            Q(name__icontains=query)
        )
    return render(request, 'manager/carbrandlist.html', {'brands': brands, 'query': query})


@login_required
def manager_car_brand_view(request, id):
    brand = get_object_or_404(Brand, id=id)
    return render(request, 'manager/managercarbrandview.html', {'brand': brand})


@login_required
def manager_car_brand_add(request):
    if request.method == 'POST':
        form = CarBrandForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Brand added successfully!")
            # Redirect to the dashboard
            return redirect('manager_car_brand')
    else:
        form = CarForm()
    return render(request, 'manager/add_car_brand.html', {'form': form})


class ManagerCarBrandEdit(UpdateView):
    model = Brand
    form_class = CarBrandForm
    template_name = 'manager/managercarbrandedit.html'
    # Redirect after successfully updating
    success_url = reverse_lazy('manager_car_brand')

    def form_valid(self, form):
        messages.success(self.request, 'Car Brand updated successfully!')
        return super().form_valid(form)


def car_brand_delete(request, brand_id):
    if request.method == "POST":
        brand = get_object_or_404(Brand, id=brand_id)
        brand_name = brand.name
        brand.delete()
        messages.success(request, f"The brand '{
                         brand_name}' has been successfully deleted.")
    return redirect('manager_car_brand')


@login_required
def manager_car_model(request):
    query = request.GET.get('q')
    models = CarModel.objects.all()  # Default: get all orders

    if query:
        # Perform search across relevant fields
        models = models.filter(
            Q(id__icontains=query) |  # Search by order ID
            # Search by car name (assuming ForeignKey)
            Q(model_name__icontains=query)
        )
    return render(request, 'manager/carmodellist.html', {'models': models, 'query': query})


@login_required
def manager_car_model_view(request, id):
    model = get_object_or_404(CarModel, id=id)
    return render(request, 'manager/managercarmodelview.html', {'model': model})


@login_required
def manager_car_model_add(request):
    if request.method == 'POST':
        form = CarModelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "model added successfully!")
            # Redirect to the dashboard
            return redirect('manager_car_model')
    else:
        form = CarForm()
    return render(request, 'manager/add_car_model.html', {'form': form})


class ManagerCarModelEdit(UpdateView):
    model = CarModel
    form_class = CarModelForm
    template_name = 'manager/managercarmodeledit.html'
    # Redirect after successfully updating
    success_url = reverse_lazy('manager_car_model')

    def form_valid(self, form):
        messages.success(self.request, 'Car Model updated successfully!')
        return super().form_valid(form)


def car_model_delete(request, model_id):
    if request.method == "POST":
        model = get_object_or_404(CarModel, id=model_id)
        model_name = model.model_name
        model.delete()
        messages.success(request, f"The Model '{
                         model_name}' has been successfully deleted.")
    return redirect('manager_car_model')


@login_required
def manager_car_color(request):
    query = request.GET.get('q')
    colors = CarColor.objects.all()  # Default: get all orders

    if query:
        # Perform search across relevant fields
        colors = colors.filter(
            Q(id__icontains=query) |  # Search by order ID
            # Search by car name (assuming ForeignKey)
            Q(color__icontains=query)
        )
    return render(request, 'manager/carcolor.html', {'colors': colors, 'query': query})


@login_required
def manager_car_color_view(request, id):
    color = get_object_or_404(CarColor, id=id)
    return render(request, 'manager/managercarcolorview.html', {'color': color})


@login_required
def manager_car_color_add(request):
    if request.method == 'POST':
        form = CarColorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "color added successfully!")
            # Redirect to the dashboard
            return redirect('manager_car_color')
    else:
        form = CarForm()
    return render(request, 'manager/add_car_color.html', {'form': form})


class ManagerCarColorEdit(UpdateView):
    model = CarColor
    form_class = CarColorForm
    template_name = 'manager/managercarcoloredit.html'
    success_url = reverse_lazy('manager_car_color')

    def form_valid(self, form):
        print(form.errors)
        messages.success(self.request, 'Car Color updated successfully!')
        return super().form_valid(form)


def car_color_delete(request, color_id):
    if request.method == "POST":
        color = get_object_or_404(CarColor, id=color_id)
        color_name = color.color
        color.delete()
        messages.success(request, f"The color '{
                         color_name}' has been successfully deleted.")
    return redirect('manager_car_color')
