# forms.py
from django import forms
from .models import Car, Brand, CarModel, CarColor


class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = [
            'car_name', 'car_desc', 'car_brand', 'car_model',
            'car_color', 'car_fuel', 'transmission', 'year',
            'available', 'price', 'image'
        ]
        widgets = {
            'car_desc': forms.Textarea(attrs={'rows': 3}),
        }


class CarBrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['id', 'name']


class CarModelForm(forms.ModelForm):
    class Meta:
        model = CarModel
        fields = ['id', 'model_name', 'brand']


class CarColorForm(forms.ModelForm):
    class Meta:
        model = CarColor
        fields = ['id', 'color']
