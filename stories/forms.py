from django import forms
from .models import Story

class StoryForm(forms.ModelForm):
    # Bu form Create va Edit uchun kerak
    class Meta:
        model = Story
        fields = ['title', 'location', 'content']
        # Rasmlar ImageField orqali keladi, ular Formda ko'rsatilishi shart emas.