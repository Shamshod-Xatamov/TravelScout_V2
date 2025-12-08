from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Trip, Profile


class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['destination', 'duration_days', 'budget_type', 'interests']

        widgets = {
            'destination': forms.TextInput(attrs={
                'class': 'w-full px-5 py-4 rounded-xl bg-gray-50 border border-gray-200 focus:border-orange-500 focus:ring-2 focus:ring-orange-200 outline-none transition-all font-medium',
                'placeholder': 'E.g., Paris, Tokyo, New York'
            }),
            'duration_days': forms.NumberInput(attrs={
                'class': 'w-full px-5 py-4 rounded-xl bg-gray-50 border border-gray-200 focus:border-orange-500 focus:ring-2 focus:ring-orange-200 outline-none transition-all font-medium',
                'min': 1, 'max': 30
            }),
            'budget_type': forms.Select(attrs={
                'class': 'w-full px-5 py-4 rounded-xl bg-gray-50 border border-gray-200 focus:border-orange-500 focus:ring-2 focus:ring-orange-200 outline-none transition-all font-medium appearance-none'
            }),
            'interests': forms.TextInput(attrs={
                'class': 'w-full px-5 py-4 rounded-xl bg-gray-50 border border-gray-200 focus:border-orange-500 focus:ring-2 focus:ring-orange-200 outline-none transition-all font-medium',
                'placeholder': 'E.g., History, Food, Hiking'
            }),
        }


class CustomSignUpForm(UserCreationForm):
    email = forms.EmailField(
        required=True,  # <--- 1. MAJBURIY QILISH
        label="Email Address",  # <--- 2. LABELNI TO'G'RILASH (OPTIONAL so'zini yo'qotadi)
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-5 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:border-orange-500 outline-none',
            'placeholder': 'Email address'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email']


    # Email oldin ishlatilgan bo'lsa xato berish uchun (ixtiyoriy, lekin foydali)
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already currently used.")
        return email

class UserUpdateForm(forms.ModelForm):
    # required=True qildik, endi bo'sh qoldirib bo'lmaydi!
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'w-full px-5 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:border-orange-500 outline-none'
    }))

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full px-5 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:border-orange-500 outline-none'}),
        }


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture']
        widgets = {
             # Inputni yashiramiz (HTMLda label orqali bosiladi)
             'profile_picture': forms.FileInput(attrs={'class': 'hidden', 'id': 'file-upload'}),
        }