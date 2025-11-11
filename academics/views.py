from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from users.decorators import role_required
from audit.models import AuditTrail
from .models import Program, Curriculum, Subject, Prereq, CurriculumSubject
import json


# ==================== MAIN INDEX ====================
@role_required('registrar')
def academics_index(request):
    """Main academics page with tabs for programs, curricula, and subjects"""
    active_tab = request.GET.get('tab', 'programs')
    context = {
        'active_tab': active_tab,
    }
    return render(request, 'registrar/academics/index.html', context)


# ==================== PROGRAMS ====================
@role_required('registrar')
def programs_list(request):
    """List all programs"""
    programs = Program.objects.all().order_by('-created_at')
    return render(request, 'registrar/academics/programs_list.html', {'programs': programs})


@role_required('registrar')
def program_create(request):
    """Create a new program"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            level = request.POST.get('level')
            passing_grade = request.POST.get('passing_grade')

            # Validation
            if not all([name, level, passing_grade]):
                return JsonResponse({'success': False, 'message': 'All fields are required'}, status=400)

            # Create program
            program = Program.objects.create(
                name=name,
                level=level,
                passing_grade=passing_grade
            )

            # Audit trail
            AuditTrail.objects.create(
                actor=request.user,
                action='create',
                entity='Program',
                entity_id=program.id,
                new_value_json={'name': name, 'level': level, 'passing_grade': str(passing_grade)}
            )

            return JsonResponse({
                'success': True,
                'message': f'Program "{name}" created successfully',
                'program': {
                    'id': program.id,
                    'name': program.name,
                    'level': program.level,
                    'passing_grade': str(program.passing_grade),
                }
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    # GET request - return modal form
    return render(request, 'registrar/academics/program_form.html')


@role_required('registrar')
def program_update(request, pk):
    """Update an existing program"""
    program = get_object_or_404(Program, pk=pk)

    if request.method == 'POST':
        try:
            # Store old values for audit
            old_values = {
                'name': program.name,
                'level': program.level,
                'passing_grade': str(program.passing_grade)
            }

            # Update fields
            program.name = request.POST.get('name')
            program.level = request.POST.get('level')
            program.passing_grade = request.POST.get('passing_grade')
            program.save()

            # Audit trail
            AuditTrail.objects.create(
                actor=request.user,
                action='update',
                entity='Program',
                entity_id=program.id,
                old_value_json=old_values,
                new_value_json={
                    'name': program.name,
                    'level': program.level,
                    'passing_grade': str(program.passing_grade)
                }
            )

            return JsonResponse({
                'success': True,
                'message': f'Program "{program.name}" updated successfully',
                'program': {
                    'id': program.id,
                    'name': program.name,
                    'level': program.level,
                    'passing_grade': str(program.passing_grade),
                }
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    # GET request - return pre-filled modal form
    return render(request, 'registrar/academics/program_form.html', {'program': program})


@role_required('registrar')
def program_delete(request, pk):
    """Delete (deactivate) a program"""
    if request.method == 'POST':
        program = get_object_or_404(Program, pk=pk)

        try:
            # Store values for audit
            old_values = {
                'name': program.name,
                'level': program.level,
                'passing_grade': str(program.passing_grade)
            }

            # Audit trail before deletion
            AuditTrail.objects.create(
                actor=request.user,
                action='delete',
                entity='Program',
                entity_id=program.id,
                old_value_json=old_values
            )

            program_name = program.name
            program.delete()

            return JsonResponse({
                'success': True,
                'message': f'Program "{program_name}" deleted successfully'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)


@role_required('registrar')
def program_subjects(request, pk):
    """View all subjects linked under a program's curricula"""
    program = get_object_or_404(Program, pk=pk)

    # Get all curricula for this program
    curricula = Curriculum.objects.filter(program=program).prefetch_related(
        'curriculumsubject_set__subject'
    )

    # Collect all unique subjects across all curricula
    subjects_set = {}
    for curriculum in curricula:
        for cs in curriculum.curriculumsubject_set.all():
            subject = cs.subject
            if subject.id not in subjects_set:
                subjects_set[subject.id] = {
                    'subject': subject,
                    'curricula': []
                }
            subjects_set[subject.id]['curricula'].append({
                'curriculum': curriculum,
                'year_level': cs.year_level,
                'term_no': cs.term_no
            })

    program_subjects = list(subjects_set.values())

    context = {
        'program': program,
        'program_subjects': program_subjects,
        'curricula_count': curricula.count(),
    }
    return render(request, 'registrar/academics/program_subjects_modal.html', context)


