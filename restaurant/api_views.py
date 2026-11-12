
from django.db import transaction
from django.db.models import Sum
from django.contrib.auth import authenticate, login, logout

from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from .models import FoodItem, Reservation
from .serializers import (
    FoodItemSerializer,
    ReservationSerializer,
    RegisterSerializer,
    ProfileSerializer
)


# Check user roles
def is_admin(user):
    return user.is_authenticated and (
        user.is_superuser
        or user.groups.filter(name='Admin').exists()
    )


def is_staff_member(user):
    return user.is_authenticated and (
        user.is_staff
        or is_admin(user)
        or user.groups.filter(name='Staff').exists()
    )


# Food API
class FoodViewSet(viewsets.ModelViewSet):
    serializer_class = FoodItemSerializer

    def get_queryset(self):
        queryset = FoodItem.objects.all()

        if not is_admin(self.request.user):
            queryset = queryset.filter(is_available=True)

        search = self.request.query_params.get('search')
        category = self.request.query_params.get('category')

        if search:
            queryset = queryset.filter(name__icontains=search)

        if category:
            queryset = queryset.filter(category__iexact=category)

        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]

        return [permissions.IsAuthenticated()]

    def check_admin(self):
        if not is_admin(self.request.user):
            return Response(
                {'error': 'Only admins can manage food items.'},
                status=status.HTTP_403_FORBIDDEN
            )

    def create(self, request, *args, **kwargs):
        error = self.check_admin()
        if error:
            return error
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        error = self.check_admin()
        if error:
            return error
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        error = self.check_admin()
        if error:
            return error
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        error = self.check_admin()
        if error:
            return error
        return super().destroy(request, *args, **kwargs)


# Reservation API
class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if is_staff_member(self.request.user):
            return Reservation.objects.all()

        return Reservation.objects.filter(
            customer=self.request.user
        )

    def perform_create(self, serializer):
        if is_staff_member(self.request.user):
            raise permissions.PermissionDenied(
                "Staff and admins cannot create customer reservations."
            )

        with transaction.atomic():
            date = serializer.validated_data['reservation_date']
            time = serializer.validated_data['reservation_time']
            guests = serializer.validated_data['number_of_guests']

            booked = Reservation.objects.filter(
                reservation_date=date,
                reservation_time=time,
                status__in=['pending', 'approved']
            ).aggregate(
                total=Sum('number_of_guests')
            )['total'] or 0

            if booked + guests > 30:
                raise ValidationError(
                    "Not enough seats available for this time slot."
                )

            serializer.save(customer=self.request.user)

    # Cancel reservation
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        reservation = self.get_object()

        if reservation.status not in ['pending', 'approved']:
            return Response(
                {'error': 'This reservation cannot be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reservation.status = 'cancelled'
        reservation.save()

        return Response({'message': 'Reservation cancelled.'})

    # Approve reservation
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        if not is_staff_member(request.user):
            return Response(
                {'error': 'Staff or admin permission required.'},
                status=status.HTTP_403_FORBIDDEN
            )

        reservation = self.get_object()

        if reservation.status != 'pending':
            return Response(
                {'error': 'Only pending reservations can be approved.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reservation.status = 'approved'
        reservation.save()

        return Response({'message': 'Reservation approved.'})

    # Reject reservation
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        if not is_staff_member(request.user):
            return Response(
                {'error': 'Staff or admin permission required.'},
                status=status.HTTP_403_FORBIDDEN
            )

        reservation = self.get_object()

        if reservation.status != 'pending':
            return Response(
                {'error': 'Only pending reservations can be rejected.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        reservation.status = 'rejected'
        reservation.save()

        return Response({'message': 'Reservation rejected.'})


# User Registration API
class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


# User Profile API
class ProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# Login API
class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:
            return Response(
                {'error': 'Invalid username or password.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        login(request, user)

        return Response({'message': 'Login successful.'})


# Logout API
class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'message': 'Logout successful.'})
