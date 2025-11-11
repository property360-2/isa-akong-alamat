from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def role_required(*allowed_roles):
    """
    Decorator to restrict view access based on user role.

    Usage:
        @role_required('admin', 'registrar')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                messages.error(request, 'You must be logged in to access this page.')
                return redirect('login')

            # Check if user has the required role
            if request.user.role not in allowed_roles:
                messages.error(request, f'Access denied. This page is only accessible to: {", ".join(allowed_roles)}')
                raise PermissionDenied

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def login_required_with_role(view_func):
    """
    Decorator to ensure user is authenticated and redirects to appropriate dashboard.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to access this page.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper
