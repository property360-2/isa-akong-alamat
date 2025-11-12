"""
Freshman enrollment flow views.
Handles new student registration and onboarding.

Flow: Landing → Create Credentials → Select Course → Confirm Credentials → Complete
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db import transaction
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
                return redirect('student_dashboard')
        except Student.DoesNotExist:
            pass

    return render(request, 'freshman/landing.html')


@csrf_protect
def freshman_create_credentials(request):
    """
    Step 1: Create Credentials Form
    Students enter: First Name, Middle Name, Surname, Suffix (optional)
    Email, Mobile Number (optional)
    Password / Confirm Password
    Username is auto-generated from: Surname + FirstName + MiddleName
    """
    if request.user.is_authenticated:
        try:
            student = Student.objects.get(user=request.user)
            if not student.onboarding_complete:
                return redirect('freshman:select_course')
            return redirect('student_dashboard')
        except Student.DoesNotExist:
            pass

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        surname = request.POST.get('surname', '').strip()
        suffix = request.POST.get('suffix', '').strip()
        email = request.POST.get('email', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        is_freshman = request.POST.get('is_freshman')

        # Validation
        errors = []

        if not first_name:
            errors.append('First name is required.')
        if not surname:
            errors.append('Surname is required.')
        if not middle_name:
            errors.append('Middle name is required.')
        if not email:
            errors.append('Email is required.')
        if not password:
            errors.append('Password is required.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if not is_freshman:
            errors.append('You must confirm you are a new freshman applicant.')

        # Auto-generate username from surname + first name + middle name
        # Format: surname + firstname + middlename (all lowercase, no spaces)
        generated_username = f"{surname.lower()}{first_name.lower()}{middle_name.lower()}"

        # Check if username already exists
        if User.objects.filter(username=generated_username).exists():
            errors.append(f'Username "{generated_username}" already exists. Please contact registrar.')

        # Check if email already exists
        if email and User.objects.filter(email=email).exists():
            errors.append('Email already exists.')

        if errors:
            context = {
                'errors': errors,
                'form_data': {
                    'first_name': first_name,
                    'middle_name': middle_name,
                    'surname': surname,
                    'suffix': suffix,
                    'email': email,
                    'mobile': mobile,
                    'generated_username': generated_username,
                }
            }
            return render(request, 'freshman/create_credentials.html', context)

        try:
            with transaction.atomic():
                # Get active term - if none, create error message
                active_term = Term.objects.filter(is_active=True, archived=False).first()
                if not active_term:
                    messages.error(request, 'No active term available. Please try again later.')
                    return render(request, 'freshman/create_credentials.html')

                # Create user with auto-generated username
                user = User.objects.create_user(
                    username=generated_username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=surname,  # Store surname in last_name
                    role='student',
                )

                # Create student record
                student = Student.objects.create(
                    user=user,
                    status='inactive',  # Will become active after onboarding
                    onboarding_complete=False,
                )

                # Store additional info in documents_json for now
                student.documents_json = {
                    'middle_name': middle_name,
                    'suffix': suffix,
                    'mobile': mobile,
                }
                student.save()

                # Audit trail
                AuditTrail.objects.create(
                    actor=user,
                    action='create_credentials',
                    entity='User',
                    entity_id=user.id,
                    new_value_json={
                        'username': generated_username,
                        'email': email,
                        'first_name': first_name,
                        'middle_name': middle_name,
                        'surname': surname,
                        'suffix': suffix,
                    }
                )

            # Log the user in OUTSIDE the transaction to avoid session conflicts
            login(request, user)

            messages.success(request, f'Welcome, {first_name}! Please select your course.')
            return redirect('freshman:select_course')

        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'freshman/create_credentials.html')

    return render(request, 'freshman/create_credentials.html')


def freshman_select_course(request):
    """
    Step 2: Course (Program) Selection Page
    Student selects their desired program and is attached to active curriculum.
    """
    if not request.user.is_authenticated:
        return redirect('freshman:create_credentials')

    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return redirect('freshman:create_credentials')

    if student.onboarding_complete:
        return redirect('student_dashboard')

    if request.method == 'POST':
        program_id = request.POST.get('program_id')

        if not program_id:
            messages.error(request, 'Please select a program.')
            programs = Program.objects.all().order_by('level', 'name')
            return render(request, 'freshman/select_course.html', {'programs': programs})

        try:
            program = Program.objects.get(pk=program_id)

            # Get active curriculum for this program
            active_curriculum = program.curricula.filter(active=True).first()
            if not active_curriculum:
                messages.error(request, f'No active curriculum available for {program.name}.')
                programs = Program.objects.all().order_by('level', 'name')
                return render(request, 'freshman/select_course.html', {'programs': programs})

            # Update student with program and curriculum
            student.program = program
            student.curriculum = active_curriculum
            student.save()

            # Audit trail
            AuditTrail.objects.create(
                actor=request.user,
                action='select_course',
                entity='Student',
                entity_id=student.id,
                new_value_json={
                    'program': program.name,
                    'curriculum': active_curriculum.version,
                }
            )

            messages.success(request, f'Program "{program.name}" selected successfully!')
            return redirect('freshman:confirm_credentials')

        except Program.DoesNotExist:
            messages.error(request, 'Selected program not found.')
            programs = Program.objects.all().order_by('level', 'name')
            return render(request, 'freshman/select_course.html', {'programs': programs})

    # GET request
    programs = Program.objects.all().order_by('level', 'name')
    return render(request, 'freshman/select_course.html', {'programs': programs})


def freshman_confirm_credentials(request):
    """
    Step 3: Confirm Credentials Page
    Student verifies all info before completing enrollment.
    Marks onboarding as complete and activates student status.
    """
    if not request.user.is_authenticated:
        return redirect('freshman:create_credentials')

    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return redirect('freshman:create_credentials')

    if student.onboarding_complete:
        return redirect('student_dashboard')

    if not student.program or not student.curriculum:
        messages.error(request, 'Please complete course selection first.')
        return redirect('freshman_select_course')

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
            messages.success(request, 'Enrollment confirmed! Welcome to Richwell College.')
            return redirect('freshman:enrollment_complete')

        except Exception as e:
            messages.error(request, f'Error confirming enrollment: {str(e)}')
            return render(request, 'freshman/confirm_credentials.html', {'student': student})

    # GET request - show confirmation page
    active_term = Term.objects.filter(is_active=True, archived=False, level=student.program.level).first()

    # Get middle name and suffix from documents_json
    middle_name = student.documents_json.get('middle_name', '')
    suffix = student.documents_json.get('suffix', '')

    context = {
        'student': student,
        'active_term': active_term,
        'middle_name': middle_name,
        'suffix': suffix,
    }
    return render(request, 'freshman/confirm_credentials.html', context)


def freshman_enrollment_complete(request):
    """
    Enrollment completion page - confirmation of successful enrollment.
    """
    if not request.user.is_authenticated:
        return redirect('freshman:create_credentials')

    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return redirect('freshman:create_credentials')

    if not student.onboarding_complete:
        messages.error(request, 'Please complete enrollment first.')
        return redirect('freshman_confirm_credentials')

    context = {
        'student': student,
    }
    return render(request, 'freshman/enrollment_complete.html', context)
