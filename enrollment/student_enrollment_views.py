"""
Student subject enrollment views.
Handles subject selection, validation, and enrollment confirmation.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from enrollment.models import Student, Term, StudentSubject, Enrollment
from academics.models import Subject, CurriculumSubject, Prereq
from audit.models import AuditTrail
import json
from decimal import Decimal


@login_required
def student_enroll_subjects(request):
    """
    Subject enrollment view for students.
    Shows subjects from student's curriculum for 1st year, 1st semester.
    Students can add/remove subjects with unit limit validation.
    """
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student record not found.')
        return redirect('student_dashboard')

    # Check if student has completed onboarding
    if not student.onboarding_complete:
        messages.error(request, 'Please complete onboarding first.')
        return redirect('freshman:landing')

    # Get active term
    active_term = Term.objects.filter(is_active=True, archived=False, level=student.program.level).first()
    if not active_term:
        messages.error(request, 'No active term available.')
        return redirect('student_dashboard')

    # Check if already enrolled for this term
    existing_enrollment = Enrollment.objects.filter(student=student, term=active_term).first()
    if existing_enrollment:
        messages.info(request, 'You have already completed enrollment for this term.')
        return redirect('enrollment:view_enrollment', term_id=active_term.id)

    # Get curriculum subjects for 1st year, 1st semester
    curriculum_subjects = CurriculumSubject.objects.filter(
        curriculum=student.curriculum,
        year_level=1,
        term_no=1
    ).select_related('subject')

    # Get student's completed subjects for prerequisite checking
    completed_subjects = StudentSubject.objects.filter(
        student=student,
        status__in=['completed']
    ).values_list('subject_id', flat=True)

    # Build subject list with prerequisite info
    subjects_with_prereqs = []
    for cs in curriculum_subjects:
        subject = cs.subject

        # Get prerequisites
        prereqs = Prereq.objects.filter(subject=subject).select_related('prereq_subject')
        prereq_list = [p.prereq_subject for p in prereqs]

        # Check if prerequisites are met
        unmet_prereqs = [p for p in prereq_list if p.id not in completed_subjects]

        subjects_with_prereqs.append({
            'subject': subject,
            'prereqs': prereq_list,
            'unmet_prereqs': unmet_prereqs,
            'is_available': len(unmet_prereqs) == 0,
        })

    if request.method == 'POST':
        try:
            selected_subject_ids = request.POST.getlist('selected_subjects')
            selected_subject_ids = [int(sid) for sid in selected_subject_ids]

            # Validate selected subjects
            selected_subjects = Subject.objects.filter(id__in=selected_subject_ids)

            # Check unit total
            total_units = sum(Decimal(str(s.units)) for s in selected_subjects)

            if total_units > 30:
                messages.error(request, f'Total units ({total_units}) exceeds maximum of 30 units.')
                context = {
                    'student': student,
                    'active_term': active_term,
                    'subjects_with_prereqs': subjects_with_prereqs,
                    'selected_subject_ids': selected_subject_ids,
                }
                return render(request, 'student/enroll_subjects.html', context)

            # Check prerequisites for selected subjects
            for subject_id in selected_subject_ids:
                subject = Subject.objects.get(id=subject_id)
                prereqs = Prereq.objects.filter(subject=subject).values_list('prereq_subject_id', flat=True)
                unmet = [p for p in prereqs if p not in completed_subjects]
                if unmet:
                    messages.error(request, f'Subject {subject.code} has unmet prerequisites.')
                    context = {
                        'student': student,
                        'active_term': active_term,
                        'subjects_with_prereqs': subjects_with_prereqs,
                        'selected_subject_ids': selected_subject_ids,
                    }
                    return render(request, 'student/enroll_subjects.html', context)

            # Store selection in session for confirmation
            request.session['enrollment_subjects'] = selected_subject_ids
            request.session['enrollment_total_units'] = float(total_units)

            return redirect('enrollment:confirm_enrollment')

        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    context = {
        'student': student,
        'active_term': active_term,
        'subjects_with_prereqs': subjects_with_prereqs,
    }
    return render(request, 'student/enroll_subjects.html', context)


@login_required
def student_confirm_enrollment(request):
    """
    Enrollment confirmation page.
    Shows summary of selected subjects and requires final confirmation.
    """
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student record not found.')
        return redirect('student_dashboard')

    # Get enrollment data from session
    selected_subject_ids = request.session.get('enrollment_subjects', [])
    total_units = request.session.get('enrollment_total_units', 0)

    if not selected_subject_ids:
        messages.error(request, 'No subjects selected.')
        return redirect('enrollment:enroll_subjects')

    # Get active term
    active_term = Term.objects.filter(is_active=True, archived=False, level=student.program.level).first()
    if not active_term:
        messages.error(request, 'No active term available.')
        return redirect('student_dashboard')

    # Get selected subjects
    selected_subjects = Subject.objects.filter(id__in=selected_subject_ids)

    if request.method == 'POST':
        # Confirm enrollment - lock it
        try:
            with transaction.atomic():
                # Create Enrollment record (locked)
                enrollment, created = Enrollment.objects.get_or_create(
                    student=student,
                    term=active_term,
                    defaults={
                        'total_units': Decimal(str(total_units)),
                        'status': 'confirmed'
                    }
                )

                if not created:
                    messages.error(request, 'Enrollment for this term already exists.')
                    return render(request, 'student/confirm_enrollment.html', {
                        'student': student,
                        'active_term': active_term,
                        'selected_subjects': selected_subjects,
                        'total_units': total_units,
                    })

                # Create StudentSubject records
                # In a real system, you'd assign sections based on availability
                # For now, we'll use the first available section
                for subject in selected_subjects:
                    # Get an available section for this subject and term
                    section = subject.sections.filter(term=active_term, status='open').first()
                    if not section:
                        section = subject.sections.filter(term=active_term).first()

                    # Get the first professor assigned to this section (if section exists)
                    professor = None
                    if section:
                        professor = section.professors.first()

                    # Create StudentSubject record even if section/professor is not assigned
                    # They can be assigned later by the registrar
                    StudentSubject.objects.create(
                        student=student,
                        subject=subject,
                        term=active_term,
                        section=section,
                        professor=professor,
                        status='enrolled'
                    )

                # Audit trail
                AuditTrail.objects.create(
                    actor=request.user,
                    action='confirm_enrollment',
                    entity='Enrollment',
                    entity_id=enrollment.id,
                    new_value_json={
                        'term': active_term.name,
                        'total_units': float(total_units),
                        'subject_count': len(selected_subject_ids),
                    }
                )

            # Clear session data
            del request.session['enrollment_subjects']
            del request.session['enrollment_total_units']

            messages.success(request, 'Enrollment confirmed successfully!')
            return redirect('enrollment:view_enrollment', term_id=active_term.id)

        except Exception as e:
            messages.error(request, f'Error confirming enrollment: {str(e)}')
            return render(request, 'student/confirm_enrollment.html', {
                'student': student,
                'active_term': active_term,
                'selected_subjects': selected_subjects,
                'total_units': total_units,
            })

    context = {
        'student': student,
        'active_term': active_term,
        'selected_subjects': selected_subjects,
        'total_units': total_units,
    }
    return render(request, 'student/confirm_enrollment.html', context)


@login_required
def student_view_enrollment(request, term_id):
    """
    View enrolled subjects for a specific term.
    Shows locked enrollment once confirmed.
    """
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student record not found.')
        return redirect('student_dashboard')

    term = get_object_or_404(Term, id=term_id)

    # Check if student is enrolled in this term
    enrollment = Enrollment.objects.filter(student=student, term=term).first()
    if not enrollment:
        messages.error(request, 'No enrollment found for this term.')
        return redirect('student_dashboard')

    # Get student's subjects for this term
    subjects = StudentSubject.objects.filter(
        student=student,
        term=term,
        status='enrolled'
    ).select_related('subject', 'section', 'professor')

    context = {
        'student': student,
        'term': term,
        'enrollment': enrollment,
        'subjects': subjects,
    }
    return render(request, 'student/view_enrollment.html', context)


@login_required
@require_http_methods(["GET"])
def api_check_prerequisites(request):
    """
    API endpoint to check if prerequisites are met for a subject.
    Returns JSON with prerequisite information.
    """
    subject_id = request.GET.get('subject_id')

    if not subject_id:
        return JsonResponse({'error': 'subject_id required'}, status=400)

    try:
        student = Student.objects.get(user=request.user)
        subject = Subject.objects.get(id=subject_id)
    except (Student.DoesNotExist, Subject.DoesNotExist):
        return JsonResponse({'error': 'Not found'}, status=404)

    # Get prerequisites
    prereqs = Prereq.objects.filter(subject=subject).select_related('prereq_subject')

    # Get student's completed subjects
    completed_subjects = StudentSubject.objects.filter(
        student=student,
        status='completed'
    ).values_list('subject_id', flat=True)

    prerequisite_info = []
    unmet_count = 0

    for prereq in prereqs:
        is_met = prereq.prereq_subject.id in completed_subjects
        if not is_met:
            unmet_count += 1
        prerequisite_info.append({
            'code': prereq.prereq_subject.code,
            'title': prereq.prereq_subject.title,
            'is_met': is_met,
        })

    return JsonResponse({
        'subject_code': subject.code,
        'prerequisites': prerequisite_info,
        'all_met': unmet_count == 0,
        'unmet_count': unmet_count,
    })
