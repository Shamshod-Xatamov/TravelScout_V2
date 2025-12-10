from django import forms

class SupportForm(forms.Form):
    # ModelForm EMAS, oddiy Form (chunki baza yo'q)
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    subject = forms.CharField(max_length=200)
    message = forms.CharField(widget=forms.Textarea)