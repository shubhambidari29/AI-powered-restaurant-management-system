from google import genai
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction


from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group

from django.views.decorators.http import require_POST
from django.db.models import Q, Sum

from .models import FoodItem, Reservation
from .forms import SignUpForm,ReservationForm,UserUpdateForm,CustomerProfileForm,ReservationAdminForm,FoodItemForm
from .ai_service import ask_ai


@require_POST
def user_logout(request):
    logout(request)
    return redirect('home')

def is_admin(user):
    return user.is_authenticated and (
        user.is_superuser or user.groups.filter(name="Admin").exists()
    )


def is_staff(user):
    return user.is_authenticated and user.groups.filter(name="Staff").exists()


def is_customer(user):
    return user.is_authenticated and user.groups.filter(name="Customer").exists()

@login_required
@user_passes_test(is_staff)
def staff_dashboard(request):
    reservations = Reservation.objects.all().order_by(
        '-created_at'
    )

    return render(
        request,
        'restaurant/staff_dashboard.html',
        {'reservations': reservations}
    )

@login_required
@user_passes_test(is_staff)
@require_POST
def update_reservation_status(request, reservation_id):
    reservation = get_object_or_404(
        Reservation,
        id=reservation_id
    )

    new_status = request.POST.get('status')

    if new_status in ['approved', 'rejected']:
        if reservation.status == 'pending':
            reservation.status = new_status
            reservation.save()

    return redirect('staff_dashboard')

@login_required
@user_passes_test(is_customer)
def customer_dashboard(request):

    reservations = Reservation.objects.filter(
        customer=request.user
    ).order_by('-created_at')

    return render(
        request,
        'restaurant/customer_dashboard.html',
        {'reservations': reservations}
    )

@login_required
@user_passes_test(is_customer)
def make_reservation(request):

    if request.method == 'POST':
        form = ReservationForm(request.POST)

        if form.is_valid():

            reservation = form.save(commit=False)
            reservation.customer = request.user

            with transaction.atomic():

                booked_guests = Reservation.objects.filter(
                    reservation_date=reservation.reservation_date,
                    reservation_time=reservation.reservation_time,
                    status__in=['pending', 'approved']
                ).aggregate(
                    total=Sum('number_of_guests')
                )['total'] or 0

                remaining_seats = 30 - booked_guests

                if reservation.number_of_guests > remaining_seats:
                    form.add_error(
                        'number_of_guests',
                        f'Only {max(remaining_seats, 0)} seats are available.'
                    )

                else:
                    reservation.save()
                    return redirect('customer_dashboard')

    else:
        form = ReservationForm()

    return render(
        request,
        'restaurant/reservation_form.html',
        {'form': form}
    )

@login_required
@user_passes_test(is_customer)
@require_POST
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(
        Reservation,
        id=reservation_id,
        customer=request.user
    )

    if reservation.status in ['pending', 'approved']:
        reservation.status = 'cancelled'
        reservation.save()

    return redirect('customer_dashboard')

def home(request):
    food_items = FoodItem.objects.filter(is_available=True)[:6]

    return render(request, 'restaurant/home.html', {
        'food_items': food_items
    })


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save()

            customer_group, created = Group.objects.get_or_create(
                name='Customer'
            )
            user.groups.add(customer_group)

            login(request, user)
            return redirect('home')

    else:
        form = SignUpForm()

    return render(request, 'restaurant/signup.html', {
        'form': form
    })

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            next_url = request.GET.get('next')

            if next_url:
                return redirect(next_url)

            return redirect('home')

    else:
        form = AuthenticationForm(request)

    return render(request, 'restaurant/login.html', {
        'form': form
    })


def menu(request):
    food_items = FoodItem.objects.filter(is_available=True)

    search_query = request.GET.get('q', '')
    selected_category = request.GET.get('category', '')

    if search_query:
        food_items = food_items.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if selected_category:
        food_items = food_items.filter(
            category__iexact=selected_category
        )

    categories = (
        FoodItem.objects
        .filter(is_available=True)
        .values_list('category', flat=True)
        .distinct()
    )

    context = {
        'food_items': food_items,
        'categories': categories,
        'search_query': search_query,
        'selected_category': selected_category,
    }

    return render(request, 'restaurant/menu.html', context)





