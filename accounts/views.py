from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta
from .forms import (
    LoginForm, RegistrationForm, UserProfileForm, UserRoleForm,
    PasswordChangeForm, UserUpdateForm
)
from .models import UserProfile, UserRole
from .decorators import admin_required, manager_required, staff_required
from inventory.models import Material, Category
from transactions.models import Transaction, StockAlert
from vendors.models import Vendor

from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required


@login_required
def get_chart_data(request):
    """AJAX endpoint to get chart data for different periods"""
    period = request.GET.get('period', 'week')
    today = timezone.now().date()

    # Set date range based on selected period
    if period == 'week':
        days = 7
        date_format = '%a'  # Mon, Tue, etc.
    elif period == 'month':
        days = 30
        date_format = '%d %b'  # 01 Jan, etc.
    elif period == 'quarter':
        days = 90
        date_format = '%d %b'  # 01 Jan, etc.
    else:
        days = 7
        date_format = '%a'

    start_date = today - timedelta(days=days - 1)

    dates = []
    inbound_data = []
    outbound_data = []

    # For large periods, we might want to aggregate by week/month
    if period == 'quarter' and days > 31:
        # Aggregate by week for quarterly view
        current_date = start_date
        while current_date <= today:
            week_end = min(current_date + timedelta(days=6), today)
            dates.append(f"{current_date.strftime('%d %b')}-{week_end.strftime('%d %b')}")

            inbound_data.append(Transaction.objects.filter(
                transaction_type='inbound',
                transaction_date__date__gte=current_date,
                transaction_date__date__lte=week_end
            ).count())

            outbound_data.append(Transaction.objects.filter(
                transaction_type='outbound',
                transaction_date__date__gte=current_date,
                transaction_date__date__lte=week_end
            ).count())

            current_date = week_end + timedelta(days=1)
    else:
        # Daily data for shorter periods
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            dates.append(current_date.strftime(date_format))

            inbound_data.append(Transaction.objects.filter(
                transaction_type='inbound',
                transaction_date__date=current_date
            ).count())

            outbound_data.append(Transaction.objects.filter(
                transaction_type='outbound',
                transaction_date__date=current_date
            ).count())

    return JsonResponse({
        'dates': dates,
        'inbound': inbound_data,
        'outbound': outbound_data
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.is_active:
                login(request, user)
                if hasattr(user, 'profile'):
                    user.profile.login_count += 1
                    user.profile.last_activity = timezone.now()
                    user.profile.save()
                messages.success(request, f'Welcome back, {username}!')
                return redirect('accounts:dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f'Welcome {username}! Account created.')
                return redirect('accounts:dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def dashboard(request):
    # Get counts with error handling
    try:
        total_materials = Material.objects.count()
    except:
        total_materials = 0

    try:
        low_stock_materials = Material.objects.filter(current_stock__lte=F('reorder_point')).count()
    except:
        low_stock_materials = 0

    try:
        total_vendors = Vendor.objects.filter(status='active').count()
    except:
        total_vendors = 0

    try:
        recent_transactions = Transaction.objects.all().order_by('-transaction_date')[:10]
    except:
        recent_transactions = []

    try:
        alerts = StockAlert.objects.filter(status='pending').select_related('material')[:5]
    except:
        alerts = []

    today = timezone.now().date()

    try:
        inbound_today = Transaction.objects.filter(
            transaction_type='inbound', transaction_date__date=today
        ).count()
    except:
        inbound_today = 0

    try:
        outbound_today = Transaction.objects.filter(
            transaction_type='outbound', transaction_date__date=today
        ).count()
    except:
        outbound_today = 0

    # Get weekly activity data for the chart
    end_date = today
    start_date = end_date - timedelta(days=6)  # Last 7 days

    # Initialize data arrays
    dates = []
    inbound_data = []
    outbound_data = []

    # Generate last 7 days
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        dates.append(current_date.strftime('%a'))  # Mon, Tue, etc.

        # Get inbound count for this date
        try:
            inbound_count = Transaction.objects.filter(
                transaction_type='inbound',
                transaction_date__date=current_date
            ).count()
        except:
            inbound_count = 0
        inbound_data.append(inbound_count)

        # Get outbound count for this date
        try:
            outbound_count = Transaction.objects.filter(
                transaction_type='outbound',
                transaction_date__date=current_date
            ).count()
        except:
            outbound_count = 0
        outbound_data.append(outbound_count)

    # Get stock distribution data
    try:
        total_stock_items = Material.objects.count()
    except:
        total_stock_items = 0

    if total_stock_items > 0:
        total_materials = Material.objects.count()
        total_value = Material.objects.aggregate(total=Sum(F('current_stock') * F('unit_cost')))['total'] or 0
        low_stock_count = Material.objects.filter(current_stock__lte=F('reorder_point')).count()
        # excess_stock_count = Material.objects.filter(current_stock__gte=F('maximum_stock')).count()

        normal_stock_count = Material.objects.filter(
            current_stock__gt=F('reorder_point'),
            current_stock__lt=F('maximum_stock')
        ).count()

        excess_stock_count = total_materials - normal_stock_count - low_stock_count

        # Calculate normal stock (everything else)
        # Important: Make sure we're not double-counting or missing items
        # Get all material IDs that are either low stock or excess stock
        low_stock_ids = Material.objects.filter(
            current_stock__lte=F('reorder_point')
        ).values_list('id', flat=True)

        excess_stock_ids = Material.objects.filter(
            current_stock__gt=F('reorder_point') * 2
        ).values_list('id', flat=True)

        # Combine the IDs (using set to avoid duplicates)
        excluded_ids = set(low_stock_ids) | set(excess_stock_ids)
    else:
        low_stock_count = excess_stock_count = normal_stock_count = 0

    context = {
        'total_materials': total_materials,
        'low_stock_materials': low_stock_materials,
        'total_vendors': total_vendors,
        'recent_transactions': recent_transactions,
        'alerts': alerts,
        'inbound_today': inbound_today,
        'outbound_today': outbound_today,
        'chart_dates': dates,
        'inbound_data': inbound_data,
        'outbound_data': outbound_data,
        'stock_distribution': {
            'normal': normal_stock_count,
            'low': low_stock_count,
            'excess': excess_stock_count,
        },
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        if hasattr(user, 'profile'):
            profile = user.profile
            profile.phone_number = request.POST.get('phone_number', '')
            profile.department = request.POST.get('department', '')
            profile.notification_email = request.POST.get('notification_email') == 'on'
            profile.notification_sms = request.POST.get('notification_sms') == 'on'
            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']
            profile.save()
        messages.success(request, 'Profile updated!')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            user = request.user
            if user.check_password(form.cleaned_data['current_password']):
                user.set_password(form.cleaned_data['new_password'])
                user.save()
                messages.success(request, 'Password changed. Please login again.')
                logout(request)
                return redirect('accounts:login')
            else:
                messages.error(request, 'Current password is incorrect.')
    else:
        form = PasswordChangeForm()
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
@admin_required
def user_list(request):
    users = User.objects.select_related('profile__role').all().order_by('-date_joined')
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(Q(username__icontains=search_query) | Q(email__icontains=search_query))
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(profile__role__name=role_filter)
    status = request.GET.get('status')
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)
    context = {
        'users': users,
        'roles': UserRole.objects.all(),
        'search_query': search_query,
        'role_filter': role_filter,
        'status': status,
    }
    return render(request, 'accounts/user_list.html', context)


@login_required
@admin_required
def user_detail(request, pk):
    user = get_object_or_404(User.objects.select_related('profile__role'), pk=pk)
    recent_transactions = Transaction.objects.filter(created_by=user)[:10]
    recent_materials = Material.objects.filter(created_by=user)[:10]
    context = {'user': user, 'recent_transactions': recent_transactions, 'recent_materials': recent_materials}
    return render(request, 'accounts/user_detail.html', context)


@login_required
@admin_required
def user_create(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)

        if form.is_valid() and profile_form.is_valid():
            user = form.save()
            profile = user.profile
            profile.phone_number = profile_form.cleaned_data['phone_number']
            profile.department = profile_form.cleaned_data['department']
            profile.employee_id = profile_form.cleaned_data['employee_id']
            profile.role = profile_form.cleaned_data['role']
            if 'avatar' in request.FILES:
                profile.avatar = request.FILES['avatar']
            profile.notification_email = profile_form.cleaned_data['notification_email']
            profile.notification_sms = profile_form.cleaned_data['notification_sms']
            profile.save()

            messages.success(request, f'User {user.username} created successfully!')
            return redirect('accounts:user_detail', pk=user.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegistrationForm()
        profile_form = UserProfileForm()

    context = {
        'form': form,
        'profile_form': profile_form,
        'title': 'Create User',
        'is_creating': True,
    }
    return render(request, 'accounts/user_form.html', context)


@login_required
@admin_required
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        default_role = UserRole.objects.filter(name='viewer').first()
        profile = UserProfile.objects.create(user=user, role=default_role)
        messages.info(request, f'Profile created for {user.username}')

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile_form.save()
            messages.success(request, f'User {user.username} updated!')
            return redirect('accounts:user_detail', pk=user.pk)
    else:
        form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)

    return render(request, 'accounts/user_form.html', {
        'form': form,
        'profile_form': profile_form,
        'user': user,
        'title': f'Edit User: {user.username}',
        'is_editing': True,
    })


@login_required
@admin_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'Cannot delete your own account.')
        return redirect('accounts:user_list')
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted!')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'user': user})


@login_required
@admin_required
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user != request.user:
        user.is_active = not user.is_active
        user.save()
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User {user.username} {status}!')
    return redirect('accounts:user_list')


@login_required
@admin_required
def admin_reset_password(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        new_pass = request.POST.get('new_password')
        confirm = request.POST.get('confirm_password')

        # Basic validation
        if not new_pass or not confirm:
            messages.error(request, 'Both password fields are required.')
        elif new_pass != confirm:
            messages.error(request, 'Passwords do not match.')
        elif len(new_pass) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            # Set the new password
            user.set_password(new_pass)
            user.save()

            # Update profile to track password change
            if hasattr(user, 'profile'):
                user.profile.last_activity = timezone.now()
                user.profile.save()

            messages.success(request, f'Password for {user.username} has been reset successfully!')
            return redirect('accounts:user_detail', pk=user.pk)

    return render(request, 'accounts/admin_reset_password.html', {'user': user})


@login_required
@admin_required
def role_list(request):
    roles = UserRole.objects.annotate(user_count=Count('userprofile')).all()
    return render(request, 'accounts/role_list.html', {'roles': roles})


@login_required
@admin_required
def role_create(request):
    if request.method == 'POST':
        form = UserRoleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Role created!')
            return redirect('accounts:role_list')
    else:
        form = UserRoleForm()
    return render(request, 'accounts/role_form.html', {'form': form, 'title': 'Create Role'})


@login_required
@admin_required
def role_update(request, pk):
    role = get_object_or_404(UserRole, pk=pk)
    if request.method == 'POST':
        form = UserRoleForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
            messages.success(request, 'Role updated!')
            return redirect('accounts:role_list')
    else:
        form = UserRoleForm(instance=role)
    return render(request, 'accounts/role_form.html', {'form': form, 'role': role, 'title': 'Edit Role'})


@login_required
@admin_required
def role_delete(request, pk):
    role = get_object_or_404(UserRole, pk=pk)
    if role.userprofile_set.exists():
        messages.error(request, 'Cannot delete role in use.')
        return redirect('accounts:role_list')
    if request.method == 'POST':
        role.delete()
        messages.success(request, 'Role deleted!')
        return redirect('accounts:role_list')
    return render(request, 'accounts/role_confirm_delete.html', {'role': role})