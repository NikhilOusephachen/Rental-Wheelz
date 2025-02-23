from django.urls import path
from . import views
from user.views import (car_brand_delete, car_color_delete, car_delete, CustomLoginView, car_model_delete, logout_view, manager_app, manager_car_add,
                        manager_car_brand, manager_car_brand_add, manager_car_brand_view, manager_car_color, manager_car_color_add, manager_car_color_view, manager_car_management, manager_car_model, manager_car_model_add, manager_car_model_view,
                        manager_car_view, manager_dashboard, manager_edit, manager_order_management,
                        ManagerCarBrandEdit, ManagerCarColorEdit, ManagerCarEdit, ManagerCarModelEdit, profile,
                        register_view, manager_gps_overview, manager_car_ratings, update_car_location, manager_predictive_maintenance)
from booking.views import bill, manager_car_driver_delete, manager_car_drivers, manager_driver_add, manager_driver_edit, manager_order_details, order, order_detail, order_list, real_bill, create_rating


urlpatterns = [
    path("", views.index, name='home'),
    path("home", views.index, name='home'),
    path("about/", views.about, name='about'),
    path("contact/", views.contact, name='contact'),
    path("vehicles/", views.vehicles, name="vehicles"),
    path('car/<int:id>/', views.vehicles_detial, name='car_detail'),

    # booking
    path("bill/<int:id>/", bill, name="bill"),
    path("order/<int:bill_id>/", order, name="order"),
    path("view_order", order_list, name="view_order"),
    path("order_detail/<int:id>/", order_detail, name="order_detail"),
    path('order/<int:order_id>/bill/', real_bill, name='real_bill'),
    path("create-rating/<int:car_id>/<int:order_id>", create_rating, name="create_rating"),


    # manager
    path("manager_app/", manager_app, name="manager_app"),
    path("manager_dashboard/", manager_dashboard, name="manager_dashboard"),
    path("manager_car_management/", manager_car_management,
         name="manager_car_management"),
    path('manager/car/add/', manager_car_add, name='manager_car_add'),
    path("manager_car_view/<int:id>/", manager_car_view, name="manager_car_view"),
    path("manager_car_edit/<int:pk>/edit/",
         ManagerCarEdit.as_view(), name="manager_car_edit"),
    path('car/delete/<int:car_id>/', car_delete, name='manager_car_delete'),
    path('manager_car_ratings/', manager_car_ratings, name='manager_car_ratings'),
    path("manager_order_management/", manager_order_management,
         name="manager_order_management"),
    path('manager_order_details/<int:order_id>/',
         manager_order_details, name="manager_order_details"),
    path('manager_edit/<int:id>/', manager_edit, name='manager_edit'),
    path('manager_car_drivers/', manager_car_drivers, name='manager_car_drivers'),
    path('manager_driver_add/', manager_driver_add, name='manager_driver_add'),
    path('manager_driver_edit/<int:driver_id>/',
         manager_driver_edit, name='manager_driver_edit'),
    path('manager_car_driver_delete/<int:driver_id>/',
         manager_car_driver_delete, name='manager_car_driver_delete'),
    path("manager_car_brand/", manager_car_brand, name="manager_car_brand"),
    path('manager/car_brand/add/', manager_car_brand_add,
         name='manager_car_brand_add'),
    path("manager_car_brand_view/<int:id>/",
         manager_car_brand_view, name="manager_car_brand_view"),
    path("manager_car_brand_edit/<int:pk>/edit/",
         ManagerCarBrandEdit.as_view(), name="manager_car_brand_edit"),
    path('car_brand_delete/delete/<int:brand_id>/',
         car_brand_delete, name='car_brand_delete'),
    path("manager_car_color/", manager_car_color, name="manager_car_color"),
    path('manager/car_color/add/', manager_car_color_add,
         name='manager_car_color_add'),
    path("manager_car_color_view/<int:id>/",
         manager_car_color_view, name="manager_car_color_view"),
    path("manager_car_color_edit/<int:pk>/edit/",
         ManagerCarColorEdit.as_view(), name="manager_car_color_edit"),
    path('car_color_delete/delete/<int:color_id>/',
         car_color_delete, name='car_color_delete'),
    path("manager_car_model/", manager_car_model, name="manager_car_model"),
    path('manager/car_model/add/', manager_car_model_add,
         name='manager_car_model_add'),
    path("manager_car_model_view/<int:id>/",
         manager_car_model_view, name="manager_car_model_view"),
    path("manager_car_model_edit/<int:pk>/edit/",
         ManagerCarModelEdit.as_view(), name="manager_car_model_edit"),
    path('car_model_delete/delete/<int:model_id>/',
         car_model_delete, name='car_model_delete'),
    path('manager_gps_overview/', manager_gps_overview, name='manager_gps_overview'),
    path('update-location/<int:car_id>/', update_car_location, name="update_car_location"),
    path('manager/car/<int:car_id>/predict/', manager_predictive_maintenance, name='manager_predictive_maintenance'),


    # users
    path("register", register_view, name="register"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("profile/", profile, name="profile"),
    path('logout/', logout_view, name='logout'),

    # Chat URLs
    path('chat/', views.customer_chat, name='customer_chat'),
    path('manager/', views.manager_messages, name='manager_messages'), 

]
