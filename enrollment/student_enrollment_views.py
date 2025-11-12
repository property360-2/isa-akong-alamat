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
from academics.models import Subject, CurriculumSubject, Prereq, Program
from audit.models import AuditTrail
from grades.models import Grade
import json
from decimal import Decimal


# ==================== HELPER FUNCTIONS ====================

def get_student_grade_history(student):
    """
    Get all subjects the student has taken with grades and status.
    Returns a list of StudentSubject records with related grade data.
    """
    past_subjects = StudentSubject.objects.filter(
        student=student,
        status__in=['completed', 'failed', 'inc', 'repeat_required']
    ).select_related('subject', 'term', 'professor').order_by('-term__start_date')

    grade_history = []
    for ss in past_subjects:
        grade = Grade.objects.filter(student_subject=ss).first()
        grade_history.append({
            'student_subject': ss,
            'subject': ss.subject,
            'term': ss.term,
            'professor': ss.professor,
            'status': ss.status,
            'grade': grade.grade if grade else 'Not Posted',
            'grade_value': float(grade.grade) if grade else None,
        })

    return grade_history


def get_completed_subjects_with_grades(student):
    """
    Get all subjects with 'completed' status and their grades.
    Returns a dict with subject_id as key and grade value as value.
    """
    completed = StudentSubject.objects.filter(
        student=student,
        status='completed'
    ).select_related('subject')

    result = {}
    for ss in completed:
        grade = Grade.objects.filter(student_subject=ss).first()
        if grade:
            result[ss.subject_id] = {
                'grade_value': float(grade.grade),
                'subject': ss.subject,
                'status': 'completed',
            }

    return result


def get_incomplete_subjects(student):
    """
    Get all subjects with 'inc' (incomplete) status.
    Returns a list of StudentSubject records.
    """
    return StudentSubject.objects.filter(
        student=student,
        status='inc'
    ).select_related('subject', 'term')


def get_student_current_level(student):
    """
    Determine the current year/semester level of the student based on
    their completed/failed subjects.

    Returns (year_level, term_no) tuple.
    Defaults to (1, 1) for new students.
    """
    if not student.curriculum:
        return (1, 1)

    # Get all subjects the student has taken (completed or failed)
    taken_subjects = StudentSubject.objects.filter(
        student=student,
        status__in=['completed', 'failed']
    ).values_list('subject_id', flat=True)

    # Get all curriculum subjects taken by this student
    completed_curriculum = CurriculumSubject.objects.filter(
        curriculum=student.curriculum,
        subject_id__in=taken_subjects
    ).values_list('year_level', 'term_no')

    if not completed_curriculum:
        return (1, 1)

    # Find the highest year/semester completed
    max_level = max(completed_curriculum, key=lambda x: (x[0], x[1]))
    year_level, term_no = max_level

    # Advance to next semester/year
    if term_no == 1:
        return (year_level, 2)
    else:
        return (year_level + 1, 1)


def check_prerequisite_with_grades(student, subject, passing_grade=None):
    """
    Check if student has met all prerequisites for a subject.
    Accepts both 'completed' subjects AND 'inc' subjects where the grade
    meets or exceeds the passing grade.

    Returns dict with:
    - 'can_take': bool - whether student can take this subject
    - 'unmet': list of unmet prerequisite subjects
    - 'with_inc': list of prerequisites met via incomplete status
    """
    if not passing_grade:
        # Get passing grade from student's program
        passing_grade = float(student.program.passing_grade)

    # Get all prerequisites for this subject
    prereqs = Prereq.objects.filter(subject=subject).select_related('prereq_subject')

    if not prereqs.exists():
        return {'can_take': True, 'unmet': [], 'with_inc': []}

    unmet = []
    with_inc = []

    for prereq in prereqs:
        prereq_subject = prereq.prereq_subject

        # Check if completed
        completed_record = StudentSubject.objects.filter(
            student=student,
            subject=prereq_subject,
            status='completed'
        ).first()

        if completed_record:
            continue

        # Check if incomplete with passing grade
        inc_record = StudentSubject.objects.filter(
            student=student,
            subject=prereq_subject,
            status='inc'
        ).first()

        if inc_record:
            grade = Grade.objects.filter(student_subject=inc_record).first()
            if grade and float(grade.grade) >= passing_grade:
                with_inc.append({
                    'subject': prereq_subject,
                    'grade': grade.grade,
                    'status': 'incomplete_but_passing'
                })
                continue

        # Prerequisite not met
        unmet.append(prereq_subject)

    return {
        'can_take': len(unmet) == 0,
        'unmet': unmet,
        'with_inc': with_inc,
    }


