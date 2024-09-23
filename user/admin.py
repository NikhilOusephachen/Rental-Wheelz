from django.contrib import admin
from .models import UserType, CustomUser
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, ProfileUpdateForm


@admin.register(UserType)
class UserTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

# Register the CustomUser in the Django Admin


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Fields to display in the admin list
    list_display = ('username', 'usertype', 'email', 'phone_number')

    # Fields to search in the admin
    search_fields = ('username', 'email', 'phone_number')

    # Form to create a user with hashed password
    add_form = CustomUserCreationForm

    # Form to change a user's details, including password handling
    form = ProfileUpdateForm

    # The fields to display in the admin detail view
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'phone_number')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'usertype')}),
    )

    # The fields to display when creating a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone_number', 'password1', 'password2', 'usertype'),
        }),
    )

    # Override the save_model to ensure password is hashed on save
    def save_model(self, request, obj, form, change):
        if form.is_valid():
            if not change or 'password' in form.cleaned_data:
                # If password was provided, hash it before saving
                if form.cleaned_data.get('password1'):
                    obj.set_password(form.cleaned_data['password1'])
            obj.save()
