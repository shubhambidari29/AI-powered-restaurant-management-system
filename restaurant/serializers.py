
from django.contrib.auth.models import User, Group
from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers

from .models import FoodItem, Reservation, CustomerProfile


# Food Serializer
class FoodItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodItem
        fields = '__all__'


# Reservation Serializer
class ReservationSerializer(serializers.ModelSerializer):
    customer = serializers.StringRelatedField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Reservation
        fields = '__all__'
        read_only_fields = ('customer', 'status', 'created_at')

    def validate(self, data):
        date = data.get(
            'reservation_date',
            getattr(self.instance, 'reservation_date', None)
        )
        time = data.get(
            'reservation_time',
            getattr(self.instance, 'reservation_time', None)
        )
        guests = data.get(
            'number_of_guests',
            getattr(self.instance, 'number_of_guests', None)
        )

        if not date or not time or not guests:
            return data

        if guests < 1 or guests > 30:
            raise serializers.ValidationError(
                "Guest count must be between 1 and 30."
            )

        if time.minute != 0 or time.second != 0:
            raise serializers.ValidationError(
                "Only full-hour reservation slots are allowed."
            )

        now = timezone.localtime()

        if date < timezone.localdate():
            raise serializers.ValidationError(
                "You cannot reserve a past date."
            )

        if date == timezone.localdate() and time <= now.time().replace(
            second=0, microsecond=0
        ):
            raise serializers.ValidationError(
                "You cannot reserve a past time."
            )

        booked = Reservation.objects.filter(
            reservation_date=date,
            reservation_time=time,
            status__in=['pending', 'approved']
        )

        if self.instance:
            booked = booked.exclude(pk=self.instance.pk)

        total = booked.aggregate(
            total=Sum('number_of_guests')
        )['total'] or 0

        if total + guests > 30:
            raise serializers.ValidationError(
                f"Only {30 - total} seats are available for this time."
            )

        return data


# User Registration Serializer
class RegisterSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(max_length=15, write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'phone_number')

    def create(self, validated_data):
        phone = validated_data.pop('phone_number')
        password = validated_data.pop('password')

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        CustomerProfile.objects.create(
            user=user,
            phone_number=phone
        )

        customer_group, created = Group.objects.get_or_create(
            name='Customer'
        )
        user.groups.add(customer_group)

        return user


# User Profile Serializer
class ProfileSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(
        source='profile.phone_number',
        required=False
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'phone_number')
        read_only_fields = ('id', 'username')

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})

        instance.email = validated_data.get(
            'email',
            instance.email
        )
        instance.save()

        if 'phone_number' in profile_data:
            instance.profile.phone_number = profile_data['phone_number']
            instance.profile.save()

        return instance