@role_required('registrar')
def program_subject_archive(request, program_pk, subject_pk):
    """Archive a subject from a program"""
    if request.method == 'POST':
        try:
            program = get_object_or_404(Program, pk=program_pk)
            subject = get_object_or_404(Subject, pk=subject_pk)

            old_values = {
                'archived': subject.archived,
                'program': program.name,
            }

            # Archive the subject
            subject.archived = True
            subject.save()

            # Audit trail
            AuditTrail.objects.create(
                actor=request.user,
                action='archive',
                entity='Subject',
                entity_id=subject.id,
                old_value_json=old_values,
                new_value_json={
                    'archived': True,
                    'program': program.name,
                }
            )

            return JsonResponse({
                'success': True,
                'message': f'Subject "{subject.code}" has been archived successfully'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)


# ==================== CURRICULA ====================
@role_required('registrar')
def curricula_list(request):
    """List all curricula"""
    curricula = Curriculum.objects.select_related('program').all().order_by('-created_at')
    programs = Program.objects.all()
    return render(request, 'registrar/academics/curricula_list.html', {
        'curricula': curricula,
        'programs': programs
    })


@role_required('registrar')
def curriculum_create(request):
    """Create a new curriculum"""
    if request.method == 'POST':
        try:
            program_id = request.POST.get('program_id')
            version = request.POST.get('version')
            effective_sy = request.POST.get('effective_sy')

            # Validation
            if not all([program_id, version, effective_sy]):
                return JsonResponse({'success': False, 'message': 'All fields are required'}, status=400)

            program = get_object_or_404(Program, pk=program_id)

            # Create curriculum (inactive by default)
            curriculum = Curriculum.objects.create(
                program=program,
                version=version,
                effective_sy=effective_sy,
                active=False
            )

            # Audit trail
            AuditTrail.objects.create(
                actor=request.user,
                action='create',
                entity='Curriculum',
                entity_id=curriculum.id,
                new_value_json={
                    'program_id': program_id,
                    'program_name': program.name,
                    'version': version,
                    'effective_sy': effective_sy,
                    'active': False
                }
            )

            return JsonResponse({
                'success': True,
                'message': f'Curriculum "{version}" created successfully',
                'curriculum': {
                    'id': curriculum.id,
                    'program_name': program.name,
                    'version': version,
                    'effective_sy': effective_sy,
                    'active': False
                }
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    # GET request - return modal form
    programs = Program.objects.all()
    return render(request, 'registrar/academics/curriculum_form.html', {'programs': programs})


@role_required('registrar')
def curriculum_detail(request, pk):
    """View curriculum details with subjects, hierarchy, and prerequisite map"""
    curriculum = get_object_or_404(Curriculum.objects.select_related('program'), pk=pk)
    curriculum_subjects = CurriculumSubject.objects.filter(
        curriculum=curriculum
    ).select_related('subject').prefetch_related('subject__subject_prereqs__prereq_subject').order_by('year_level', 'term_no')

    # Build hierarchy data grouped by year and semester
    hierarchy = {}
    for cs in curriculum_subjects:
        year_key = f"Year {cs.year_level}"
        if cs.term_no == 1:
            sem_key = "1st Semester"
        elif cs.term_no == 2:
            sem_key = "2nd Semester"
        else:
            sem_key = "Summer"

        term_key = f"{year_key} - {sem_key}"

        if term_key not in hierarchy:
            hierarchy[term_key] = {
                'year_level': cs.year_level,
                'term_no': cs.term_no,
                'subjects': []
            }

        hierarchy[term_key]['subjects'].append(cs)

    # Build prerequisite map
    prerequisite_map = {}
    for cs in curriculum_subjects:
        subject = cs.subject
        prereqs = subject.subject_prereqs.all()
        if prereqs:
            prerequisite_map[subject.id] = {
                'subject': subject,
                'prerequisites': [p.prereq_subject for p in prereqs]
            }

    return render(request, 'registrar/academics/curriculum_detail.html', {
        'curriculum': curriculum,
        'curriculum_subjects': curriculum_subjects,
        'hierarchy': hierarchy,
        'prerequisite_map': prerequisite_map
    })


@role_required('registrar')
def curriculum_add_subjects(request, pk):
    """Add subjects to a curriculum (single or bulk)"""
    curriculum = get_object_or_404(Curriculum, pk=pk)

    if request.method == 'POST':
        try:
            subject_ids = request.POST.getlist('subject_ids[]')
            year_level = request.POST.get('year_level')
            term_no = request.POST.get('term_no')

            # Validation
            if not all([subject_ids, year_level, term_no]):
                return JsonResponse({'success': False, 'message': 'Subject, Year Level, and Term are required'}, status=400)

            year_level = int(year_level)
            term_no = int(term_no)

            # Get subjects and validate they belong to the curriculum's program
            subjects = Subject.objects.filter(
                id__in=subject_ids,
                program=curriculum.program,
                active=True,
                archived=False
            )

            if len(subjects) != len(subject_ids):
                return JsonResponse({
                    'success': False,
                    'message': 'Some selected subjects do not belong to this curriculum\'s program or are inactive'
                }, status=400)

            # Add subjects to curriculum
            added_count = 0
            for subject in subjects:
                # Check if already exists
                if not CurriculumSubject.objects.filter(curriculum=curriculum, subject=subject).exists():
                    CurriculumSubject.objects.create(
                        curriculum=curriculum,
                        subject=subject,
                        year_level=year_level,
                        term_no=term_no,
                        is_recommended=True
                    )
                    added_count += 1

            # Audit trail
            AuditTrail.objects.create(
                actor=request.user,
                action='add_subjects',
                entity='Curriculum',
                entity_id=curriculum.id,
                new_value_json={
                    'subject_count': added_count,
                    'year_level': year_level,
                    'term_no': term_no,
                }
            )

            return JsonResponse({
                'success': True,
                'message': f'{added_count} subject(s) added to curriculum successfully'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    # GET request - show add subjects modal
    subjects = Subject.objects.filter(
        program=curriculum.program,
        active=True,
        archived=False
    ).exclude(
        curriculumsubject__curriculum=curriculum
    ).distinct()

    context = {
        'curriculum': curriculum,
        'available_subjects': subjects,
    }
    return render(request, 'registrar/academics/curriculum_add_subjects_modal.html', context)


@role_required('registrar')
def curriculum_update(request, pk):
    """Update an existing curriculum"""
    curriculum = get_object_or_404(Curriculum, pk=pk)

    if request.method == 'POST':
        try:
            # Store old values for audit
            old_values = {
                'program_id': curriculum.program.id,
                'version': curriculum.version,
                'effective_sy': curriculum.effective_sy,
                'active': curriculum.active
            }

            # Update fields
            program_id = request.POST.get('program_id')
            program = get_object_or_404(Program, pk=program_id)

            curriculum.program = program
            curriculum.version = request.POST.get('version')
            curriculum.effective_sy = request.POST.get('effective_sy')
            curriculum.save()

            # Audit trail
            AuditTrail.objects.create(
                actor=request.user,
                action='update',
                entity='Curriculum',
                entity_id=curriculum.id,
                old_value_json=old_values,
                new_value_json={
                    'program_id': program.id,
                    'version': curriculum.version,
                    'effective_sy': curriculum.effective_sy,
                    'active': curriculum.active
                }
            )

            return JsonResponse({
                'success': True,
                'message': f'Curriculum "{curriculum.version}" updated successfully'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    # GET request
    programs = Program.objects.all()
    return render(request, 'registrar/academics/curriculum_form.html', {
        'curriculum': curriculum,
        'programs': programs
    })


@role_required('registrar')
def curriculum_duplicate(request, pk):
    """Duplicate curriculum with all its subjects"""
    if request.method == 'POST':
        try:
            source_curriculum = get_object_or_404(Curriculum, pk=pk)
            new_version = request.POST.get('new_version')
            new_effective_sy = request.POST.get('new_effective_sy')

            # Validation
            if not all([new_version, new_effective_sy]):
                return JsonResponse({'success': False, 'message': 'All fields are required'}, status=400)

            # Check if version already exists for this program
            if Curriculum.objects.filter(program=source_curriculum.program, version=new_version).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'A curriculum with this version already exists for this program'
                }, status=400)

            with transaction.atomic():
                # Create new curriculum
                new_curriculum = Curriculum.objects.create(
                    program=source_curriculum.program,
                    version=new_version,
                    effective_sy=new_effective_sy,
                    active=False
                )

                # Copy all curriculum subjects
                source_subjects = CurriculumSubject.objects.filter(curriculum=source_curriculum)
                for cs in source_subjects:
                    CurriculumSubject.objects.create(
                        curriculum=new_curriculum,
                        subject=cs.subject,
                        year_level=cs.year_level,
                        term_no=cs.term_no,
                        is_recommended=cs.is_recommended
                    )

                # Audit trail
                AuditTrail.objects.create(
                    actor=request.user,
                    action='duplicate',
                    entity='Curriculum',
                    entity_id=new_curriculum.id,
                    old_value_json={'source_curriculum_id': source_curriculum.id},
                    new_value_json={
                        'version': new_version,
                        'effective_sy': new_effective_sy,
                        'subjects_copied': source_subjects.count()
                    }
                )

            return JsonResponse({
                'success': True,
                'message': f'Curriculum "{new_version}" created successfully',
                'curriculum_id': new_curriculum.id,
                'curriculum_name': new_version
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    # GET request
    curriculum = get_object_or_404(Curriculum, pk=pk)
    return render(request, 'registrar/academics/curriculum_duplicate_form.html', {
        'curriculum': curriculum
    })


@role_required('registrar')
def curriculum_toggle_active(request, pk):
    """Toggle curriculum active status (only one active per program)"""
    if request.method == 'POST':
        try:
            curriculum = get_object_or_404(Curriculum, pk=pk)
            new_status = request.POST.get('active') == 'true'

            with transaction.atomic():
                if new_status:
                    # Deactivate all other curricula for this program
                    Curriculum.objects.filter(
                        program=curriculum.program
                    ).exclude(pk=pk).update(active=False)

                # Update this curriculum
                old_status = curriculum.active
                curriculum.active = new_status
                curriculum.save()

                # Audit trail
                AuditTrail.objects.create(
                    actor=request.user,
                    action='toggle_active',
                    entity='Curriculum',
                    entity_id=curriculum.id,
                    old_value_json={'active': old_status},
                    new_value_json={'active': new_status}
                )

            status_text = 'activated' if new_status else 'deactivated'
            return JsonResponse({
                'success': True,
                'message': f'Curriculum "{curriculum.version}" {status_text} successfully'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)


# ==================== SUBJECTS ====================
@role_required('registrar')
def subjects_list(request):
    """List all subjects (including archived for admin purposes)"""
    show_archived = request.GET.get('show_archived', 'false') == 'true'

    subjects = Subject.objects.select_related('program').prefetch_related('subject_prereqs__prereq_subject').all().order_by('-created_at')

    # Filter out archived subjects unless explicitly showing them
    if not show_archived:
        subjects = subjects.filter(archived=False)

    programs = Program.objects.all()
    return render(request, 'registrar/academics/subjects_list.html', {
        'subjects': subjects,
        'programs': programs,
        'show_archived': show_archived
    })


@role_required('registrar')
def subject_create(request):
    """Create a new subject"""
    if request.method == 'POST':
        try:
            code = request.POST.get('code')
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            units = request.POST.get('units')
            subject_type = request.POST.get('type')
            recommended_year = request.POST.get('recommended_year')
            recommended_sem = request.POST.get('recommended_sem')
            program_id = request.POST.get('program_id')
            prerequisite_ids = request.POST.getlist('prerequisites[]')

            # Validation
            if not all([code, title, units, subject_type, program_id]):
                return JsonResponse({'success': False, 'message': 'Required fields are missing'}, status=400)

            program = get_object_or_404(Program, pk=program_id)

            with transaction.atomic():
                # Create subject
                subject = Subject.objects.create(
                    code=code,
                    title=title,
                    description=description,
                    units=units,
                    type=subject_type,
                    recommended_year=recommended_year if recommended_year else None,
                    recommended_sem=recommended_sem if recommended_sem else None,
                    program=program,
                    active=True
                )

                # Add prerequisites if any
                if prerequisite_ids:
                    for prereq_id in prerequisite_ids:
                        prereq_subject = get_object_or_404(Subject, pk=prereq_id)
                        Prereq.objects.create(
                            subject=subject,
                            prereq_subject=prereq_subject
                        )

                # Audit trail
                AuditTrail.objects.create(
                    actor=request.user,
                    action='create',
                    entity='Subject',
                    entity_id=subject.id,
                    new_value_json={
                        'code': code,
                        'title': title,
                        'units': str(units),
                        'type': subject_type,
                        'program_id': program_id,
                        'prerequisites': prerequisite_ids
                    }
                )

            return JsonResponse({
                'success': True,
                'message': f'Subject "{code}" created successfully',
                'subject': {
                    'id': subject.id,
                    'code': subject.code,
                    'title': subject.title
                }
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    # GET request
    programs = Program.objects.all()
    return render(request, 'registrar/academics/subject_form.html', {'programs': programs})


@role_required('registrar')
def subject_update(request, pk):
    """Update an existing subject"""
    subject = get_object_or_404(Subject, pk=pk)

    if request.method == 'POST':
        try:
            # Store old values for audit
            old_prereqs = list(subject.subject_prereqs.values_list('prereq_subject_id', flat=True))
            old_values = {
                'code': subject.code,
                'title': subject.title,
                'units': str(subject.units),
                'type': subject.type,
                'prerequisites': old_prereqs
            }

            # Update fields
            subject.code = request.POST.get('code')
            subject.title = request.POST.get('title')
            subject.description = request.POST.get('description', '')
            subject.units = request.POST.get('units')
            subject.type = request.POST.get('type')
            subject.recommended_year = request.POST.get('recommended_year') or None
            subject.recommended_sem = request.POST.get('recommended_sem') or None
            program_id = request.POST.get('program_id')
            subject.program = get_object_or_404(Program, pk=program_id)

            prerequisite_ids = request.POST.getlist('prerequisites[]')

            with transaction.atomic():
                subject.save()

                # Update prerequisites - remove old ones and add new ones
                subject.subject_prereqs.all().delete()
                if prerequisite_ids:
                    for prereq_id in prerequisite_ids:
                        prereq_subject = get_object_or_404(Subject, pk=prereq_id)
                        Prereq.objects.create(
                            subject=subject,
                            prereq_subject=prereq_subject
                        )

                # Audit trail
                AuditTrail.objects.create(
                    actor=request.user,
                    action='update',
                    entity='Subject',
                    entity_id=subject.id,
                    old_value_json=old_values,
                    new_value_json={
                        'code': subject.code,
                        'title': subject.title,
                        'units': str(subject.units),
                        'type': subject.type,
                        'prerequisites': prerequisite_ids
                    }
                )

            return JsonResponse({
                'success': True,
                'message': f'Subject "{subject.code}" updated successfully'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    # GET request
    programs = Program.objects.all()
    existing_prereqs = subject.subject_prereqs.select_related('prereq_subject').all()
    return render(request, 'registrar/academics/subject_form.html', {
        'subject': subject,
        'programs': programs,
        'existing_prereqs': existing_prereqs
    })


@role_required('registrar')
def subject_delete(request, pk):
    """Delete (deactivate) a subject"""
    if request.method == 'POST':
        subject = get_object_or_404(Subject, pk=pk)

        try:
            # Store values for audit
            old_values = {
                'code': subject.code,
                'title': subject.title,
                'units': str(subject.units)
            }

            # Audit trail before deletion
            AuditTrail.objects.create(
                actor=request.user,
                action='delete',
                entity='Subject',
                entity_id=subject.id,
                old_value_json=old_values
            )

            subject_code = subject.code
            subject.delete()

            return JsonResponse({
                'success': True,
                'message': f'Subject "{subject_code}" deleted successfully'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)


@role_required('registrar')
def program_search(request):
    """Live search for programs"""
    query = request.GET.get('q', '')

    programs = Program.objects.filter(
        Q(name__icontains=query),
    )

    programs = programs[:10]  # Limit to 10 results

    results = [
        {
            'id': p.id,
            'name': p.name,
            'level': p.get_level_display(),
            'display': f"{p.name} ({p.get_level_display()})"
        }
        for p in programs
    ]

    return JsonResponse({'results': results})


@role_required('registrar')
def subject_search(request):
    """Live search for subjects (used for prerequisites) - excludes archived subjects"""
    query = request.GET.get('q', '')
    program_id = request.GET.get('program', None)
    exclude_id = request.GET.get('exclude', None)

    subjects = Subject.objects.filter(
        Q(code__icontains=query) | Q(title__icontains=query),
        active=True,
        archived=False
    )

    # Filter by program if specified
    if program_id:
        subjects = subjects.filter(program_id=program_id)

    # Exclude the subject being edited (can't be its own prerequisite)
    if exclude_id:
        subjects = subjects.exclude(id=exclude_id)

    subjects = subjects[:10]  # Limit to 10 results

    results = [
        {
            'id': s.id,
            'code': s.code,
            'title': s.title,
            'display': f"{s.code} - {s.title}"
        }
        for s in subjects
    ]

    return JsonResponse({'results': results})


# ==================== PREREQUISITES ====================
@role_required('registrar')
def prerequisite_add(request):
    """Add a prerequisite to a subject (AJAX endpoint)"""
    if request.method == 'POST':
        try:
            subject_id = request.POST.get('subject_id')
            prereq_subject_id = request.POST.get('prereq_subject_id')

            subject = get_object_or_404(Subject, pk=subject_id)
            prereq_subject = get_object_or_404(Subject, pk=prereq_subject_id)

            # Check if already exists
            if Prereq.objects.filter(subject=subject, prereq_subject=prereq_subject).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'This prerequisite already exists'
                }, status=400)

            # Create prerequisite
            prereq = Prereq.objects.create(
                subject=subject,
                prereq_subject=prereq_subject
            )

            # Audit trail
            AuditTrail.objects.create(
                actor=request.user,
                action='add_prerequisite',
                entity='Subject',
                entity_id=subject.id,
                new_value_json={
                    'prereq_subject_id': prereq_subject.id,
                    'prereq_subject_code': prereq_subject.code
                }
            )

            return JsonResponse({
                'success': True,
                'message': f'Prerequisite added successfully',
                'prereq': {
                    'id': prereq.id,
                    'code': prereq_subject.code,
                    'title': prereq_subject.title
                }
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)


@role_required('registrar')
def prerequisite_delete(request, pk):
    """Remove a prerequisite from a subject"""
    if request.method == 'POST':
        try:
            prereq = get_object_or_404(Prereq, pk=pk)
            subject = prereq.subject
            prereq_subject = prereq.prereq_subject

            # Audit trail
            AuditTrail.objects.create(
                actor=request.user,
                action='remove_prerequisite',
                entity='Subject',
                entity_id=subject.id,
                old_value_json={
                    'prereq_subject_id': prereq_subject.id,
                    'prereq_subject_code': prereq_subject.code
                }
            )

            prereq.delete()

            return JsonResponse({
                'success': True,
                'message': f'Prerequisite removed successfully'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
