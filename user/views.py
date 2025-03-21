from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import authenticate, login
from django.contrib import messages
from booking.models import Order, Rating
from myapp.forms import CarBrandForm, CarColorForm, CarForm, CarModelForm
from django.db.models import Q
from myapp.models import Brand, Car, CarColor, CarModel, CarTracking, CarLocation, MaintenancePrediction
from user.models import UserType
from .forms import CustomUserCreationForm, ProfileUpdateForm
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import UpdateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
#from .services.maintenance_predictor import MaintenancePredictor
import os
import joblib
import pandas as pd
from django.conf import settings
from datetime import datetime

def register_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            # Fetch the customer usertype
            try:
                user_type = "Customer"
                customer_type = UserType.objects.get(name=user_type.lower())
            except UserType.DoesNotExist:
                messages.error(request, "Customer user type does not exist.")
                # Redirect to registration page if UserType not found
                return redirect("register")

            # Set usertype to Customer
            user.usertype = customer_type

            # Now save the user
            user.save()

            messages.success(request, "Registration successful.")
            return redirect("login")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()

    return render(request, "register.html", {"form": form})


class CustomLoginView(LoginView):
    template_name = "login.html"
    success_url = reverse_lazy("vehicles")

    def post(self, request, *args, **kwargs):
        # Get the credentials from the POST data
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        # Check if authentication was successful
        if user is not None:
            # Check if the user type is "customer"
            if hasattr(user, "usertype") and user.usertype.name.lower() == "customer":
                # Log in the user if they are not a "customer"
                login(request, user)
                return redirect(self.success_url)

            # Add a message and redirect to the login page
            messages.error(request, "Access denied for non-customers.")
            return redirect("login")

        # If the user could not be authenticated, proceed as usual (default LoginView behavior)
        return super().post(request, *args, **kwargs)


def logout_view(request):
    request.session.flush()
    return redirect("/")


@login_required
def profile(request):
    user = request.user

    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()

            messages.success(request, "Profile updated successfully.")
            return redirect("vehicles")
    else:
        form = ProfileUpdateForm(instance=user)

    return render(
        request,
        "registration/profile.html",
        {
            "form": form,
        },
    )


def manager_app(request):
    if request.method == "POST":
        # Get username and password from the form
        username = request.POST.get("username")
        password = request.POST.get("password")
        print(username)
        print(password)
        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if (
                user.usertype.name == "manager"
            ):  # Assuming 'user_type' is part of your user model
                # Log the user in
                login(request, user)
                # Redirect to manager dashboard after successful login
                return redirect("manager_dashboard")
            else:
                # Show error if the user is not a manager
                messages.error(request, "You are not authorized to access this page.")
                return redirect("manager_app")  # Redirect to the login page
        else:
            # Show error if authentication fails
            messages.error(request, "Invalid username or password.")
            return redirect("manager_app")  # Redirect to the login page

    return render(request, "manager/managerlogin.html")


@login_required
def manager_dashboard(request):
    order = Order.objects.all()
    order_count = order.count()
    car_count = Car.objects.all().count()
    recent_orders = order.order_by("-created_at")[:5]
    non_approved_order = order.filter(is_approved=False).count()
    return render(
        request,
        "manager/managerdashbord.html",
        {
            "orders": order,
            "order_count": order_count,
            "car_count": car_count,
            "recent_orders": recent_orders,
            "approved_count": non_approved_order,
        },
    )


@login_required
def manager_car_management(request):
    query = request.GET.get("q")  # Get the search query from the URL
    if query:
        # Use Q objects to allow searching in multiple fields
        cars = Car.objects.filter(
            Q(car_name__icontains=query)
            |
            # Assuming CarBrand has a `name` field
            Q(car_brand__name__icontains=query)
            | Q(year__icontains=query)
        )
    else:
        cars = Car.objects.all()

    return render(
        request, "manager/managercarmanagement.html", {"cars": cars, "query": query}
    )


@login_required
def manager_car_view(request, id):
    car = get_object_or_404(Car, id=id)
    return render(request, "manager/managercarview.html", {"car": car})


@login_required
def manager_car_add(request):
    if request.method == "POST":
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the form but don't commit to database yet
            car = form.save(commit=False)
            
            # Get lease details from the form and convert to appropriate types
            lease_price = request.POST.get('lease_price')
            min_months = request.POST.get('minimum_lease_months')
            max_months = request.POST.get('maximum_lease_months')
            
            # Ensure values are not empty and convert to appropriate types
            if lease_price and lease_price.strip():
                car.lease_price = float(lease_price)
                # If lease price is provided, set is_available_for_lease to True
                if float(lease_price) > 0:
                    car.is_available_for_lease = True
            
            if min_months and min_months.strip():
                car.minimum_lease_months = int(min_months)
                
            if max_months and max_months.strip():
                car.maximum_lease_months = int(max_months)
            
            # Now save the car with all details
            car.save()
            
            messages.success(request, "Car added successfully!")
            return redirect("manager_car_management")
        else:
            print(form.errors)
            messages.error(request, "Please correct the errors below.")
    else:
        form = CarForm()
    
    # Get all necessary data for the form
    brands = Brand.objects.all()
    models = CarModel.objects.all()
    colors = CarColor.objects.all()
    
    return render(request, "manager/add_car.html", {
        "form": form,
        "brands": brands,
        "models": models,
        "colors": colors
    })


