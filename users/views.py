from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .decorators import role_required


def login_view(request):
    """
    Handle user login and redirect to appropriate dashboard based on role.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                auth_login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """
    Handle user logout.
    """
    auth_logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')


@login_required
def dashboard_view(request):
    """
    Main dashboard view that redirects to role-specific dashboards.
    """
    user = request.user
    role = user.role

    # Redirect to role-specific dashboard
    if role == 'admin':
        return redirect('admin_dashboard')
    elif role == 'registrar':
        return redirect('registrar_dashboard')
    elif role == 'professor':
        return redirect('professor_dashboard')
    elif role == 'student':
        return redirect('student_dashboard')
    elif role == 'admission':
        return redirect('admission_dashboard')
    elif role == 'dean':
        return redirect('dean_dashboard')
    else:
        messages.error(request, 'Invalid user role.')
        return redirect('login')


# Role-specific Dashboard Views
@role_required('admin')
def admin_dashboard(request):
    """
    Admin dashboard with system overview and links to all modules.
    """
    from enrollment.models import Student, Term, Section
    from academics.models import Program, Subject
    from grades.models import Grade
    from users.models import User

    context = {
        'total_students': Student.objects.count(),
        'total_programs': Program.objects.count(),
        'total_subjects': Subject.objects.count(),
        'active_terms': Term.objects.filter(is_active=True).count(),
        'total_sections': Section.objects.count(),
        'total_users': User.objects.count(),
        'total_professors': User.objects.filter(role='professor').count(),
    }
    return render(request, 'dashboards/admin_dashboard.html', context)


@role_required('registrar')
def registrar_dashboard(request):
    """
    Registrar dashboard with terms, sections, curriculum control, and transferee management.
    """
    from enrollment.models import Term, Section, TransfereeEnrollment
    from academics.models import Program, Curriculum

    # Transferee statistics
    pending_transferees = TransfereeEnrollment.objects.filter(
        status='pending_tor_verification'
    ).count()

    tor_verified_transferees = TransfereeEnrollment.objects.filter(
        status='tor_verified'
    ).count()

    context = {
        'active_terms': Term.objects.filter(is_active=True, archived=False),
        'recent_sections': Section.objects.all().order_by('-created_at')[:10],
        'total_programs': Program.objects.count(),
        'total_curricula': Curriculum.objects.filter(active=True).count(),
        'pending_transferees': pending_transferees,
        'tor_verified_transferees': tor_verified_transferees,
    }
    return render(request, 'dashboards/registrar_dashboard.html', context)


@role_required('professor')
def professor_dashboard(request):
    """
    Professor dashboard showing assigned sections and grading access.
    """
    from enrollment.models import Section

    sections = Section.objects.filter(professor=request.user).select_related('subject', 'term')

    context = {
        'assigned_sections': sections,
        'total_sections': sections.count(),
    }
    return render(request, 'dashboards/professor_dashboard.html', context)


@role_required('student')
def student_dashboard(request):
    """
    Student dashboard with enrollment and grade viewer.
    Shows enrollment eligibility based on past term completion and grade posting.
    """
    from enrollment.models import Student, StudentSubject, Enrollment, Term
    from enrollment.student_enrollment_views import can_student_enroll

    try:
        student = Student.objects.get(user=request.user)
        enrolled_subjects = StudentSubject.objects.filter(student=student).select_related('subject', 'term', 'section')

        # Check enrollment eligibility with comprehensive checks
        active_term = Term.objects.filter(is_active=True, archived=False, level=student.program.level).first()

        can_enroll = False
        enrollment_status = None
        enrollment_message = None
        enrollment_details = {}

        if active_term:
            can_enroll, enrollment_message, enrollment_details = can_student_enroll(student, active_term)

        context = {
            'student': student,
            'enrolled_subjects': enrolled_subjects,
            'total_units': sum([ss.subject.units for ss in enrolled_subjects if ss.status == 'enrolled']),
            'has_active_enrollment': not can_enroll and enrollment_details.get('reason') == 'already_enrolled',
            'can_enroll': can_enroll,
            'enrollment_message': enrollment_message,
            'enrollment_details': enrollment_details,
            'active_term': active_term,
        }
    except Student.DoesNotExist:
        context = {
            'student': None,
            'enrolled_subjects': [],
            'total_units': 0,
            'has_active_enrollment': False,
            'can_enroll': False,
            'enrollment_message': None,
            'enrollment_details': {},
            'active_term': None,
        }

    return render(request, 'dashboards/student_dashboard.html', context)


@role_required('admission')
def admission_dashboard(request):
    """
    Admission dashboard for managing new applicants.
    """
    from enrollment.models import Student

    recent_students = Student.objects.all().order_by('-created_at')[:20]

    context = {
        'recent_students': recent_students,
        'total_students': Student.objects.count(),
        'active_students': Student.objects.filter(status='active').count(),
    }
    return render(request, 'dashboards/admission_dashboard.html', context)


@role_required('dean')
def dean_dashboard(request):
    """
    Dean dashboard with academic analytics and oversight.
    """
    from enrollment.models import Student, Section
    from academics.models import Program

    context = {
        'total_students': Student.objects.count(),
        'active_students': Student.objects.filter(status='active').count(),
        'total_sections': Section.objects.count(),
        'programs': Program.objects.all(),
    }
    return render(request, 'dashboards/dean_dashboard.html', context)


@login_required
@role_required('student')
def student_account_settings(request):
    """
    Student account settings page - allows students to edit username and password.
    """
    from django.contrib.auth import update_session_auth_hash
    from audit.models import AuditTrail

    user = request.user

    if request.method == 'POST':
        action = request.POST.get('action')

        # Change Username
        if action == 'change_username':
            new_username = request.POST.get('new_username', '').strip()
            confirm_password = request.POST.get('confirm_password', '')

            # Validation
            errors = []

            if not new_username:
                errors.append('New username cannot be empty.')

            if len(new_username) < 3:
                errors.append('Username must be at least 3 characters long.')

            if len(new_username) > 150:
                errors.append('Username cannot exceed 150 characters.')

            # Check if username already exists
            if new_username != user.username and User.objects.filter(username=new_username).exists():
                errors.append('This username is already taken.')

            # Verify password
            if not user.check_password(confirm_password):
                errors.append('Incorrect password. Username change cancelled.')

            if errors:
                context = {
                    'user': user,
                    'errors': errors,
                    'action': 'change_username',
                }
                return render(request, 'account_settings.html', context)

            # Change username
            old_username = user.username
            user.username = new_username
            user.save()

            # Audit trail
            AuditTrail.objects.create(
                actor=user,
                action='change_username',
                entity='User',
                entity_id=user.id,
                new_value_json={
                    'old_username': old_username,
                    'new_username': new_username,
                }
            )

            messages.success(request, f'Username changed successfully! Your new username is @{new_username}')
            return redirect('account_settings')

        # Change Password
        elif action == 'change_password':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            # Validation
            errors = []

            if not user.check_password(current_password):
                errors.append('Current password is incorrect.')

            if len(new_password) < 8:
                errors.append('New password must be at least 8 characters long.')

            if new_password != confirm_password:
                errors.append('New passwords do not match.')

            if new_password == current_password:
                errors.append('New password must be different from current password.')

            if errors:
                context = {
                    'user': user,
                    'errors': errors,
                    'action': 'change_password',
                }
                return render(request, 'account_settings.html', context)

            # Change password
            user.set_password(new_password)
            user.save()

            # Audit trail
            AuditTrail.objects.create(
                actor=user,
                action='change_password',
                entity='User',
                entity_id=user.id,
                new_value_json={
                    'action': 'password_changed',
                }
            )

            # Keep user logged in after password change
            update_session_auth_hash(request, user)

            messages.success(request, 'Password changed successfully!')
            return redirect('account_settings')

    context = {
        'user': user,
    }
    return render(request, 'account_settings.html', context)
