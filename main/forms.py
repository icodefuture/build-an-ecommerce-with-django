from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Product, Gallery, Order

class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=25, 
        min_length=5, 
        label='Username', 
        widget=forms.TextInput(
            attrs={
                'class': 'form-control'
            }
        ))
    
    password = forms.CharField(
        max_length=15, 
        min_length=8, 
        label='Password', 
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'type': 'password'
            }
        ))

class ProductForm(forms.ModelForm):
    image = forms.ImageField()
    
    class Meta:
        model = Product
        fields = ['title', 'image', 'price', 'description']
        exclude = ['slug']

class GalleryForm(forms.ModelForm):
    image = forms.ImageField(
        widget=forms.FileInput(
            attrs={
                'class': 'form-control',
                'multiple': 'true'
            }
        )
    )

    class Meta:
        model = Gallery
        fields = ['image']

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = '__all__'
        exclude = ['user', 'total', 'created_at', 'updated_at', 'status', 'session_id', 'payment_id']