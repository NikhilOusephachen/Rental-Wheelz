from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from booking.models import Order


class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, required=False)
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput,
        help_text='Enter a strong password.'
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput,
        help_text='Enter the same password as above, for verification.'
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name',
                  'email', 'phone_number', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError({
                'password2': "The two password fields didn’t match.",
            })
        return cleaned_data


class ProfileUpdateForm(forms.ModelForm):
    #address = forms.CharField(max_length=500, required=False)
    #driving_license = forms.ImageField(required=False)

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'image', 'driving_licence']

        widgets = { 
            'phone_number': forms.TextInput(attrs={'maxlength': '15'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # If a user is passed in, find their latest order's driving license
        if user:
            try:
                latest_order = Order.objects.filter(user=user).latest('created_at')
                if latest_order.driving_license:
                    #self.fields['driving_license'].initial = latest_order.driving_license
                    self.fields['address'].initial = latest_order.address
            except Order.DoesNotExist:
                pass  # If no order exists, don't set any initial driving license