class ManagerCarEdit(UpdateView):
    model = Car
    form_class = CarForm
    template_name = "manager/managercaredit.html"
    success_url = reverse_lazy("manager_car_management")

    def form_valid(self, form):
        # Get the car instance but don't save yet
        car = form.save(commit=False)
        
        # Update lease details
        lease_price = self.request.POST.get('lease_price')
        min_months = self.request.POST.get('minimum_lease_months')
        max_months = self.request.POST.get('maximum_lease_months')
        
        # Ensure values are not empty and convert to appropriate types
        if lease_price and lease_price.strip():
            car.lease_price = float(lease_price)
            # If lease price is provided, set is_available_for_lease to True
            if float(lease_price) > 0:
                car.is_available_for_lease = True
        
        if min_months and min_months.strip():
            car.minimum_lease_months = int(min_months)
            
        if max_months and max_months.strip():
            car.maximum_lease_months = int(max_months)
        
        # Now save the car
        car.save()
        
        messages.success(self.request, "Car details updated successfully!")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = Brand.objects.all()
        context['models'] = CarModel.objects.all()
        context['colors'] = CarColor.objects.all()
        return context

def car_delete(request, car_id):
    if request.method == "POST":
        car = get_object_or_404(Car, id=car_id)
        car_name = car.car_name
        car.delete()
        messages.success(
            request, f"The car '{car_name}' has been successfully deleted."
        )
    return redirect("manager_car_management")


@login_required
def manager_car_ratings(request):
    ratings = Rating.objects.all()
    return render(request, "manager/car_ratings.html", {"ratings": ratings})


@login_required
def manager_order_management(request):
    query = request.GET.get("q")
    orders = Order.objects.all()  # Default: get all orders

    if query:
        # Perform search across relevant fields
        orders = orders.filter(
            Q(id__icontains=query)  # Search by order ID
            |
            # Search by car name (assuming ForeignKey)
            Q(car__car_name__icontains=query)
            |
            # Search by customer  first name
            Q(user__username__icontains=query)
        )

    return render(
        request,
        "manager/managerordermanagement.html",
        {"orders": orders, "query": query},
    )


@login_required
def manager_edit(request, id):
    # Fetch the order associated with the given ID
    order = get_object_or_404(Order, id=id)

    # Toggle the approval status
    order.is_approved = not order.is_approved
    order.save()

    # Toggle the car availability status
    car = Car.objects.get(id=order.car.id)
    car.available = not car.available
    car.save()

    # Update the 'is_enabled' status of the car's tracking feature
    # We only enable tracking if the car is approved and available
    # Get or create the 'CarTracking' object for the given car
    car_tracking, created = CarTracking.objects.get_or_create(car=car)
    if order.is_approved:
        car_tracking.is_enabled = True  # Enable tracking if the car is approved and available
        print("car tarcking is enabled")
        print(car_tracking.is_enabled)
    else:
        car_tracking.is_enabled = False  # Disable tracking if not approved or not available
    car_tracking.save()

    # Add a success message based on the approval status
    if order.is_approved:
        messages.success(request, "Order has been approved and car tracking enabled.")
    else:
        messages.warning(request, "Order has been disapproved and car tracking disabled.")

    # Redirect to the manager's order management page or any other relevant page
    return redirect("manager_order_management")



@login_required
def manager_car_brand(request):
    query = request.GET.get("q")
    brands = Brand.objects.all()  # Default: get all orders

    if query:
        # Perform search across relevant fields
        brands = brands.filter(
            Q(id__icontains=query)  # Search by order ID
            |
            # Search by car name (assuming ForeignKey)
            Q(name__icontains=query)
        )
    return render(
        request, "manager/carbrandlist.html", {"brands": brands, "query": query}
    )


@login_required
def manager_car_brand_view(request, id):
    brand = get_object_or_404(Brand, id=id)
    return render(request, "manager/managercarbrandview.html", {"brand": brand})


@login_required
def manager_car_brand_add(request):
    if request.method == "POST":
        form = CarBrandForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Brand added successfully!")
            # Redirect to the dashboard
            return redirect("manager_car_brand")
    else:
        form = CarForm()
    return render(request, "manager/add_car_brand.html", {"form": form})


