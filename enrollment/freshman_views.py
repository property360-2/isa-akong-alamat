"""
Freshman enrollment flow views.
Handles new student registration and onboarding.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from enrollment.models import Student, Term
from academics.models import Program
from users.models import User
from audit.models import AuditTrail


def freshman_landing(request):
    """
    Freshman enrollment landing page.
    Unauthenticated entry point for new freshman students.
    """
    # If user is already authenticated and has completed onboarding, redirect to portal
    if request.user.is_authenticated:
        try:
            student = Student.objects.get(user=request.user)
            if student.onboarding_complete:
                return redirect('enrollments:student_dashboard')
        except Student.DoesNotExist:
            pass

    return render(request, 'freshman/landing.html')


@csrf_protect
def freshman_register(request):
    """
    Student registration form - creates account and temporary Student record.
    Automatically attaches the active term.
    """
    if request.user.is_authenticated:
        try:
            student = Student.objects.get(user=request.user)
            if student.onboarding_complete:
                return redirect('enrollments:student_dashboard')
            return redirect('freshman_select_program')
        except Student.DoesNotExist:
            pass

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        is_freshman = request.POST.get('is_freshman')

        # Validation
        errors = []

        if not full_name:
            errors.append('Full name is required.')
        if not email:
            errors.append('Email is required.')
        if not username:
            errors.append('Username is required.')
        if not password:
            errors.append('Password is required.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if not is_freshman:
            errors.append('You must confirm you are a new freshman applicant.')

        # Check if username already exists
        if username and User.objects.filter(username=username).exists():
            errors.append('Username already exists.')

        # Check if email already exists
        if email and User.objects.filter(email=email).exists():
            errors.append('Email already exists.')

        if errors:
            context = {
                'errors': errors,
                'form_data': {
                    'full_name': full_name,
                    'email': email,
                    'mobile': mobile,
                    'username': username,
                }
            }
            return render(request, 'freshman/register.html', context)

        try:
            with transaction.atomic():
                # Get active term - if none, create error message
                active_term = Term.objects.filter(is_active=True, archived=False).first()
                if not active_term:
                    messages.error(request, 'No active term available. Please try again later.')
                    return render(request, 'freshman/register.html')

                # Parse full name (simple split on space)
                name_parts = full_name.rsplit(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ''

                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role='student',
                )

                # Create student record
                student = Student.objects.create(
                    user=user,
                    status='inactive',  # Will become active after onboarding
                    onboarding_complete=False,
                )

                # Audit trail
                AuditTrail.objects.create(
                    actor=user,
                    action='register',
                    entity='User',
                    entity_id=user.id,
                    new_value_json={
                        'username': username,
                        'email': email,
                        'full_name': full_name,
                    }
                )

            # Log the user in OUTSIDE the transaction to avoid session conflicts
            login(request, user)

            messages.success(request, f'Welcome, {first_name}! Please select your program.')
            return redirect('freshman_select_program')

        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'freshman/register.html')

    return render(request, 'freshman/register.html')


def freshman_select_program(request):
    """
    Program (course) selection page.
    Student selects their desired program and is attached to active curriculum.
    """
    if not request.user.is_authenticated:
        return redirect('freshman_register')

    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return redirect('freshman_register')

    if student.onboarding_complete:
        return redirect('enrollments:student_dashboard')

    if request.method == 'POST':
        program_id = request.POST.get('program_id')

        if not program_id:
            messages.error(request, 'Please select a program.')
            programs = Program.objects.all().order_by('level', 'name')
            return render(request, 'freshman/select_program.html', {'programs': programs})

        try:
            program = Program.objects.get(pk=program_id)

            # Get active curriculum for this program
            active_curriculum = program.curricula.filter(active=True).first()
            if not active_curriculum:
                messages.error(request, f'No active curriculum available for {program.name}.')
                programs = Program.objects.all().order_by('level', 'name')
                return render(request, 'freshman/select_program.html', {'programs': programs})

            # Update student with program and curriculum
            student.program = program
            student.curriculum = active_curriculum
            student.save()

            # Audit trail
            AuditTrail.objects.create(
                actor=request.user,
                action='select_program',
                entity='Student',
                entity_id=student.id,
                new_value_json={
                    'program': program.name,
                    'curriculum': active_curriculum.version,
                }
            )

            messages.success(request, f'Program "{program.name}" selected successfully!')
            return redirect('freshman_review_account')

        except Program.DoesNotExist:
            messages.error(request, 'Selected program not found.')
            programs = Program.objects.all().order_by('level', 'name')
            return render(request, 'freshman/select_program.html', {'programs': programs})

    # GET request
    programs = Program.objects.all().order_by('level', 'name')
    return render(request, 'freshman/select_program.html', {'programs': programs})


def freshman_review_account(request):
    """
    Account review page - student verifies info before completing onboarding.
    Marks onboarding as complete and activates student status.
    """
    if not request.user.is_authenticated:
        return redirect('freshman_register')

    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return redirect('freshman_register')

    if student.onboarding_complete:
        return redirect('enrollments:student_dashboard')

    if not student.program or not student.curriculum:
        messages.error(request, 'Please complete program selection first.')
        return redirect('freshman_select_program')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Mark onboarding as complete
                student.onboarding_complete = True
                student.status = 'active'
                student.save()

                # Audit trail
                AuditTrail.objects.create(
                    actor=request.user,
                    action='complete_onboarding',
                    entity='Student',
                    entity_id=student.id,
                    new_value_json={
                        'onboarding_complete': True,
                        'status': 'active',
                        'program': student.program.name,
                        'curriculum': student.curriculum.version,
                    }
                )

            # Add message AFTER transaction completes
            messages.success(request, 'Account confirmed! Proceeding to subject enrollment.')
            return redirect('freshman_enroll_subjects')

        except Exception as e:
            messages.error(request, f'Error confirming account: {str(e)}')
            return render(request, 'freshman/review_account.html', {'student': student})

    # GET request - show review page
    active_term = Term.objects.filter(is_active=True, archived=False, level=student.program.level).first()

    context = {
        'student': student,
        'active_term': active_term,
    }
    return render(request, 'freshman/review_account.html', context)


def freshman_enroll_subjects(request):
    """
    Subject enrollment page - Step 4 of freshman enrollment.
    Placeholder for future subject selection functionality.
    """
    if not request.user.is_authenticated:
        return redirect('freshman_register')

    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return redirect('freshman_register')

    if not student.onboarding_complete:
        messages.error(request, 'Please complete account review first.')
        return redirect('freshman_review_account')

    context = {
        'student': student,
    }
    return render(request, 'freshman/enroll_subjects.html', context)
