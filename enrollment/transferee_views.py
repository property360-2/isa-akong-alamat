"""
Transferee enrollment management views.
Handles manual enrollment of transferees by registrar/admission staff.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.db import transaction
from django.http import JsonResponse
from users.decorators import role_required
from .models import TransfereeEnrollment, TransfereeCredit, Student
from users.models import User
from audit.models import AuditTrail
from datetime import datetime
import secrets
import string


def generate_transferee_password():
    """Generate a secure random password for transferee account"""
    password_chars = string.ascii_uppercase + string.ascii_lowercase + string.digits + "!@#$%&"
    generated_password = (
        secrets.choice(string.ascii_uppercase) +
        secrets.choice(string.ascii_uppercase) +
        secrets.choice(string.ascii_lowercase) +
        secrets.choice(string.ascii_lowercase) +
        secrets.choice(string.digits) +
        secrets.choice(string.digits) +
        secrets.choice("!@#$%&") +
        ''.join(secrets.choice(password_chars) for _ in range(5))
    )
    # Shuffle to make it less predictable
    return ''.join(secrets.SystemRandom().sample(generated_password, len(generated_password)))


@login_required
@role_required('registrar', 'admission')
def transferee_list(request):
    """
    List all transferee enrollments with filtering and search.
    """
    transferees = TransfereeEnrollment.objects.all()

    # Filtering
    status = request.GET.get('status')
    transfer_type = request.GET.get('transfer_type')
    search = request.GET.get('search')

    if status:
        transferees = transferees.filter(status=status)
    if transfer_type:
        transferees = transferees.filter(transfer_type=transfer_type)
    if search:
        transferees = transferees.filter(
            first_name__icontains=search
        ) | transferees.filter(
            last_name__icontains=search
        ) | transferees.filter(
            email__icontains=search
        )

    context = {
        'transferees': transferees,
        'status_choices': TransfereeEnrollment.STATUS_CHOICES,
        'transfer_type_choices': TransfereeEnrollment.TRANSFER_TYPE_CHOICES,
        'current_status': status,
        'current_transfer_type': transfer_type,
        'search_query': search,
    }

    return render(request, 'transferee/transferee_list.html', context)


@login_required
@role_required('registrar', 'admission')
def transferee_create(request):
    """
    Create new transferee enrollment record.
    Registrar/Admission manually inputs transferee credentials.
    """
    from academics.models import Program, Curriculum

    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        suffix = request.POST.get('suffix', '').strip()
        email = request.POST.get('email', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        transfer_type = request.POST.get('transfer_type')
        source_school = request.POST.get('source_school', '').strip()
        source_program = request.POST.get('source_program', '').strip()
        program_id = request.POST.get('program')
        curriculum_id = request.POST.get('curriculum')
        notes = request.POST.get('notes', '').strip()

        # Validation
        errors = []

        if not first_name:
            errors.append('First name is required.')
        if not last_name:
            errors.append('Last name is required.')
        if not email:
            errors.append('Email is required.')
        if '@' not in email:
            errors.append('Please enter a valid email address.')
        if not transfer_type:
            errors.append('Transfer type is required.')
        if not source_school:
            errors.append('Source school name is required.')
        if not source_program:
            errors.append('Source program name is required.')
        if not program_id:
            errors.append('Target program is required.')
        if not curriculum_id:
            errors.append('Target curriculum is required.')

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            errors.append('Email already exists in the system.')

        # Check if transferee email already exists
        if TransfereeEnrollment.objects.filter(email=email).exists():
            errors.append('This email is already registered as a transferee.')

        if errors:
            context = {
                'programs': Program.objects.all(),
                'errors': errors,
                'form_data': request.POST,
            }
            return render(request, 'transferee/transferee_form.html', context)

        try:
            # Get program and curriculum
            program = Program.objects.get(pk=program_id)
            curriculum = Curriculum.objects.get(pk=curriculum_id)

            # Create transferee enrollment
            transferee = TransfereeEnrollment.objects.create(
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
                suffix=suffix,
                email=email,
                mobile=mobile,
                transfer_type=transfer_type,
                source_school=source_school,
                source_program=source_program,
                program=program,
                curriculum=curriculum,
                notes=notes,
            )

            # Audit trail
            AuditTrail.objects.create(
                actor=request.user,
                action='create_transferee_enrollment',
                entity='TransfereeEnrollment',
                entity_id=transferee.id,
                new_value_json={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'transfer_type': transfer_type,
                    'source_school': source_school,
                    'program': program.name,
                }
            )

            messages.success(request, f'Transferee enrollment created for {first_name} {last_name}. Status: Pending Credential Input')
            return redirect('enrollment:transferee_detail', pk=transferee.id)

        except Program.DoesNotExist:
            messages.error(request, 'Selected program not found.')
        except Curriculum.DoesNotExist:
            messages.error(request, 'Selected curriculum not found.')
        except Exception as e:
            messages.error(request, f'Error creating transferee enrollment: {str(e)}')

    # GET request
    from academics.models import Program
    context = {
        'programs': Program.objects.all(),
    }
    return render(request, 'transferee/transferee_form.html', context)


@login_required
@role_required('registrar', 'admission')
def transferee_detail(request, pk):
    """
    View transferee enrollment details, verify TOR, and manage credits.
    """
    transferee = get_object_or_404(TransfereeEnrollment, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        # Verify TOR
        if action == 'verify_tor':
            if transferee.status != 'pending_tor_verification':
                messages.error(request, 'Can only verify TOR for enrollments pending verification.')
                return redirect('enrollment:transferee_detail', pk=pk)

            with transaction.atomic():
                transferee.status = 'tor_verified'
                transferee.tor_verified = True
                transferee.tor_verified_at = datetime.now()
                transferee.tor_verified_by = request.user
                transferee.save()

                # Audit trail
                AuditTrail.objects.create(
                    actor=request.user,
                    action='verify_transferee_tor',
                    entity='TransfereeEnrollment',
                    entity_id=transferee.id,
                    new_value_json={'tor_verified': True}
                )

            messages.success(request, 'TOR verified successfully! Ready to create account.')
            return redirect('enrollment:transferee_detail', pk=pk)

        # Create account
        elif action == 'create_account':
            if transferee.status != 'tor_verified':
                messages.error(request, 'TOR must be verified before creating account.')
                return redirect('enrollment:transferee_detail', pk=pk)

            if transferee.created_user:
                messages.warning(request, 'Account already created for this transferee.')
                return redirect('enrollment:transferee_detail', pk=pk)

            try:
                with transaction.atomic():
                    # Generate username
                    generated_username = f"{transferee.last_name.lower()}{transferee.first_name.lower()}{secrets.token_hex(3)}"

                    # Check if username exists
                    while User.objects.filter(username=generated_username).exists():
                        generated_username = f"{transferee.last_name.lower()}{transferee.first_name.lower()}{secrets.token_hex(3)}"

                    # Generate password
                    generated_password = generate_transferee_password()

                    # Create user
                    user = User.objects.create_user(
                        username=generated_username,
                        email=transferee.email,
                        password=generated_password,
                        first_name=transferee.first_name,
                        last_name=transferee.last_name,
                        role='student',
                    )

                    # Create student record
                    student = Student.objects.create(
                        user=user,
                        program=transferee.program,
                        curriculum=transferee.curriculum,
                        status='active',
                        onboarding_complete=True,  # Transferee is pre-onboarded
                    )

                    # Generate and assign student ID
                    from enrollment.freshman_views import generate_student_id
                    student.student_id = generate_student_id(student)
                    student.save()

                    # Credit subjects from TOR
                    credits = transferee.credits.filter(status='credited')
                    for credit in credits:
                        if credit.subject:  # Only credit if subject is mapped
                            StudentSubject = __import__('enrollment.models', fromlist=['StudentSubject']).StudentSubject
                            # Use active term for credits
                            from enrollment.models import Term
                            active_term = Term.objects.filter(is_active=True).first()
                            if active_term:
                                StudentSubject.objects.create(
                                    student=student,
                                    subject=credit.subject,
                                    term=active_term,
                                    status='completed',
                                )

                    # Update transferee record
                    transferee.created_user = user
                    transferee.account_created_at = datetime.now()
                    transferee.account_created_by = request.user
                    transferee.status = 'account_created'
                    transferee.save()

                    # Audit trail
                    AuditTrail.objects.create(
                        actor=request.user,
                        action='create_transferee_account',
                        entity='TransfereeEnrollment',
                        entity_id=transferee.id,
                        new_value_json={
                            'username': generated_username,
                            'student_id': student.student_id,
                        }
                    )

                # Store credentials in session for display
                request.session['transferee_username'] = generated_username
                request.session['transferee_password'] = generated_password
                request.session['transferee_student_id'] = student.student_id

                messages.success(request, 'Account created successfully! Credentials have been generated.')
                return redirect('enrollment:transferee_account_details', pk=pk)

            except Exception as e:
                messages.error(request, f'Error creating account: {str(e)}')
                return redirect('enrollment:transferee_detail', pk=pk)

        # Reject transferee
        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', '').strip()
            if not rejection_reason:
                messages.error(request, 'Rejection reason is required.')
                return redirect('enrollment:transferee_detail', pk=pk)

            transferee.status = 'rejected'
            transferee.rejection_reason = rejection_reason
            transferee.save()

            # Audit trail
            AuditTrail.objects.create(
                actor=request.user,
                action='reject_transferee',
                entity='TransfereeEnrollment',
                entity_id=transferee.id,
                new_value_json={'rejection_reason': rejection_reason}
            )

            messages.success(request, 'Transferee enrollment rejected.')
            return redirect('enrollment:transferee_list')

    context = {
        'transferee': transferee,
        'credits': transferee.credits.all(),
    }
    return render(request, 'transferee/transferee_detail.html', context)


@login_required
@role_required('registrar', 'admission')
def transferee_account_details(request, pk):
    """
    Display generated account credentials for transferee.
    """
    transferee = get_object_or_404(TransfereeEnrollment, pk=pk)

    if transferee.status != 'account_created':
        messages.error(request, 'Account not yet created for this transferee.')
        return redirect('enrollment:transferee_detail', pk=pk)

    username = request.session.pop('transferee_username', None)
    password = request.session.pop('transferee_password', None)
    student_id = request.session.pop('transferee_student_id', None)

    context = {
        'transferee': transferee,
        'username': username,
        'password': password,
        'student_id': student_id,
    }
    return render(request, 'transferee/transferee_account_details.html', context)


@login_required
@role_required('student')
def transferee_login_enroll(request):
    """
    Allow transferee to login and start enrolling subjects.
    This is the same as regular student enrollment.
    """
    # Transferee students use the regular student enrollment flow
    from enrollment.student_enrollment_views import student_enroll_subjects
    return student_enroll_subjects(request)
