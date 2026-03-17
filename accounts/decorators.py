from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Please login.')
                return redirect('accounts:login')
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if hasattr(request.user, 'profile') and request.user.profile.role:
                if request.user.profile.role.name in allowed_roles:
                    return view_func(request, *args, **kwargs)
            messages.error(request, 'Permission denied.')
            return redirect('accounts:dashboard')
        return _wrapped_view
    return decorator

def admin_required(view_func):
    return role_required(['admin'])(view_func)

def manager_required(view_func):
    return role_required(['admin', 'manager'])(view_func)

def staff_required(view_func):
    return role_required(['admin', 'manager', 'staff'])(view_func)