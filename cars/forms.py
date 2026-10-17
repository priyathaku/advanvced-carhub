from django import forms
from django.utils import timezone
from .models import Car, TestDriveRequest, ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Your Full Name', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'name@example.com', 'required': True}),
            'subject': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Subject / Topic', 'required': True}),
            'message': forms.Textarea(attrs={'class': 'form-input form-textarea', 'placeholder': 'How can our luxury concierge assist you?', 'rows': 4, 'required': True}),
        }


class TestDriveForm(forms.ModelForm):
    TIME_SLOTS = [
        ('10:00 AM - 11:30 AM', '10:00 AM - 11:30 AM (Morning VIP)'),
        ('12:00 PM - 01:30 PM', '12:00 PM - 01:30 PM (Midday)'),
        ('02:30 PM - 04:00 PM', '02:30 PM - 04:00 PM (Afternoon Track)'),
        ('04:30 PM - 06:00 PM', '04:30 PM - 06:00 PM (Sunset Cruise)'),
    ]

    preferred_time = forms.ChoiceField(
        choices=TIME_SLOTS,
        widget=forms.Select(attrs={'class': 'form-input form-select', 'required': True})
    )

    class Meta:
        model = TestDriveRequest
        fields = ['name', 'email', 'phone', 'car', 'preferred_date', 'preferred_time', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Full Name', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email Address', 'required': True}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+1 (555) 000-0000', 'required': True}),
            'car': forms.Select(attrs={'class': 'form-input form-select', 'required': True}),
            'preferred_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date', 'required': True}),
            'notes': forms.Textarea(attrs={'class': 'form-input form-textarea', 'placeholder': 'Any specific requests or requirements for your test drive?', 'rows': 3}),
        }

    def clean_preferred_date(self):
        date = self.cleaned_data.get('preferred_date')
        if date and date < timezone.now().date():
            raise forms.ValidationError("Test drive date cannot be in the past.")
        return date