class ManagerCarBrandEdit(UpdateView):
    model = Brand
    form_class = CarBrandForm
    template_name = "manager/managercarbrandedit.html"
    # Redirect after successfully updating
    success_url = reverse_lazy("manager_car_brand")

    def form_valid(self, form):
        messages.success(self.request, "Car Brand updated successfully!")
        return super().form_valid(form)


def car_brand_delete(request, brand_id):
    if request.method == "POST":
        brand = get_object_or_404(Brand, id=brand_id)
        brand_name = brand.name
        brand.delete()
        messages.success(
            request, f"The brand '{brand_name}' has been successfully deleted."
        )
    return redirect("manager_car_brand")


@login_required
def manager_car_model(request):
    query = request.GET.get("q")
    models = CarModel.objects.all()  # Default: get all orders

    if query:
        # Perform search across relevant fields
        models = models.filter(
            Q(id__icontains=query)  # Search by order ID
            |
            # Search by car name (assuming ForeignKey)
            Q(model_name__icontains=query)
        )
    return render(
        request, "manager/carmodellist.html", {"models": models, "query": query}
    )


@login_required
def manager_car_model_view(request, id):
    model = get_object_or_404(CarModel, id=id)
    return render(request, "manager/managercarmodelview.html", {"model": model})


@login_required
def manager_car_model_add(request):
    if request.method == "POST":
        form = CarModelForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "model added successfully!")
            # Redirect to the dashboard
            return redirect("manager_car_model")
    else:
        form = CarForm()
    return render(request, "manager/add_car_model.html", {"form": form})


class ManagerCarModelEdit(UpdateView):
    model = CarModel
    form_class = CarModelForm
    template_name = "manager/managercarmodeledit.html"
    # Redirect after successfully updating
    success_url = reverse_lazy("manager_car_model")

    def form_valid(self, form):
        messages.success(self.request, "Car Model updated successfully!")
        return super().form_valid(form)


def car_model_delete(request, model_id):
    if request.method == "POST":
        model = get_object_or_404(CarModel, id=model_id)
        model_name = model.model_name
        model.delete()
        messages.success(
            request, f"The Model '{model_name}' has been successfully deleted."
        )
    return redirect("manager_car_model")


@login_required
def manager_car_color(request):
    query = request.GET.get("q")
    colors = CarColor.objects.all()  # Default: get all orders

    if query:
        # Perform search across relevant fields
        colors = colors.filter(
            Q(id__icontains=query)  # Search by order ID
            |
            # Search by car name (assuming ForeignKey)
            Q(color__icontains=query)
        )
    return render(request, "manager/carcolor.html", {"colors": colors, "query": query})


@login_required
def manager_car_color_view(request, id):
    color = get_object_or_404(CarColor, id=id)
    return render(request, "manager/managercarcolorview.html", {"color": color})


@login_required
def manager_car_color_add(request):
    if request.method == "POST":
        form = CarColorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "color added successfully!")
            # Redirect to the dashboard
            return redirect("manager_car_color")
    else:
        form = CarForm()
    return render(request, "manager/add_car_color.html", {"form": form})


class ManagerCarColorEdit(UpdateView):
    model = CarColor
    form_class = CarColorForm
    template_name = "manager/managercarcoloredit.html"
    success_url = reverse_lazy("manager_car_color")

    def form_valid(self, form):
        print(form.errors)
        messages.success(self.request, "Car Color updated successfully!")
        return super().form_valid(form)


def car_color_delete(request, color_id):
    if request.method == "POST":
        color = get_object_or_404(CarColor, id=color_id)
        color_name = color.color
        color.delete()
        messages.success(
            request, f"The color '{color_name}' has been successfully deleted."
        )
    return redirect("manager_car_color")


def manager_gps_overview(request):
    # Get all cars that have location tracking enabled
    tracked_vehicles = Car.objects.filter(tracking__is_enabled=True)
    print(tracked_vehicles)

    # Add current location data to each tracked vehicle
    vehicle_data = []
   
    for vehicle in tracked_vehicles:
        # Get the current location for each car
        location = CarLocation.objects.filter(
            car=vehicle
        ).first()  # Get the first matching location
        print(location)
        if location:
            vehicle_data.append({"car": vehicle, "location": location})

    return render(
        request, "manager/manager_gps_overview.html", {"vehicle_data": vehicle_data}
    )


