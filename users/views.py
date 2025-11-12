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
    Registrar dashboard with terms, sections, and curriculum control.
    """
    from enrollment.models import Term, Section
    from academics.models import Program, Curriculum

    context = {
        'active_terms': Term.objects.filter(is_active=True, archived=False),
        'recent_sections': Section.objects.all().order_by('-created_at')[:10],
        'total_programs': Program.objects.count(),
        'total_curricula': Curriculum.objects.filter(active=True).count(),
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