def get_available_subjects_for_student(student, active_term, include_inc_path=False):
    """
    Get available subjects for student to enroll in.

    If include_inc_path=False: Only show subjects at student's current level
                               where all prerequisites are 'completed'.
    If include_inc_path=True: Show subjects at student's current level
                              and one level ahead if student has incomplete subjects.

    Returns list of dicts with subject info and prerequisite status.
    """
    # Get student's current level
    year_level, term_no = get_student_current_level(student)

    # Get incomplete subjects
    incomplete_subjects = get_incomplete_subjects(student)
    has_inc = incomplete_subjects.exists()

    # Start with current level
    available_levels = [(year_level, term_no)]

    # If student has incomplete subjects, also show next level
    if has_inc and include_inc_path:
        if term_no == 2:
            available_levels.append((year_level + 1, 1))

    # Get curriculum subjects for available levels
    curriculum_subjects = CurriculumSubject.objects.filter(
        curriculum=student.curriculum,
        year_level__in=[level[0] for level in available_levels],
        term_no__in=[level[1] for level in available_levels]
    ).select_related('subject')

    # Check prerequisite status for each subject
    subjects_info = []
    passing_grade = float(student.program.passing_grade)

    for cs in curriculum_subjects:
        subject = cs.subject

        # Check if already enrolled/taken
        already_taken = StudentSubject.objects.filter(
            student=student,
            subject=subject,
            term=active_term
        ).exists()

        if already_taken:
            continue

        # Check prerequisites
        prereq_check = check_prerequisite_with_grades(student, subject, passing_grade)

        subjects_info.append({
            'subject': subject,
            'curriculum_level': (cs.year_level, cs.term_no),
            'current_level': (year_level, term_no),
            'can_take': prereq_check['can_take'],
            'unmet_prereqs': prereq_check['unmet'],
            'with_inc_prereqs': prereq_check['with_inc'],
            'is_available': prereq_check['can_take'],
        })

    return subjects_info, has_inc


# ==================== VIEWS ====================