# View to update car location
# @csrf_exempt  # Disable CSRF for simplicity (you can use proper security in production)
def update_car_location(request, car_id):
    car = get_object_or_404(Car, id=car_id)

    if request.method == "POST":
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")
        tracking_enabled = request.POST.get("tracking_enabled", False)

        # Update or create the car's location
        location, created = CarLocation.objects.update_or_create(
            car=car,
            defaults={
                "latitude": latitude,
                "longitude": longitude,
                "last_updated": timezone.now()
            }
        )

        # Update the tracking status
        car.is_tracking_enabled = tracking_enabled
        car.save()

        # Provide feedback to the user
        if created:
            messages.success(request, f"Location for {car.car_name} added successfully.")
        else:
            messages.success(request, f"Location for {car.car_name} updated successfully.")

        return redirect("manager_gps_overview")

    return render(request, "manager/update_car_location.html", {"car": car})


@login_required
def manager_predictive_maintenance(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    context = {
        'car': car,
        'predictions': MaintenancePrediction.objects.filter(car=car).order_by('-created_at')[:5]
    }
    
    if request.method == 'POST':
        try:
            # Load model and scaler
            model_path = os.path.join(settings.BASE_DIR, 'ml_model', 'predictive_maintenance_model.pkl')
            scaler_path = os.path.join(settings.BASE_DIR, 'ml_model', 'scaler.pkl')
            
            model = joblib.load(model_path)
            scaler = joblib.load(scaler_path)

            # Get feature names from the model
            feature_names_path = os.path.join(settings.BASE_DIR, 'ml_model', 'feature_names.txt')
            with open(feature_names_path, 'r') as f:
                model_features = [line.strip() for line in f.readlines()]
            
            print("Available features:", model_features)  # Debug print

            # Create input data dictionary
            input_dict = {
                'Mileage': float(request.POST.get('mileage', 0)),
                'Odometer_Reading': float(request.POST.get('odometer_reading', 0)),
                'Days_Since_Last_Service': float(request.POST.get('days_since_last_service', 0)),
                'Engine_Size': float(request.POST.get('engine_size', 2000)),
                'Service_History': float(request.POST.get('service_history', 0)),
                'Accident_History': float(request.POST.get('accident_history', 0)),
                'Maintenance_History': 2 if request.POST.get('maintenance_history') == 'Good' else 1 if request.POST.get('maintenance_history') == 'Average' else 0,
                'Fuel_Type': 1 if str(car.car_fuel).lower() == 'petrol' else 0,
                'Transmission_Type': 1 if str(car.transmission).lower() == 'automatic' else 0,
                'Reported_Issues': 0  # Adding default value for Reported_Issues
            }

            # Get vehicle model and conditions
            vehicle_model = str(car.car_model).upper()
            tire_condition = request.POST.get('tire_condition', 'Good')
            brake_condition = request.POST.get('brake_condition', 'Good')

            # Add one-hot encoded columns
            for model_type in ['SUV', 'Truck', 'Van', 'Car', 'Motorcycle', 'Bus']:
                input_dict[f'Vehicle_Model_{model_type}'] = 1 if model_type == vehicle_model else 0

            for condition in ['Good', 'New', 'Worn Out']:
                input_dict[f'Tire_Condition_{condition}'] = 1 if condition == tire_condition else 0
                input_dict[f'Brake_Condition_{condition}'] = 1 if condition == brake_condition else 0

            # Create DataFrame with exact feature names
            input_data = pd.DataFrame([input_dict])
            input_data = input_data[model_features]  # Ensure columns match exactly

            # Scale numerical features
            numerical_features = [
                'Mileage', 'Odometer_Reading', 'Days_Since_Last_Service',
                'Engine_Size', 'Service_History', 'Accident_History'
            ]
            input_data[numerical_features] = scaler.transform(input_data[numerical_features])

            # Make prediction
            prediction = bool(model.predict(input_data)[0])
            probability = float(model.predict_proba(input_data)[0][1])

            # Save prediction
            maintenance_prediction = MaintenancePrediction.objects.create(
                car=car,
                mileage=float(request.POST.get('mileage', 0)),
                odometer_reading=float(request.POST.get('odometer_reading', 0)),
                days_since_last_service=int(request.POST.get('days_since_last_service', 0)),
                engine_size=float(request.POST.get('engine_size', 2000)),
                service_history=int(request.POST.get('service_history', 0)),
                accident_history=int(request.POST.get('accident_history', 0)),
                maintenance_history=request.POST.get('maintenance_history', 'Good'),
                fuel_type=car.car_fuel,
                transmission_type=car.transmission,
                vehicle_model=car.car_model,
                tire_condition=request.POST.get('tire_condition', 'Good'),
                brake_condition=request.POST.get('brake_condition', 'Good'),
                prediction_result=prediction,
                prediction_probability=probability * 100
            )

            context['prediction'] = maintenance_prediction

        except Exception as e:
            print(f"Error during prediction: {str(e)}")
            context['error'] = str(e)

    return render(request, 'manager/predictive_maintenance.html', context)