@login_required
@user_passes_test(is_customer)
def customer_profile(request):

    profile = request.user.profile

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = CustomerProfileForm(
            request.POST,
            instance=profile
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            return redirect('customer_profile')

    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = CustomerProfileForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }

    return render(
        request,
        'restaurant/customer_profile.html',
        context
    )


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):

    recent_reservations = Reservation.objects.select_related(
        'customer'
    ).order_by('-created_at')[:5]

    context = {
        'total_customers': User.objects.filter(
            groups__name='Customer'
        ).count(),

        'total_staff': User.objects.filter(
            groups__name='Staff'
        ).count(),

        'total_food_items': FoodItem.objects.count(),

        'total_reservations': Reservation.objects.count(),

        'pending_reservations': Reservation.objects.filter(
            status='pending'
        ).count(),

        'recent_reservations': recent_reservations,
    }

    return render(
        request,
        'restaurant/admin_dashboard.html',
        context
    )


@login_required
@user_passes_test(is_admin)
def manage_reservations(request):
    reservations = Reservation.objects.select_related(
        'customer'
    ).order_by('-created_at')

    search = request.GET.get('search', '')
    status = request.GET.get('status', '')

    if search:
        reservations = reservations.filter(
            customer__username__icontains=search
        )

    if status:
        reservations = reservations.filter(status=status)

    return render(request, 'restaurant/manage_reservations.html', {
        'reservations': reservations,
        'search': search,
        'selected_status': status,
    })

@login_required
@user_passes_test(is_admin)
@require_POST
def admin_update_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    new_status = request.POST.get('status')

    if new_status in ['approved', 'rejected']:
        if reservation.status == 'pending':
            reservation.status = new_status
            reservation.save()

    return redirect('manage_reservations')

@login_required
@user_passes_test(is_admin)
def edit_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    if request.method == 'POST':
        form = ReservationAdminForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()
            return redirect('manage_reservations')
    else:
        form = ReservationAdminForm(instance=reservation)

    return render(request, 'restaurant/edit_reservation.html', {
        'form': form
    })


@login_required
@user_passes_test(is_admin)
@require_POST
def delete_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    reservation.delete()
    return redirect('manage_reservations')

@login_required
@user_passes_test(is_admin)
def manage_food(request):
    food_items = FoodItem.objects.all()
    return render(request, 'restaurant/manage_food.html', {
        'food_items': food_items
    })

@login_required
@user_passes_test(is_admin)
def add_food(request):
    if request.method == 'POST':
        form = FoodItemForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return redirect('manage_food')
    else:
        form = FoodItemForm()

    return render(request, 'restaurant/add_food.html', {
        'form': form
    })

@login_required
@user_passes_test(is_admin)
def edit_food(request, food_id):
    food = get_object_or_404(FoodItem, id=food_id)

    if request.method == 'POST':
        form = FoodItemForm(request.POST, request.FILES, instance=food)
        if form.is_valid():
            form.save()
            return redirect('manage_food')
    else:
        form = FoodItemForm(instance=food)

    return render(request, 'restaurant/edit_food.html', {'form': form})

@login_required
@user_passes_test(is_admin)
@require_POST
def delete_food(request, food_id):
    food = get_object_or_404(FoodItem, id=food_id)
    food.delete()
    return redirect('manage_food')



@login_required
@user_passes_test(is_admin)
def manage_users(request):
    users = User.objects.exclude(
        is_superuser=True
    ).exclude(
        groups__name='Admin'
    ).prefetch_related('groups').distinct().order_by('username')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        role = request.POST.get('role')

        if role in ['Customer', 'Staff']:
            selected_user = get_object_or_404(users, id=user_id)
            group, created = Group.objects.get_or_create(name=role)

            selected_user.groups.remove(
                *Group.objects.filter(name__in=['Customer', 'Staff'])
            )
            selected_user.groups.add(group)

        return redirect('manage_users')

    return render(request, 'restaurant/manage_users.html', {
        'users': users
    })

@login_required
@user_passes_test(is_admin)
@require_POST
def delete_user(request, user_id):
    users = User.objects.exclude(
        is_superuser=True
    ).exclude(groups__name='Admin')

    user = get_object_or_404(users, id=user_id)

    if user != request.user:
        user.delete()

    return redirect('manage_users')


def ai_assistant(request):

    if request.method == 'POST':
        question = request.POST.get('message', '').strip()

        if not question:
            return JsonResponse({
                'reply': 'Please enter a question.'
            }, status=400)

        try:
            answer = ask_ai(question)

            return JsonResponse({
                'reply': answer
            })

        except Exception as e:
            print("AI Error:", repr(e))

            return JsonResponse({
                'reply': 'Sorry, our AI assistant is temporarily unavailable.'
            }, status=503)

    return render(request, 'restaurant/ai_assistant.html')