@login_required
def student_enroll_subjects(request):
    """
    Subject enrollment view for students.
    Shows available subjects based on student's current level and incomplete status.
    Handles prerequisite checking for both completed and incomplete (but passing) subjects.
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

    # Get student's current level
    year_level, term_no = get_student_current_level(student)

    # Get available subjects with prerequisite info
    available_subjects, has_incomplete = get_available_subjects_for_student(student, active_term, include_inc_path=True)

    # Get grade history
    grade_history = get_student_grade_history(student)

    # Get incomplete subjects
    incomplete_subjects = get_incomplete_subjects(student)

    if request.method == 'POST':
        try:
            selected_subject_ids = request.POST.getlist('selected_subjects')
            selected_subject_ids = [int(sid) for sid in selected_subject_ids]

            if not selected_subject_ids:
                messages.error(request, 'Please select at least one subject.')
                context = {
                    'student': student,
                    'active_term': active_term,
                    'available_subjects': available_subjects,
                    'grade_history': grade_history,
                    'incomplete_subjects': incomplete_subjects,
                    'has_incomplete': has_incomplete,
                    'current_level': (year_level, term_no),
                    'selected_subject_ids': selected_subject_ids,
                }
                return render(request, 'student/enroll_subjects.html', context)

            # Validate selected subjects
            selected_subjects = Subject.objects.filter(id__in=selected_subject_ids)

            # Check unit total
            total_units = sum(Decimal(str(s.units)) for s in selected_subjects)

            if total_units > 30:
                messages.error(request, f'Total units ({total_units}) exceeds maximum of 30 units.')
                context = {
                    'student': student,
                    'active_term': active_term,
                    'available_subjects': available_subjects,
                    'grade_history': grade_history,
                    'incomplete_subjects': incomplete_subjects,
                    'has_incomplete': has_incomplete,
                    'current_level': (year_level, term_no),
                    'selected_subject_ids': selected_subject_ids,
                }
                return render(request, 'student/enroll_subjects.html', context)

            # Check prerequisites for selected subjects using new logic
            for subject in selected_subjects:
                prereq_check = check_prerequisite_with_grades(student, subject)
                if not prereq_check['can_take']:
                    unmet_codes = ', '.join([p.code for p in prereq_check['unmet']])
                    messages.error(request, f'Subject {subject.code} has unmet prerequisites: {unmet_codes}')
                    context = {
                        'student': student,
                        'active_term': active_term,
                        'available_subjects': available_subjects,
                        'grade_history': grade_history,
                        'incomplete_subjects': incomplete_subjects,
                        'has_incomplete': has_incomplete,
                        'current_level': (year_level, term_no),
                        'selected_subject_ids': selected_subject_ids,
                    }
                    return render(request, 'student/enroll_subjects.html', context)

            # Check for double enrollment
            for subject_id in selected_subject_ids:
                existing = StudentSubject.objects.filter(
                    student=student,
                    subject_id=subject_id,
                    term=active_term
                ).exists()
                if existing:
                    subject = Subject.objects.get(id=subject_id)
                    messages.error(request, f'You are already enrolled in {subject.code} this term.')
                    context = {
                        'student': student,
                        'active_term': active_term,
                        'available_subjects': available_subjects,
                        'grade_history': grade_history,
                        'incomplete_subjects': incomplete_subjects,
                        'has_incomplete': has_incomplete,
                        'current_level': (year_level, term_no),
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
        'available_subjects': available_subjects,
        'grade_history': grade_history,
        'incomplete_subjects': incomplete_subjects,
        'has_incomplete': has_incomplete,
        'current_level': (year_level, term_no),
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
def student_grade_history(request):
    """
    Display student's grade history across all terms.
    Shows all completed, failed, incomplete, and repeat required subjects.
    """
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student record not found.')
        return redirect('student_dashboard')

    # Get grade history
    grade_history = get_student_grade_history(student)

    # Calculate GPA (only from completed subjects)
    completed_with_grades = [
        gh for gh in grade_history
        if gh['status'] == 'completed' and gh['grade_value'] is not None
    ]

    gpa = None
    if completed_with_grades:
        total_grade = sum(gh['grade_value'] for gh in completed_with_grades)
        gpa = total_grade / len(completed_with_grades)

    context = {
        'student': student,
        'grade_history': grade_history,
        'gpa': gpa,
        'total_completed': len([gh for gh in grade_history if gh['status'] == 'completed']),
        'total_failed': len([gh for gh in grade_history if gh['status'] == 'failed']),
        'total_incomplete': len([gh for gh in grade_history if gh['status'] == 'inc']),
    }
    return render(request, 'student/grade_history.html', context)


@login_required
@require_http_methods(["GET"])
def api_check_prerequisites(request):
    """
    API endpoint to check if prerequisites are met for a subject.
    Returns JSON with prerequisite information including incomplete but passing subjects.
    """
    subject_id = request.GET.get('subject_id')

    if not subject_id:
        return JsonResponse({'error': 'subject_id required'}, status=400)

    try:
        student = Student.objects.get(user=request.user)
        subject = Subject.objects.get(id=subject_id)
    except (Student.DoesNotExist, Subject.DoesNotExist):
        return JsonResponse({'error': 'Not found'}, status=404)

    # Use new prerequisite checking logic
    prereq_check = check_prerequisite_with_grades(student, subject)

    # Get prerequisites
    prereqs = Prereq.objects.filter(subject=subject).select_related('prereq_subject')

    prerequisite_info = []

    for prereq in prereqs:
        prereq_subject = prereq.prereq_subject
        is_met = False
        status = 'unmet'

        # Check if completed
        if StudentSubject.objects.filter(
            student=student,
            subject=prereq_subject,
            status='completed'
        ).exists():
            is_met = True
            status = 'completed'
        # Check if incomplete but passing
        elif prereq_check['with_inc']:
            for inc_prereq in prereq_check['with_inc']:
                if inc_prereq['subject'].id == prereq_subject.id:
                    is_met = True
                    status = 'incomplete_but_passing'
                    break

        prerequisite_info.append({
            'code': prereq_subject.code,
            'title': prereq_subject.title,
            'is_met': is_met,
            'status': status,
        })

    return JsonResponse({
        'subject_code': subject.code,
        'prerequisites': prerequisite_info,
        'all_met': prereq_check['can_take'],
        'unmet_count': len(prereq_check['unmet']),
        'unmet_subjects': [{'code': s.code, 'title': s.title} for s in prereq_check['unmet']],
    })
