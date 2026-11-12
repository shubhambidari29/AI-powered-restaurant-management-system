
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api_views import (
    FoodViewSet,
    ReservationViewSet,
    RegisterAPIView,
    ProfileAPIView,
    LoginAPIView,
    LogoutAPIView
)

# API Router
router = DefaultRouter()

router.register('food', FoodViewSet, basename='api-food')
router.register(
    'reservations',
    ReservationViewSet,
    basename='api-reservations'
)

urlpatterns = [
    path('', include(router.urls)),

    # User APIs
    path('register/', RegisterAPIView.as_view(), name='api-register'),
    path('profile/', ProfileAPIView.as_view(), name='api-profile'),
    path('login/', LoginAPIView.as_view(), name='api-login'),
    path('logout/', LogoutAPIView.as_view(), name='api-logout'),
]
