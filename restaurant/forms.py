
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum

from .models import FoodItem, CustomerProfile, Reservation


class SignUpForm(UserCreationForm):

    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'phone_number',
            'password1',
            'password2'
        ]

    def save(self, commit=True):
        user = super().save(commit=commit)

        if commit:
            CustomerProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data['phone_number']
            )

        return user


class ReservationForm(forms.ModelForm):

    number_of_guests = forms.IntegerField(
        min_value=1,
        max_value=30,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'max': 30
        })
    )

    class Meta:
        model = Reservation
        fields = [
            'reservation_date',
            'reservation_time',
            'number_of_guests',
            'special_request',
        ]

        widgets = {
            'reservation_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'min': timezone.localdate().isoformat()
            }),
            'reservation_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'step': 3600
            }),
            'special_request': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any special requests?'
            }),
        }

    def clean_reservation_date(self):
        reservation_date = self.cleaned_data['reservation_date']

        if reservation_date < timezone.localdate():
            raise forms.ValidationError(
                "You cannot reserve a table for a past date."
            )

        return reservation_date

    def clean(self):
        cleaned_data = super().clean()

        reservation_date = cleaned_data.get('reservation_date')
        reservation_time = cleaned_data.get('reservation_time')
        guests = cleaned_data.get('number_of_guests')

        if reservation_time and (
            reservation_time.minute != 0 or
            reservation_time.second != 0
        ):
            self.add_error(
                'reservation_time',
                'Please select a full-hour slot, such as 7:00 PM.'
            )

        if reservation_date and reservation_time and guests:
            booked_guests = Reservation.objects.filter(
                reservation_date=reservation_date,
                reservation_time=reservation_time,
                status__in=['pending', 'approved']
            ).aggregate(total=Sum('number_of_guests'))['total'] or 0

            remaining_seats = 30 - booked_guests

            if guests > remaining_seats:
                self.add_error(
                    'number_of_guests',
                    f'Only {max(remaining_seats, 0)} seats are available.'
                )

        if reservation_date and reservation_time:
            now = timezone.localtime()

            if reservation_date == now.date():
                current_time = now.time().replace(tzinfo=None)

                if reservation_time <= current_time:
                    self.add_error(
                        'reservation_time',
                        'This time has already passed. Please select a future time.'
                    )

        return cleaned_data


class UserUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class CustomerProfileForm(forms.ModelForm):

    class Meta:
        model = CustomerProfile
        fields = ['phone_number']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ReservationAdminForm(forms.ModelForm):

    number_of_guests = forms.IntegerField(
        min_value=1,
        max_value=30,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'max': 30
        })
    )

    class Meta:
        model = Reservation
        fields = [
            'reservation_date',
            'reservation_time',
            'number_of_guests',
            'special_request',
        ]


class FoodItemForm(forms.ModelForm):

    class Meta:
        model = FoodItem
        fields = ['name', 'description', 'price', 'category', 'image', 'is_available']
